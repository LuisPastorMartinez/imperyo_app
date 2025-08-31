# pages/pedido/crear_pedido.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils import get_next_id, save_dataframe_firestore
from .helpers import convert_to_firestore_type
import time

def show_create(df_pedidos, df_listas):
    st.subheader("Crear Nuevo Pedido")

    # Se inicializa el estado de la sesión si no existe.
    if 'form_state' not in st.session_state:
        st.session_state.form_state = {
            "new_producto": "",
            "new_cliente": "",
            "new_telefono": "",
            "new_club": "",
            "new_talla": "",
            "new_tela": "",
            "new_descripcion": "",
            "new_fecha_entrada": datetime.now().date(),
            "new_tiene_fecha_salida": False,
            "new_fecha_salida": None,
            "new_precio": 0.0,
            "new_precio_factura": 0.0,
            "new_tipo_pago": "",
            "new_adelanto": 0.0,
            "new_observaciones": "",
            "new_empezado": False,
            "new_terminado": False,
            "new_cobrado": False,
            "new_retirado": False,
            "new_pendiente": False
        }

    # Función para resetear el formulario.
    def reset_form_state():
        st.session_state.form_state = {
            "new_producto": "",
            "new_cliente": "",
            "new_telefono": "",
            "new_club": "",
            "new_talla": "",
            "new_tela": "",
            "new_descripcion": "",
            "new_fecha_entrada": datetime.now().date(),
            "new_tiene_fecha_salida": False,
            "new_fecha_salida": None,
            "new_precio": 0.0,
            "new_precio_factura": 0.0,
            "new_tipo_pago": "",
            "new_adelanto": 0.0,
            "new_observaciones": "",
            "new_empezado": False,
            "new_terminado": False,
            "new_cobrado": False,
            "new_retirado": False,
            "new_pendiente": False
        }

    with st.form("nuevo_pedido_form"):
        next_id = get_next_id(df_pedidos, 'ID')
        st.info(f"El próximo ID de pedido será: **{next_id}**")
        
        col1, col2 = st.columns(2)
        with col1:
            productos = [""] + df_listas['Producto'].dropna().unique().tolist() if 'Producto' in df_listas.columns else [""]
            producto = st.selectbox("Producto*", productos, key="new_producto", index=productos.index(st.session_state.form_state["new_producto"]))
            cliente = st.text_input("Cliente*", key="new_cliente", value=st.session_state.form_state["new_cliente"])
            telefono = st.text_input("Teléfono*", key="new_telefono", value=st.session_state.form_state["new_telefono"], max_chars=15)
            club = st.text_input("Club*", key="new_club", value=st.session_state.form_state["new_club"])
            tallas = [""] + df_listas['Talla'].dropna().unique().tolist() if 'Talla' in df_listas.columns else [""]
            talla = st.selectbox("Talla", tallas, key="new_talla", index=tallas.index(st.session_state.form_state["new_talla"]))
            telas = [""] + df_listas['Tela'].dropna().unique().tolist() if 'Tela' in df_listas.columns else [""]
            tela = st.selectbox("Tela", telas, key="new_tela", index=telas.index(st.session_state.form_state["new_tela"]))
            descripcion = st.text_area("Descripción", key="new_descripcion", value=st.session_state.form_state["new_descripcion"])

        with col2:
            fecha_entrada = st.date_input("Fecha entrada", value=st.session_state.form_state["new_fecha_entrada"], key="new_fecha_entrada")
            tiene_fecha_salida = st.checkbox("Establecer fecha de salida", value=st.session_state.form_state["new_tiene_fecha_salida"], key="new_tiene_fecha_salida")
            if tiene_fecha_salida:
                fecha_salida = st.date_input("Fecha salida", value=st.session_state.form_state["new_fecha_salida"], key="new_fecha_salida")
            else:
                fecha_salida = None
            precio = st.number_input("Precio", min_value=0.0, value=st.session_state.form_state["new_precio"], key="new_precio")
            precio_factura = st.number_input("Precio factura", min_value=0.0, value=st.session_state.form_state["new_precio_factura"], key="new_precio_factura")
            tipos_pago = [""] + df_listas['Tipo de pago'].dropna().unique().tolist() if 'Tipo de pago' in df_listas.columns else [""]
            tipo_pago = st.selectbox("Tipo de pago", tipos_pago, key="new_tipo_pago", index=tipos_pago.index(st.session_state.form_state["new_tipo_pago"]))
            adelanto = st.number_input("Adelanto", min_value=0.0, value=st.session_state.form_state["new_adelanto"], key="new_adelanto")
            observaciones = st.text_area("Observaciones", value=st.session_state.form_state["new_observaciones"], key="new_observaciones")

        st.write("**Estado del pedido:**")
        estado_cols = st.columns(5)
        with estado_cols[0]:
            empezado = st.checkbox("Empezado", value=st.session_state.form_state["new_empezado"], key="new_empezado")
        with estado_cols[1]:
            terminado = st.checkbox("Terminado", value=st.session_state.form_state["new_terminado"], key="new_terminado")
        with estado_cols[2]:
            cobrado = st.checkbox("Cobrado", value=st.session_state.form_state["new_cobrado"], key="new_cobrado")
        with estado_cols[3]:
            retirado = st.checkbox("Retirado", value=st.session_state.form_state["new_retirado"], key="new_retirado")
        with estado_cols[4]:
            pendiente = st.checkbox("Pendiente", value=st.session_state.form_state["new_pendiente"], key="new_pendiente")

        if st.form_submit_button("Guardar Nuevo Pedido"):
            if not cliente or not telefono or not producto or not club:
                st.error("Por favor complete los campos obligatorios (*)")
                return

            if not telefono.isdigit() or len(telefono) != 9:
                st.error("El teléfono debe contener exactamente 9 dígitos numéricos")
                return

            new_pedido = {
                'ID': next_id,
                'Producto': convert_to_firestore_type(producto),
                'Cliente': convert_to_firestore_type(cliente),
                'Telefono': convert_to_firestore_type(telefono),
                'Club': convert_to_firestore_type(club),
                'Talla': convert_to_firestore_type(talla),
                'Tela': convert_to_firestore_type(tela),
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
                st.success(f"Pedido {next_id} creado correctamente!")
                
                # Resetea el formulario manualmente después de guardar
                reset_form_state()
                
                st.session_state.data['df_pedidos'] = df_pedidos
                st.experimental_rerun()
            else:
                st.error("Error al crear el pedido")