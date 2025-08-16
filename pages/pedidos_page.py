# pages/pedidos_page.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from utils import get_next_id, save_dataframe_firestore, delete_document_firestore

def show_pedidos_page(df_pedidos, df_listas):
    # Definir las 4 pestañas
    tab1, tab2, tab3, tab4 = st.tabs(["Crear Pedido", "Consultar Pedidos", "Modificar Pedido", "Eliminar Pedido"])
    
    # Función para conversión segura de tipos (versión corregida)
    def convert_to_firestore_type(value):
        """Convierte los valores a tipos compatibles con Firestore"""
        if pd.isna(value) or value is None or value == "":
            return None
        elif isinstance(value, (int, float, str, bool)):
            return value
        elif isinstance(value, (date, datetime)):
            return datetime.combine(value, datetime.min.time()) if isinstance(value, date) else value
        elif isinstance(value, pd.Timestamp):
            return value.to_pydatetime()
        elif isinstance(value, (np.integer, np.floating)):
            return int(value) if isinstance(value, np.integer) else float(value)
        try:
            return str(value)
        except (ValueError, TypeError):
            return None
    
    # ==============================================
    # Pestaña 1: Crear Pedido
    # ==============================================
    with tab1:
        st.subheader("Crear Nuevo Pedido")
        
        with st.form("nuevo_pedido_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                producto = st.selectbox(
                    "Producto*",
                    [""] + df_listas['Producto'].dropna().unique().tolist(),
                    key="new_producto"
                )
                cliente = st.text_input("Cliente*", key="new_cliente")
                telefono = st.text_input("Teléfono*", key="new_telefono")
                club = st.text_input("Club*", key="new_club")
                talla = st.selectbox(
                    "Talla",
                    [""] + df_listas['Talla'].dropna().unique().tolist(),
                    key="new_talla"
                )
                tela = st.selectbox(
                    "Tela",
                    [""] + df_listas['Tela'].dropna().unique().tolist(),
                    key="new_tela"
                )
                descripcion = st.text_area("Descripción", key="new_descripcion")
            
            with col2:
                fecha_entrada = st.date_input(
                    "Fecha entrada*", 
                    value=datetime.now(),
                    key="new_fecha_entrada"
                )
                fecha_salida = st.date_input(
                    "Fecha salida", 
                    value=None,
                    key="new_fecha_salida"
                )
                precio = st.number_input("Precio", min_value=0.0, value=0.0, key="new_precio")
                precio_factura = st.number_input(
                    "Precio factura", 
                    min_value=0.0, 
                    value=0.0,
                    key="new_precio_factura"
                )
                tipo_pago = st.selectbox(
                    "Tipo de pago",
                    [""] + df_listas['Tipo de pago'].dropna().unique().tolist(),
                    key="new_tipo_pago"
                )
                adelanto = st.number_input(
                    "Adelanto", 
                    min_value=0.0, 
                    value=0.0,
                    key="new_adelanto"
                )
                observaciones = st.text_area("Observaciones", key="new_observaciones")
            
            # Estado del pedido
            st.write("**Estado del pedido:**")
            estado_cols = st.columns(5)
            with estado_cols[0]:
                empezado = st.checkbox("Empezado", value=False, key="new_empezado")
            with estado_cols[1]:
                terminado = st.checkbox("Terminado", value=False, key="new_terminado")
            with estado_cols[2]:
                cobrado = st.checkbox("Cobrado", value=False, key="new_cobrado")
            with estado_cols[3]:
                retirado = st.checkbox("Retirado", value=False, key="new_retirado")
            with estado_cols[4]:
                pendiente = st.checkbox("Pendiente", value=False, key="new_pendiente")
            
            if st.form_submit_button("Guardar Nuevo Pedido"):
                if not cliente or not telefono or not producto or not club:
                    st.error("Por favor complete los campos obligatorios (*)")
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
                        'Precio': float(convert_to_firestore_type(precio)),
                        'Precio Factura': float(convert_to_firestore_type(precio_factura)),
                        'Tipo de pago': convert_to_firestore_type(tipo_pago),
                        'Adelanto': float(convert_to_firestore_type(adelanto)),
                        'Observaciones': convert_to_firestore_type(observaciones),
                        'Inicio Trabajo': bool(convert_to_firestore_type(empezado)),
                        'Trabajo Terminado': bool(convert_to_firestore_type(terminado)),
                        'Cobrado': bool(convert_to_firestore_type(cobrado)),
                        'Retirado': bool(convert_to_firestore_type(retirado)),
                        'Pendiente': bool(convert_to_firestore_type(pendiente)),
                        'id_documento_firestore': None
                    }
                    
                    # Asegurar que el DataFrame tenga las columnas correctas
                    if 'df_pedidos' not in st.session_state.data:
                        st.session_state.data['df_pedidos'] = pd.DataFrame(columns=new_pedido.keys())
                    
                    # Añadir al DataFrame
                    new_pedido_df = pd.DataFrame([new_pedido])
                    df_pedidos = pd.concat([df_pedidos, new_pedido_df], ignore_index=True)
                    
                    # Convertir tipos numéricos explícitamente
                    numeric_cols = ['Precio', 'Precio Factura', 'Adelanto']
                    for col in numeric_cols:
                        df_pedidos[col] = pd.to_numeric(df_pedidos[col], errors='coerce')
                    
                    # Guardar en Firestore
                    if save_dataframe_firestore(df_pedidos, 'pedidos'):
                        st.success(f"Pedido {new_id} creado correctamente!")
                        st.session_state.data['df_pedidos'] = df_pedidos
                        st.rerun()
                    else:
                        st.error("Error al crear el pedido")

    # Resto del código permanece igual...
    # [Las otras pestañas (Consultar, Modificar, Eliminar) no se modificaron]