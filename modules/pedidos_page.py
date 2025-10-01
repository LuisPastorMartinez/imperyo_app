# pedidos_page.py
import streamlit as st
import pandas as pd
from datetime import datetime
import json
import time

# Importamos solo lo necesario
from utils.firestore_utils import get_next_id, save_dataframe_firestore
from utils.data_utils import limpiar_telefono
from utils.helpers import convert_to_firestore_type, safe_select_index

# =============== FUNCIONES INCORPORADAS DIRECTAMENTE ===============

def show_create(df_pedidos, df_listas):
    # Limpiar estado si viene de otra página
    if 'ultima_pagina' not in st.session_state:
        st.session_state.ultima_pagina = "Crear"
    else:
        if st.session_state.ultima_pagina != "Crear":
            keys_to_delete = [
                "num_productos", "force_refresh", "reset_form",
                "cliente_", "telefono_", "club_", "descripcion_",
                "fecha_entrada_", "fecha_salida_", "precio_total_",
                "precio_factura_", "tipo_pago_", "adelanto_", "observaciones_",
                "empezado_", "cobrado_", "pendiente_"
            ]
            for key in list(st.session_state.keys()):
                if key.startswith("producto_") or key.startswith("tela_") or key.startswith("precio_unit_") or key.startswith("cantidad_") or key in keys_to_delete:
                    del st.session_state[key]
            st.session_state.num_productos = 1
            st.session_state.force_refresh = str(datetime.now().timestamp())
        st.session_state.ultima_pagina = "Crear"

    st.markdown("## 🆕 Crear Nuevo Pedido")
    st.write("---")

    año_actual = datetime.now().year
    st.info(f"📅 **Año del pedido:** {año_actual}")

    # --- Inicializar número de filas de productos ---
    if "num_productos" not in st.session_state:
        st.session_state.num_productos = 1
    if "force_refresh" not in st.session_state:
        st.session_state.force_refresh = ""

    # --- BLOQUE DE PRODUCTOS ---
    st.markdown("### 🧵 Productos del pedido")
    
    productos_lista = [""]
    if 'Producto' in df_listas.columns:
        unique_products = df_listas['Producto'].dropna().unique()
        if len(unique_products) > 0:
            productos_lista.extend(unique_products.tolist())

    telas_lista = [""]
    if 'Tela' in df_listas.columns:
        unique_telas = df_listas['Tela'].dropna().unique()
        if len(unique_telas) > 0:
            telas_lista.extend(unique_telas.tolist())

    total_productos = 0.0
    productos_temp = []

    for i in range(st.session_state.num_productos):
        suffix = st.session_state.force_refresh
        cols = st.columns([3, 3, 2, 2])
        with cols[0]:
            producto = st.selectbox(
                f"Producto {i+1}",
                productos_lista,
                index=safe_select_index(productos_lista, ""),
                key=f"producto_{i}_{suffix}",
                help="Selecciona un producto de la lista"
            )
        with cols[1]:
            tela = st.selectbox(
                f"Tela {i+1}",
                telas_lista,
                index=safe_select_index(telas_lista, ""),
                key=f"tela_{i}_{suffix}",
                help="Selecciona el tipo de tela"
            )
        with cols[2]:
            precio_unit = st.number_input(
                f"Precio €", 
                min_value=0.0, 
                value=0.0, 
                step=0.5,
                format="%.2f",
                key=f"precio_unit_{i}_{suffix}",
                help="Precio unitario del producto"
            )
        with cols[3]:
            cantidad = st.number_input(
                f"Cantidad", 
                min_value=1, 
                value=1, 
                step=1,
                key=f"cantidad_{i}_{suffix}",
                help="Cantidad de unidades"
            )

        total_productos += precio_unit * cantidad
        productos_temp.append({
            "Producto": producto,
            "Tela": tela,
            "PrecioUnitario": precio_unit,
            "Cantidad": cantidad
        })

    st.markdown(f"<div style='background-color: #e3f2fd; padding: 10px; border-radius: 8px;'><b>💰 Subtotal productos:</b> <span style='font-size: 1.2em; color: #1976d2;'>{total_productos:.2f} €</span></div>", unsafe_allow_html=True)

    st.write("")

    add_col, remove_col = st.columns([1, 1])
    with add_col:
        if st.button("➕ Añadir otro producto", type="secondary", use_container_width=True, key=f"crear_add_producto_{st.session_state.force_refresh}"):
            st.session_state.num_productos += 1
            st.rerun()

    with remove_col:
        if st.session_state.num_productos > 1:
            if st.button("➖ Quitar último producto", type="secondary", use_container_width=True, key=f"crear_remove_producto_{st.session_state.force_refresh}"):
                st.session_state.num_productos -= 1
                st.rerun()

    st.write("---")

    # --- RESTO DEL FORMULARIO ---
    with st.form("nuevo_pedido_form", clear_on_submit=False):
        suffix = st.session_state.force_refresh
        next_id = get_next_id(df_pedidos, 'ID')
        st.markdown(f"### 🆔 ID del pedido: **{next_id}**")

        col1, col2 = st.columns(2)
        
        with col1:
            clientes_existentes = df_pedidos['Cliente'].dropna().unique().tolist() if 'Cliente' in df_pedidos.columns else []
            cliente = st.selectbox(
                "Cliente*",
                [""] + clientes_existentes,
                index=0,
                key=f"cliente_{suffix}",
                help="Empieza a escribir para buscar"
            )
            
            telefono = st.text_input(
                "Teléfono* (9 dígitos)", 
                max_chars=9, 
                key=f"telefono_{suffix}",
                placeholder="Ej: 612345678"
            )
            
            clubes_existentes = df_pedidos['Club'].dropna().unique().tolist() if 'Club' in df_pedidos.columns else []
            club = st.selectbox(
                "Club*",
                [""] + clubes_existentes,
                index=0,
                key=f"club_{suffix}",
                help="Selecciona o escribe el club"
            )
            
            descripcion = st.text_area(
                "Descripción",
                key=f"descripcion_{suffix}",
                placeholder="Detalles del pedido, observaciones, etc."
            )

        with col2:
            fecha_entrada = st.date_input(
                "📅 Fecha de entrada", 
                value=datetime.now().date(), 
                key=f"fecha_entrada_{suffix}"
            )
            
            tiene_fecha_salida = st.checkbox("📆 Establecer fecha de salida", key=f"tiene_fecha_salida_{suffix}")
            if tiene_fecha_salida:
                fecha_salida = st.date_input("Fecha de salida", value=datetime.now().date(), key=f"fecha_salida_{suffix}")
            else:
                fecha_salida = None
            
            precio = st.number_input(
                "💰 Precio total (€)", 
                min_value=0.0, 
                value=0.0, 
                step=1.0,
                format="%.2f",
                key=f"precio_total_{suffix}"
            )
            
            precio_factura = st.number_input(
                "🧾 Precio factura (€)", 
                min_value=0.0, 
                value=0.0, 
                step=1.0,
                format="%.2f",
                key=f"precio_factura_{suffix}"
            )
            
            tipos_pago = [""]
            if 'Tipo de pago' in df_listas.columns:
                unique_tipos = df_listas['Tipo de pago'].dropna().unique()
                if len(unique_tipos) > 0:
                    tipos_pago.extend(unique_tipos.tolist())
            tipo_pago = st.selectbox(
                "💳 Tipo de pago", 
                tipos_pago, 
                index=safe_select_index(tipos_pago, ""), 
                key=f"tipo_pago_{suffix}"
            )
            
            adelanto = st.number_input(
                "💵 Adelanto (€)", 
                min_value=0.0, 
                value=0.0, 
                step=1.0,
                format="%.2f",
                key=f"adelanto_{suffix}"
            )
            
            observaciones = st.text_area(
                "📝 Observaciones adicionales",
                key=f"observaciones_{suffix}",
                placeholder="Notas internas, acuerdos, etc."
            )

        # Estados iniciales
        st.write("### 🏷️ Estado inicial del pedido")
        estado = st.radio(
            "Selecciona el estado:",
            options=["Empezado", "Cobrado", "Pendiente"],
            index=0,
            horizontal=True,
            key=f"estado_{suffix}"
        )

        submitted = st.form_submit_button("✅ Guardar Nuevo Pedido", type="primary", use_container_width=True)

        if submitted:
            if not cliente or not telefono or not club:
                st.error("❌ Por favor complete los campos obligatorios (*)")
                return

            telefono_limpio = limpiar_telefono(telefono)
            if not telefono_limpio or len(telefono_limpio) != 9:
                st.error("❌ El teléfono debe contener exactamente 9 dígitos numéricos")
                return

            productos_json = json.dumps(productos_temp)

            empezado = estado == "Empezado"
            cobrado = estado == "Cobrado"
            pendiente = estado == "Pendiente"

            new_pedido = {
                'ID': next_id,
                'Productos': productos_json,
                'Cliente': convert_to_firestore_type(cliente),
                'Telefono': convert_to_firestore_type(telefono_limpio),
                'Club': convert_to_firestore_type(club),
                'Breve Descripción': convert_to_firestore_type(descripcion),
                'Fecha entrada': convert_to_firestore_type(fecha_entrada),
                'Fecha Salida': convert_to_firestore_type(fecha_salida),
                'Precio': convert_to_firestore_type(precio),
                'Precio Factura': convert_to_firestore_type(precio_factura),
                'Tipo de pago': convert_to_firestore_type(tipo_pago),
                'Adelanto': convert_to_firestore_type(adelanto),
                'Observaciones': convert_to_firestore_type(observaciones),
                'Inicio Trabajo': convert_to_firestore_type(empezado),
                'Trabajo Terminado': False,
                'Cobrado': convert_to_firestore_type(cobrado),
                'Retirado': False,
                'Pendiente': convert_to_firestore_type(pendiente),
                'Año': año_actual,
                'id_documento_firestore': None
            }

            with st.spinner("💾 Guardando pedido..."):
                new_pedido_df = pd.DataFrame([new_pedido])
                df_pedidos_actualizado = pd.concat([df_pedidos, new_pedido_df], ignore_index=True)
                df_pedidos_actualizado = df_pedidos_actualizado.where(pd.notna(df_pedidos_actualizado), None)

                for c in df_pedidos_actualizado.columns:
                    df_pedidos_actualizado[c] = df_pedidos_actualizado[c].apply(lambda x: None if x is pd.NaT else x)

                if save_dataframe_firestore(df_pedidos_actualizado, 'pedidos'):
                    st.success(f"🎉 ¡Pedido **{next_id}** del año **{año_actual}** creado correctamente!")
                    st.balloons()
                    
                    # Notificación por Telegram (opcional)
                    try:
                        from utils.notifications import enviar_telegram
                        precio_mostrar = precio if precio > 0 else precio_factura if precio_factura > 0 else 0.0
                        mensaje = f"🆕 <b>Nuevo pedido</b>\nID: {next_id}\nCliente: {cliente}\nEquipo: {club}\nPrecio: {precio_mostrar:.2f} €"
                        enviar_telegram(
                            mensaje=mensaje,
                            bot_token=st.secrets["telegram"]["bot_token"],
                            chat_id=st.secrets["telegram"]["chat_id"]
                        )
                    except Exception as e:
                        st.warning(f"⚠️ No se pudo enviar notificación: {e}")

                    # Actualizar sesión
                    st.session_state.data['df_pedidos'] = df_pedidos_actualizado
                    st.session_state.data_loaded = False
                    st.session_state.force_refresh = str(datetime.now().timestamp())
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Error al crear el pedido. Por favor, inténtelo de nuevo.")


