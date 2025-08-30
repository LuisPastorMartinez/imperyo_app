# pages/pedido/crear_pedido.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils import get_next_id, save_dataframe_firestore
from .helpers import convert_to_firestore_type

def show_create(df_pedidos, df_listas):
    st.subheader("Crear Nuevo Pedido")

    with st.form("nuevo_pedido_form"):
        col1, col2 = st.columns(2)
        with col1:
            productos = [""] + df_listas['Producto'].dropna().unique().tolist() if 'Producto' in df_listas.columns else [""]
            producto = st.selectbox("Producto*", productos, key="new_producto")
            cliente = st.text_input("Cliente*", key="new_cliente")
            telefono = st.text_input("Teléfono*", key="new_telefono", max_chars=15)
            club = st.text_input("Club*", key="new_club")
            tallas = [""] + df_listas['Talla'].dropna().unique().tolist() if 'Talla' in df_listas.columns else [""]
            talla = st.selectbox("Talla", tallas, key="new_talla")
            telas = [""] + df_listas['Tela'].dropna().unique().tolist() if 'Tela' in df_listas.columns else [""]
            tela = st.selectbox("Tela", telas, key="new_tela")
            descripcion = st.text_area("Descripción", key="new_descripcion")
        
        with col2:
            fecha_entrada = st.date_input("Fecha de entrada*", datetime.now(), key="new_fecha_entrada")
            fecha_salida = st.date_input("Fecha de Salida", key="new_fecha_salida")
            precio = st.number_input("Precio*", min_value=0.0, key="new_precio")
            precio_factura = st.number_input("Precio Factura", min_value=0.0, key="new_precio_factura")
            tipo_pago = st.selectbox("Tipo de Pago", ["", "Efectivo", "Transferencia", "Bizum"], key="new_tipo_pago")
            adelanto = st.number_input("Adelanto", min_value=0.0, key="new_adelanto")
            observaciones = st.text_area("Observaciones", key="new_observaciones")
            
        st.markdown("---")
        col_checkbox1, col_checkbox2, col_checkbox3, col_checkbox4, col_checkbox5 = st.columns(5)
        with col_checkbox1:
            empezado = st.checkbox("Empezado", key="new_empezado")
        with col_checkbox2:
            terminado = st.checkbox("Terminado", key="new_terminado")
        with col_checkbox3:
            cobrado = st.checkbox("Cobrado", key="new_cobrado")
        with col_checkbox4:
            retirado = st.checkbox("Retirado", key="new_retirado")
        with col_checkbox5:
            pendiente = st.checkbox("Pendiente", key="new_pendiente")

        st.markdown("---")
        submitted = st.form_submit_button("Guardar Pedido")

    if submitted:
        if not all([producto, cliente, telefono, club, fecha_entrada, precio]):
            st.warning("Por favor, rellene todos los campos obligatorios marcados con *.")
        else:
            new_id = get_next_id(df_pedidos, 'ID')
            new_pedido = {
                'ID': new_id,
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
                st.success(f"Pedido {new_id} creado correctamente!")
                
                # AÑADIDO: Establecer una bandera para la redirección
                st.session_state['redirect_to_consult'] = True
                st.rerun() 

            else:
                st.error("Error al crear el pedido.")