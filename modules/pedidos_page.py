import streamlit as st
import pandas as pd
from datetime import datetime

# Importamos las funciones de pedido
try:
    from modules.pedido import show_create, show_consult, show_modify, show_delete
except ImportError as e:
    st.error(f"❌ Error al importar 'modules.pedido': {e}")
    st.stop()

# --- IMPORTAR UTILS DE EMAIL ---
try:
    from utils.email_utils import send_completion_email
except ImportError:
    st.warning("⚠️ No se encontró 'utils/email_utils.py'. Las notificaciones por email no estarán disponibles hasta que se cree el archivo.")

def show_pedidos_page(df_pedidos=None, df_listas=None):
    """
    Página principal de Pedidos.
    Si no se pasan df_pedidos/df_listas, intenta cargarlos desde sesión o Firestore.
    """
    # --- CARGA DE DATOS (solo si no vienen como parámetro) ---
    if df_pedidos is None or df_listas is None:
        data = st.session_state.get('data', {})
        if isinstance(data, dict) and 'df_pedidos' in data and 'df_listas' in data:
            df_pedidos = data['df_pedidos']
            df_listas = data['df_listas']
        else:
            st.error("❌ No se encontraron los datos necesarios. Por favor, recarga la aplicación desde la página principal.")
            return

    # --- VALIDACIONES ---
    if df_pedidos is None:
        st.error("❌ No se cargó el DataFrame de pedidos.")
        return
    if df_listas is None:
        st.error("❌ No se cargó el DataFrame de listas.")
        return

    # --- PREPARAR COLUMNAS ---
    if not df_pedidos.empty and 'Año' in df_pedidos.columns:
        df_pedidos['Año'] = pd.to_numeric(df_pedidos['Año'], errors='coerce').fillna(2025).astype('int64')

    # --- OBTENER AÑO SELECCIONADO (sincronizado con página de inicio) ---
    año_actual = datetime.now().year

    # Si hay datos, obtener años disponibles
    if not df_pedidos.empty:
        años_disponibles = sorted(df_pedidos['Año'].dropna().unique(), reverse=True)
    else:
        años_disponibles = [año_actual]

    # Usar el año seleccionado en la sesión (sincronizado con página de inicio)
    año_seleccionado = st.sidebar.selectbox(
        "📅 Filtrar por Año",
        options=años_disponibles,
        index=años_disponibles.index(st.session_state.get('selected_year', año_actual)) 
               if st.session_state.get('selected_year', año_actual) in años_disponibles 
               else 0,
        key="año_selector_pedidos"
    )

    # Guardar selección en sesión (para sincronizar con otras páginas)
    st.session_state.selected_year = año_seleccionado

    # --- FILTRAR POR AÑO ---
    df_pedidos_filtrado = df_pedidos[df_pedidos['Año'] == año_seleccionado].copy()

    # --- MOSTRAR RESUMEN RÁPIDO ---
    st.markdown(f"### 📋 Pedidos del año {año_seleccionado}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📦 Total Pedidos", len(df_pedidos_filtrado))
    with col2:
        terminados = len(df_pedidos_filtrado[df_pedidos_filtrado['Estado'] == 'Terminado']) if 'Estado' in df_pedidos_filtrado.columns else 0
        st.metric("✅ Terminados", terminados)
    with col3:
        pendientes = len(df_pedidos_filtrado[df_pedidos_filtrado['Estado'] == 'Pendiente']) if 'Estado' in df_pedidos_filtrado.columns else 0
        st.metric("⏳ Pendientes", pendientes)

    st.write("---")

    # --- PESTAÑAS CON ICONOS ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Crear Pedido",
        "🔍 Consultar Pedidos", 
        "✏️ Modificar Pedido",
        "🗑️ Eliminar Pedido"
    ])

    with tab1:
        st.subheader("➕ Crear Nuevo Pedido")
        show_create(df_pedidos_filtrado, df_listas)

    with tab2:
        st.subheader("🔍 Consultar y Filtrar Pedidos")
        
        # Filtro de búsqueda rápida
        if not df_pedidos_filtrado.empty:
            search_term = st.text_input("🔍 Buscar por Cliente, Producto o ID", placeholder="Escribe para filtrar...")
            if search_term:
                mask = df_pedidos_filtrado.apply(lambda row: search_term.lower() in str(row).lower(), axis=1)
                df_filtrado_busqueda = df_pedidos_filtrado[mask]
                st.info(f"🔎 Se encontraron {len(df_filtrado_busqueda)} resultados.")
            else:
                df_filtrado_busqueda = df_pedidos_filtrado
        else:
            df_filtrado_busqueda = df_pedidos_filtrado

        # --- ACCIONES RÁPIDAS: CAMBIAR ESTADO ---
        if not df_filtrado_busqueda.empty:
            st.markdown("### 🚀 Acciones Rápidas — Cambiar Estado")

            # Crear copia para edición
            df_edit = df_filtrado_busqueda.copy()

            # Asegurar columna Estado
            if 'Estado' not in df_edit.columns:
                df_edit['Estado'] = 'Pendiente'

            # Definir estados posibles
            estados_posibles = ['Nuevo', 'Empezado', 'Pendiente', 'Terminado']

            # Mostrar tabla editable con selectbox por fila
            for idx, row in df_edit.iterrows():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"**ID {row['ID']}** — {row.get('Cliente', 'N/A')} — {row.get('Producto', 'N/A')}")
                with col2:
                    nuevo_estado = st.selectbox(
                        f"Estado",
                        options=estados_posibles,
                        index=estados_posibles.index(row['Estado']) if row['Estado'] in estados_posibles else 0,
                        key=f"estado_{row['ID']}",
                        label_visibility="collapsed"
                    )
                    df_edit.at[idx, 'Estado'] = nuevo_estado
                with col3:
                    # Si cambió el estado, mostrar indicador
                    if nuevo_estado != row['Estado']:
                        st.markdown("🔄 **Cambio detectado**")

            # Botón para guardar todos los cambios
            if st.button("💾 Guardar Todos los Cambios", type="primary", use_container_width=True):
                cambios_realizados = False
                ids_actualizados = []

                for idx, row in df_edit.iterrows():
                    id_pedido = row['ID']
                    nuevo_estado = row['Estado']
                    original_row = df_pedidos_filtrado[df_pedidos_filtrado['ID'] == id_pedido].iloc[0]
                    estado_original = original_row['Estado'] if 'Estado' in original_row else 'Pendiente'

                    if nuevo_estado != estado_original:
                        # Actualizar en el DataFrame original
                        mask_original = df_pedidos['ID'] == id_pedido
                        df_pedidos.loc[mask_original, 'Estado'] = nuevo_estado

                        # Guardar en Firestore
                        if save_dataframe_firestore(df_pedidos, 'pedidos'):
                            cambios_realizados = True
                            ids_actualizados.append(id_pedido)

                            # 📩 ENVIAR EMAIL SI CAMBIA A "TERMINADO"
                            if nuevo_estado == "Terminado" and 'email_utils' in globals():
                                try:
                                    # Obtener datos del cliente
                                    cliente = row.get('Cliente', 'Cliente')
                                    email = row.get('Email', None)  # ← Asegúrate de tener esta columna
                                    producto = row.get('Producto', 'tu pedido')
                                    fecha_salida = row.get('Fecha Salida', 'N/A')

                                    if email and "@" in str(email):
                                        success = send_completion_email(
                                            to_email=email,
                                            client_name=cliente,
                                            product_name=producto,
                                            delivery_date=str(fecha_salida)
                                        )
                                        if success:
                                            st.success(f"✉️ Email enviado a {cliente} ({email})")
                                        else:
                                            st.warning(f"⚠️ No se pudo enviar email a {cliente}")
                                    else:
                                        st.info(f"ℹ️ No se envió email: {cliente} no tiene email registrado.")
                                except Exception as e:
                                    st.error(f"❌ Error al enviar email: {e}")
                        else:
                            st.error(f"❌ Error al guardar el pedido ID {id_pedido} en Firestore.")

                if cambios_realizados:
                    # Actualizar sesión
                    st.session_state.data['df_pedidos'] = df_pedidos
                    st.success(f"✅ ¡{len(ids_actualizados)} pedidos actualizados correctamente!")
                    st.rerun()  # Refrescar para ver cambios
                else:
                    st.info("ℹ️ No se detectaron cambios en los estados.")

        # Mostrar tabla completa (solo lectura)
        st.markdown("### 📊 Vista de Pedidos")
        show_consult(df_filtrado_busqueda, df_listas)

    with tab3:
        st.subheader("✏️ Modificar Pedido Existente")
        show_modify(df_pedidos_filtrado, df_listas)

    with tab4:
        st.subheader("🗑️ Eliminar Pedido")
        show_delete(df_pedidos_filtrado, df_listas)

# Para pruebas locales
if __name__ == "__main__":
    show_pedidos_page()