def show_consult(df_filtrado, df_listas):
    if df_filtrado.empty:
        st.info("📭 No hay pedidos para mostrar.")
        return

    # Preparar visualización
    display_df = df_filtrado.copy()
    columnas_mostrar = ['ID', 'Cliente', 'Club', 'Producto', 'Precio', 'Fecha entrada', 'Estado']
    columnas_disponibles = [col for col in columnas_mostrar if col in display_df.columns]
    st.dataframe(display_df[columnas_disponibles], use_container_width=True, height=400)


def show_modify(df_pedidos, df_listas):
    if df_pedidos.empty:
        st.info("📭 No hay pedidos para modificar.")
        return

    pedido_id = st.number_input("🔍 Ingresa el ID del pedido a modificar", min_value=1, step=1)
    if not (df_pedidos['ID'] == pedido_id).any():
        st.warning("⚠️ No se encontró un pedido con ese ID.")
        return

    idx = df_pedidos[df_pedidos['ID'] == pedido_id].index[0]
    row = df_pedidos.loc[idx].copy()

    st.markdown(f"### ✏️ Editando Pedido ID: **{pedido_id}**")

    with st.form("modificar_pedido"):
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input("Cliente*", value=row.get('Cliente', ''))
            telefono = st.text_input("Teléfono*", value=row.get('Telefono', ''), max_chars=9)
            club = st.text_input("Club*", value=row.get('Club', ''))
            descripcion = st.text_area("Descripción", value=row.get('Breve Descripción', ''))
        with col2:
            fecha_entrada = st.date_input("Fecha entrada", value=row.get('Fecha entrada', datetime.now().date()))
            fecha_salida_val = row.get('Fecha Salida')
            tiene_fecha_salida = st.checkbox("Establecer fecha de salida", value=pd.notna(fecha_salida_val))
            if tiene_fecha_salida:
                fecha_salida = st.date_input("Fecha salida", value=fecha_salida_val if pd.notna(fecha_salida_val) else datetime.now().date())
            else:
                fecha_salida = None
            precio = st.number_input("Precio total (€)", value=float(row.get('Precio', 0)), min_value=0.0, step=1.0)
            precio_factura = st.number_input("Precio factura (€)", value=float(row.get('Precio Factura', 0)), min_value=0.0, step=1.0)
            adelanto = st.number_input("Adelanto (€)", value=float(row.get('Adelanto', 0)), min_value=0.0, step=1.0)
            observaciones = st.text_area("Observaciones", value=row.get('Observaciones', ''))

        # Estados
        st.write("### 🏷️ Estado actual")
        inicio_trabajo = st.checkbox("Inicio Trabajo", value=bool(row.get('Inicio Trabajo', False)))
        trabajo_terminado = st.checkbox("Trabajo Terminado", value=bool(row.get('Trabajo Terminado', False)))
        cobrado = st.checkbox("Cobrado", value=bool(row.get('Cobrado', False)))
        retirado = st.checkbox("Retirado", value=bool(row.get('Retirado', False)))
        pendiente = st.checkbox("Pendiente", value=bool(row.get('Pendiente', False)))

        submitted = st.form_submit_button("✅ Guardar Cambios", type="primary", use_container_width=True)

        if submitted:
            if not cliente or not telefono or not club:
                st.error("❌ Campos obligatorios incompletos.")
                return

            telefono_limpio = limpiar_telefono(telefono)
            if not telefono_limpio or len(telefono_limpio) != 9:
                st.error("❌ Teléfono inválido.")
                return

            df_pedidos.at[idx, 'Cliente'] = cliente
            df_pedidos.at[idx, 'Telefono'] = telefono_limpio
            df_pedidos.at[idx, 'Club'] = club
            df_pedidos.at[idx, 'Breve Descripción'] = descripcion
            df_pedidos.at[idx, 'Fecha entrada'] = fecha_entrada
            df_pedidos.at[idx, 'Fecha Salida'] = fecha_salida
            df_pedidos.at[idx, 'Precio'] = precio
            df_pedidos.at[idx, 'Precio Factura'] = precio_factura
            df_pedidos.at[idx, 'Adelanto'] = adelanto
            df_pedidos.at[idx, 'Observaciones'] = observaciones
            df_pedidos.at[idx, 'Inicio Trabajo'] = inicio_trabajo
            df_pedidos.at[idx, 'Trabajo Terminado'] = trabajo_terminado
            df_pedidos.at[idx, 'Cobrado'] = cobrado
            df_pedidos.at[idx, 'Retirado'] = retirado
            df_pedidos.at[idx, 'Pendiente'] = pendiente

            with st.spinner("💾 Guardando cambios..."):
                if save_dataframe_firestore(df_pedidos, 'pedidos'):
                    st.success("✅ ¡Pedido actualizado correctamente!")
                    st.session_state.data['df_pedidos'] = df_pedidos
                    st.session_state.data_loaded = False
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Error al guardar los cambios.")


def show_delete(df_pedidos, df_listas):
    if df_pedidos.empty:
        st.info("📭 No hay pedidos para eliminar.")
        return

    pedido_id = st.number_input("🗑️ Ingresa el ID del pedido a eliminar", min_value=1, step=1)
    if not (df_pedidos['ID'] == pedido_id).any():
        st.warning("⚠️ No se encontró un pedido con ese ID.")
        return

    row = df_pedidos[df_pedidos['ID'] == pedido_id].iloc[0]
    st.markdown(f"### ¿Eliminar pedido **{pedido_id}** de **{row['Cliente']}**?")
    st.write(f"**Precio:** {row.get('Precio', 0):.2f} €")

    if st.button("🗑️ Confirmar eliminación", type="primary"):
        doc_id = row.get('id_documento_firestore')
        if doc_id:
            from utils.firestore_utils import delete_document_firestore
            if delete_document_firestore('pedidos', doc_id):
                st.success("✅ Pedido eliminado.")
                st.session_state.data_loaded = False
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Error al eliminar.")
        else:
            st.error("❌ No se encontró el documento en Firestore.")


# =============== FUNCIÓN PRINCIPAL ===============

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

    # Añadir columna 'Estado' si no existe
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