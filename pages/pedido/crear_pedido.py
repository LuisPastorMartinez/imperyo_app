import streamlit as st
import pandas as pd
import json
from datetime import datetime
from utils import get_next_id, save_dataframe_firestore
from .helpers import convert_to_firestore_type
import time

def show_create(df_pedidos, df_listas):
    st.subheader("Crear Nuevo Pedido")

    # --- Inicializar número de filas de productos ---
    if "num_productos" not in st.session_state:
        st.session_state.num_productos = 1  # siempre empezamos con 1 fila

    # --- BLOQUE DE PRODUCTOS ---
    st.markdown("### Productos del pedido")
    productos_lista = [""] + df_listas['Producto'].dropna().unique().tolist() if 'Producto' in df_listas.columns else [""]
    telas_lista = [""] + df_listas['Tela'].dropna().unique().tolist() if 'Tela' in df_listas.columns else [""]

    total_productos = 0.0
    productos_temp = []

    for i in range(st.session_state.num_productos):
        cols = st.columns([3, 3, 2, 2])
        with cols[0]:
            producto = st.selectbox(f"Producto {i+1}", productos_lista, key=f"producto_{i}")
        with cols[1]:
            tela = st.selectbox(f"Tela {i+1}", telas_lista, key=f"tela_{i}")
        with cols[2]:
            precio_unit = st.number_input(f"Precio {i+1}", min_value=0.0, value=0.0, key=f"precio_unit_{i}")
        with cols[3]:
            cantidad = st.number_input(f"Cantidad {i+1}", min_value=1, value=1, key=f"cantidad_{i}")

        total_productos += precio_unit * cantidad
        productos_temp.append({
            "Producto": producto,
            "Tela": tela,
            "PrecioUnitario": precio_unit,
            "Cantidad": cantidad
        })

    st.markdown(f"**💰 Total productos: {total_productos:.2f} €**")

    add_col, remove_col = st.columns([1, 1])
    with add_col:
        if st.button("➕ Añadir otro producto", key="crear_add_producto"):
            st.session_state.num_productos += 1
            st.experimental_rerun()

    with remove_col:
        if st.session_state.num_productos > 1:
            if st.button("➖ Quitar último producto", key="crear_remove_producto"):
                st.session_state.num_productos -= 1
                st.experimental_rerun()

    # --- RESTO DEL FORMULARIO ---
    with st.form("nuevo_pedido_form"):
        next_id = get_next_id(df_pedidos, 'ID')
        st.info(f"El próximo ID de pedido será: **{next_id}**")

        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input("Cliente*")
            telefono = st.text_input("Teléfono*", max_chars=9)
            club = st.text_input("Club*")
            descripcion = st.text_area("Descripción")

        with col2:
            fecha_entrada = st.date_input("Fecha entrada", value=datetime.now().date())
            tiene_fecha_salida = st.checkbox("Establecer fecha de salida")
            fecha_salida = st.date_input("Fecha salida", value=datetime.now().date()) if tiene_fecha_salida else None
            precio = st.number_input("Precio total", min_value=0.0, value=total_productos)
            precio_factura = st.number_input("Precio factura", min_value=0.0, value=0.0)
            tipos_pago = [""] + df_listas['Tipo de pago'].dropna().unique().tolist() if 'Tipo de pago' in df_listas.columns else [""]
            tipo_pago = st.selectbox("Tipo de pago", tipos_pago)
            adelanto = st.number_input("Adelanto", min_value=0.0, value=0.0)
            observaciones = st.text_area("Observaciones")

        st.write("**Estado del pedido:**")
        estado_cols = st.columns(5)
        with estado_cols[0]:
            empezado = st.checkbox("Empezado")
        with estado_cols[1]:
            terminado = st.checkbox("Terminado")
        with estado_cols[2]:
            cobrado = st.checkbox("Cobrado")
        with estado_cols[3]:
            retirado = st.checkbox("Retirado")
        with estado_cols[4]:
            pendiente = st.checkbox("Pendiente")

        if st.form_submit_button("Guardar Nuevo Pedido"):
            if not cliente or not telefono or not club:
                st.error("Por favor complete los campos obligatorios (*)")
                return

            if not telefono.isdigit() or len(telefono) != 9:
                st.error("El teléfono debe contener exactamente 9 dígitos numéricos")
                return

            # Guardar productos como JSON string
            productos_json = json.dumps(productos_temp)

            new_pedido = {
                'ID': next_id,
                'Productos': productos_json,
                'Cliente': convert_to_firestore_type(cliente),
                'Telefono': convert_to_firestore_type(telefono),
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
                'Trabajo Terminado': convert_to_firestore_type(terminado),
                'Cobrado': convert_to_firestore_type(cobrado),
                'Retirado': convert_to_firestore_type(retirado),
                'Pendiente': convert_to_firestore_type(pendiente),
                'id_documento_firestore': None
            }

            new_pedido_df = pd.DataFrame([new_pedido])
            df_pedidos = pd.concat([df_pedidos, new_pedido_df], ignore_index=True)
            df_pedidos = df_pedidos.where(pd.notna(df_pedidos), None)

            for c in df_pedidos.columns:
                df_pedidos[c] = df_pedidos[c].apply(lambda x: None if x is pd.NaT else x)

            if save_dataframe_firestore(df_pedidos, 'pedidos'):
                success_placeholder = st.empty()
                success_placeholder.success(f"Pedido {next_id} creado correctamente!")
                time.sleep(2)
                success_placeholder.empty()

                if 'data' not in st.session_state:
                    st.session_state['data'] = {}
                st.session_state.data['df_pedidos'] = df_pedidos

                # --- 🔄 Resetear solo campos del formulario sin romper navegación ---
                keys_to_keep = ["data"]
                keys_to_delete = [k for k in st.session_state.keys() if k not in keys_to_keep]
                for key in keys_to_delete:
                    del st.session_state[key]

                # Reiniciar número de productos a 1 de forma segura
                st.session_state.num_productos = 1

                # Usar experimental_rerun para evitar reinicio de la app
                st.experimental_rerun()
            else:
                st.error("Error al crear el pedido")
