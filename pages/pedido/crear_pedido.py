import streamlit as st
import pandas as pd
import json
from datetime import datetime
from utils import get_next_id, save_dataframe_firestore
from .helpers import convert_to_firestore_type
import time

def show_create(df_pedidos, df_listas):
    # --- Comprobar si hay que resetear el formulario ---
    if st.session_state.get("reset_form", False):
        keys_to_keep = ["data"]
        for key in list(st.session_state.keys()):
            if key not in keys_to_keep:
                del st.session_state[key]
        st.session_state.num_productos = 1
        st.session_state.force_refresh = str(datetime.now().timestamp())
        st.session_state.reset_form = False

    st.subheader("Crear Nuevo Pedido")

    # --- Inicializar número de filas de productos ---
    if "num_productos" not in st.session_state:
        st.session_state.num_productos = 1
    if "force_refresh" not in st.session_state:
        st.session_state.force_refresh = ""

    # --- BLOQUE DE PRODUCTOS ---
    st.markdown("### Productos del pedido")
    productos_lista = [""] + df_listas['Producto'].dropna().unique().tolist() if 'Producto' in df_listas.columns else [""]
    telas_lista = [""] + df_listas['Tela'].dropna().unique().tolist() if 'Tela' in df_listas.columns else [""]

    total_productos = 0.0
    productos_temp = []

    for i in range(st.session_state.num_productos):
        suffix = st.session_state.force_refresh
        cols = st.columns([3, 3, 2, 2])
        with cols[0]:
            producto = st.selectbox(f"Producto {i+1}", productos_lista, key=f"producto_{i}_{suffix}")
        with cols[1]:
            tela = st.selectbox(f"Tela {i+1}", telas_lista, key=f"tela_{i}_{suffix}")
        with cols[2]:
            precio_unit = st.number_input(f"Precio {i+1}", min_value=0.0, value=0.0, key=f"precio_unit_{i}_{suffix}")
        with cols[3]:
            cantidad = st.number_input(f"Cantidad {i+1}", min_value=1, value=1, key=f"cantidad_{i}_{suffix}")

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
        if st.button("➕ Añadir otro producto", key=f"crear_add_producto_{st.session_state.force_refresh}"):
            st.session_state.num_productos += 1
            st.rerun()

    with remove_col:
        if st.session_state.num_productos > 1:
            if st.button("➖ Quitar último producto", key=f"crear_remove_producto_{st.session_state.force_refresh}"):
                st.session_state.num_productos -= 1
                st.rerun()

    # --- RESTO DEL FORMULARIO ---
    with st.form("nuevo_pedido_form"):
        suffix = st.session_state.force_refresh
        next_id = get_next_id(df_pedidos, 'ID')
        st.info(f"El próximo ID de pedido será: **{next_id}**")

        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input("Cliente*", key=f"cliente_{suffix}")
            telefono = st.text_input("Teléfono*", max_chars=9, key=f"telefono_{suffix}")
            club = st.text_input("Club*", key=f"club_{suffix}")
            descripcion = st.text_area("Descripción", key=f"descripcion_{suffix}")

        with col2:
            fecha_entrada = st.date_input("Fecha entrada", value=datetime.now().date(), key=f"fecha_entrada_{suffix}")
            tiene_fecha_salida = st.checkbox("Establecer fecha de salida", key=f"tiene_fecha_salida_{suffix}")
            fecha_salida = st.date_input("Fecha salida", value=datetime.now().date(), key=f"fecha_salida_{suffix}") if tiene_fecha_salida else None
            precio = st.number_input("Precio total", min_value=0.0, value=total_productos, key=f"precio_total_{suffix}")
            precio_factura = st.number_input("Precio factura", min_value=0.0, value=0.0, key=f"precio_factura_{suffix}")
            tipos_pago = [""] + df_listas['Tipo de pago'].dropna().unique().tolist() if 'Tipo de pago' in df_listas.columns else [""]
            tipo_pago = st.selectbox("Tipo de pago", tipos_pago, key=f"tipo_pago_{suffix}")
            adelanto = st.number_input("Adelanto", min_value=0.0, value=0.0, key=f"adelanto_{suffix}")
            observaciones = st.text_area("Observaciones", key=f"observaciones_{suffix}")

        st.write("**Estado del pedido:**")
        estado_cols = st.columns(5)
        with estado_cols[0]:
            empezado = st.checkbox("Empezado", key=f"empezado_{suffix}")
        with estado_cols[1]:
            terminado = st.checkbox("Terminado", key=f"terminado_{suffix}")
        with estado_cols[2]:
            cobrado = st.checkbox("Cobrado", key=f"cobrado_{suffix}")
        with estado_cols[3]:
            retirado = st.checkbox("Retirado", key=f"retirado_{suffix}")
        with estado_cols[4]:
            pendiente = st.checkbox("Pendiente", key=f"pendiente_{suffix}")

        if st.form_submit_button("Guardar Nuevo Pedido", key=f"guardar_{suffix}"):
            if not cliente or not telefono or not club:
                st.error("Por favor complete los campos obligatorios (*)")
                return

            if not telefono.isdigit() or len(telefono) != 9:
                st.error("El teléfono debe contener exactamente 9 dígitos numéricos")
                return

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

                # Activar reseteo y nueva clave de refresco
                st.session_state.reset_form = True
                st.session_state.force_refresh = str(datetime.now().timestamp())

                # 🔑 Forzar rerun inmediato para que se limpie al instante
                st.rerun()
            else:
                st.error("Error al crear el pedido")
