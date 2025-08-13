# pages/pedidos_page.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils import get_next_id, save_dataframe_firestore, delete_document_firestore

def show_pedidos_page(df_pedidos, df_listas):
    tab1, tab2, tab3, tab4 = st.tabs(["Crear Pedido", "Consultar Pedidos", "Modificar Pedido", "Eliminar Pedido"])
    
    def convert_to_firestore_type(value):
        if pd.isna(value) or value is None or value == "":
            return None
        elif isinstance(value, (int, float, str, bool)):
            return value
        elif isinstance(value, (date, datetime)):
            return datetime.combine(value, datetime.min.time()) if isinstance(value, date) else value
        elif isinstance(value, pd.Timestamp):
            return value.to_pydatetime()
        try:
            return float(value)
        except (ValueError, TypeError):
            return str(value)
    
    # ==============================================
    # Pestaña 1: Crear Pedido
    # ==============================================
    with tab1:
        st.subheader("Crear Nuevo Pedido")
        
        # Autocompletado: obtener valores únicos de la base
        clientes_existentes = sorted(df_pedidos['Cliente'].dropna().unique())
        telefonos_existentes = sorted(df_pedidos['Telefono'].dropna().unique())
        clubs_existentes = sorted(df_pedidos['Club'].dropna().unique())

        with st.form("nuevo_pedido_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                producto = st.selectbox(
                    "Producto*",
                    [""] + df_listas['Producto'].dropna().unique().tolist(),
                    key="new_producto"
                )
                # Cliente autocompletar
                cliente = st.selectbox(
                    "Cliente*",
                    [""] + list(clientes_existentes),
                    key="new_cliente"
                )
                cliente_input = st.text_input("Escribe nuevo cliente (si no está en la lista):", key="new_cliente_input")
                cliente_final = cliente_input if cliente_input else cliente

                # Teléfono autocompletar
                telefono = st.selectbox(
                    "Teléfono*",
                    [""] + list(telefonos_existentes),
                    key="new_telefono"
                )
                telefono_input = st.text_input("Escribe nuevo teléfono (si no está en la lista):", key="new_telefono_input")
                telefono_final = telefono_input if telefono_input else telefono

                # Club autocompletar, con asterisco en el label
                club = st.selectbox(
                    "Club*",
                    [""] + list(clubs_existentes),
                    key="new_club"
                )
                club_input = st.text_input("Escribe nuevo club (si no está en la lista):", key="new_club_input")
                club_final = club_input if club_input else club

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
                pendiente = st.checkbox("Pendiente", value=True, key="new_pendiente")
            
            if st.form_submit_button("Guardar Nuevo Pedido"):
                # Validación solo Cliente/Telefono/Club/Producto/Fecha entrada obligatorios
                if not cliente_final or not telefono_final or not club_final or not producto or not fecha_entrada:
                    st.error("Por favor, complete todos los campos obligatorios: Producto, Cliente, Teléfono, Club y Fecha entrada.")
                else:
                    new_id = get_next_id(df_pedidos, 'ID')
                    new_pedido = {
                        'ID': new_id,
                        'Producto': convert_to_firestore_type(producto),
                        'Cliente': convert_to_firestore_type(cliente_final),
                        'Telefono': convert_to_firestore_type(telefono_final),
                        'Club': convert_to_firestore_type(club_final),
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
                    
                    if save_dataframe_firestore(df_pedidos, 'pedidos'):
                        st.success(f"Pedido {new_id} creado correctamente!")
                        st.session_state.data['df_pedidos'] = df_pedidos
                        st.rerun()
                    else:
                        st.error("Error al crear el pedido")

    # ==============================================
    # El resto de pestañas permanece igual
    # ==============================================
    # ... (tabs de consultar, modificar y eliminar pedido igual que el anterior)