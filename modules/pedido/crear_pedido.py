import streamlit as st  # ← ¡IMPORTANTE! Faltaba esta línea
import pandas as pd
import json
from datetime import datetime
from utils.firestore_utils import get_next_id, save_dataframe_firestore
from utils.data_utils import limpiar_telefono
from .helpers import convert_to_firestore_type, safe_select_index
import time

def show_create(df_pedidos, df_listas):
    # ✅ LIMPIAR ESTADO SI VIENE DE OTRA PÁGINA
    if 'ultima_pagina' not in st.session_state:
        st.session_state.ultima_pagina = "Crear"
    else:
        if st.session_state.ultima_pagina != "Crear":
            # Limpiar todas las keys del formulario
            keys_to_delete = [
                "num_productos", "force_refresh", "reset_form",
                "cliente_", "telefono_", "club_", "descripcion_",
                "fecha_entrada_", "fecha_salida_", "precio_total_",
                "precio_factura_", "tipo_pago_", "adelanto_", "observaciones_",
                "pendiente_", "empezado_", "cobrado_"
            ]
            for key in list(st.session_state.keys()):
                if key.startswith("producto_") or key.startswith("tela_") or key.startswith("precio_unit_") or key.startswith("cantidad_") or key in keys_to_delete:
                    del st.session_state[key]
            st.session_state.num_productos = 1
            st.session_state.force_refresh = str(datetime.now().timestamp())
            st.session_state.reset_form = False
        st.session_state.ultima_pagina = "Crear"  # ← Corregido typo: "pagida" → "pagina"

    st.markdown("## 🆕 Crear Nuevo Pedido")
    st.write("---")

    # ✅ AÑO ACTUAL (no editable)
    año_actual = datetime.now().year
    st.info(f"📅 **Año del pedido:** {año_actual} — Solo se puede crear en el año actual")

    # --- Inicializar número de filas de productos ---
    if "num_productos" not in st.session_state:
        st.session_state.num_productos = 1
    if "force_refresh" not in st.session_state:
        st.session_state.force_refresh = ""

    # --- BLOQUE DE PRODUCTOS ---
    st.markdown("### 🧵 Productos del pedido")
    
    # Preparar listas para selectbox
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
            # ✅ Autocompletado para Cliente y Club si hay datos previos
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
            
            # ✅ PRECIO Y PRECIO FACTURA MANUALES — PUEDEN SER 0
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

        # ✅ ESTADOS: Radio button para evitar conflictos (solo un estado principal)
        st.write("### 🏷️ Estado del pedido")
        estado = st.radio(
            "Selecciona el estado inicial:",
            options=["Pendiente", "Empezado", "Cobrado"],
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

            # Mapear estado a checkboxes
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
                df_pedidos = pd.concat([df_pedidos, new_pedido_df], ignore_index=True)
                df_pedidos = df_pedidos.where(pd.notna(df_pedidos), None)

                for c in df_pedidos.columns:
                    df_pedidos[c] = df_pedidos[c].apply(lambda x: None if x is pd.NaT else x)

                if save_dataframe_firestore(df_pedidos, 'pedidos'):
                    st.success(f"🎉 ¡Pedido **{next_id}** del año **{año_actual}** creado correctamente!")
                    st.balloons()
                    
                    # ✅ ENVIAR NOTIFICACIÓN POR TELEGRAM
                    try:
                        from utils.notifications import enviar_telegram
                        
                        # Obtener precio a mostrar (el que sea > 0)
                        precio_mostrar = precio if precio > 0 else precio_factura if precio_factura > 0 else 0.0
                        
                        mensaje = f"🆕 <b>Nuevo pedido</b>\nID: {next_id}\nCliente: {cliente}\nEquipo: {club}\nPrecio: {precio_mostrar:.2f} €"
                        enviar_telegram(
                            mensaje=mensaje,
                            bot_token=st.secrets["telegram"]["bot_token"],
                            chat_id=st.secrets["telegram"]["chat_id"]
                        )
                    except Exception as e:
                        st.warning(f"⚠️ No se pudo enviar notificación: {e}")

                    if 'data' not in st.session_state:
                        st.session_state['data'] = {}
                    st.session_state.data['df_pedidos'] = df_pedidos

                    st.session_state.reset_form = True
                    st.session_state.force_refresh = str(datetime.now().timestamp())
                    
                    # Limpiar formulario
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("❌ Error al crear el pedido. Por favor, inténtelo de nuevo.")