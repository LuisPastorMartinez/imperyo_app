# modules/pedidos_page.py oki
import streamlit as st
import pandas as pd
from datetime import datetime

# Importamos las funciones de pedido
try:
    from modules.pedido import show_create, show_consult, show_modify, show_delete
except ImportError as e:
    st.error(f"❌ Error al importar 'modules.pedido': {e}")
    st.stop()

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
        df_pedidos['Año'] = pd.to_numeric(df_pedidos['Año'], errors='coerce').fillna(datetime.now().year).astype('int64')

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

    # --- AÑADIR COLUMNA 'Estado' SI NO EXISTE ---
    if 'Estado' not in df_pedidos_filtrado.columns:
        def calcular_estado(row):
            if row.get('Pendiente', False):
                return 'Pendiente'
            if (row.get('Trabajo Terminado', False) and 
                row.get('Cobrado', False) and 
                row.get('Retirado', False)):
                return 'Completado'
            if row.get('Trabajo Terminado', False):
                return 'Terminado'
            if row.get('Inicio Trabajo', False):
                return 'Empezado'
            return 'Nuevo'
        df_pedidos_filtrado['Estado'] = df_pedidos_filtrado.apply(calcular_estado, axis=1)

    # --- MOSTRAR RESUMEN RÁPIDO ---
    st.markdown(f"### 📋 Pedidos del año {año_seleccionado}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📦 Total Pedidos", len(df_pedidos_filtrado))
    with col2:
        terminados = len(df_pedidos_filtrado[df_pedidos_filtrado['Estado'] == 'Terminado'])
        st.metric("✅ Terminados", terminados)
    with col3:
        pendientes = len(df_pedidos_filtrado[df_pedidos_filtrado['Estado'] == 'Pendiente'])
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