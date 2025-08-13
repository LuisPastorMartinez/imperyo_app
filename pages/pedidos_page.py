import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils import get_next_id, save_dataframe_firestore, delete_document_firestore
import logging

logger = logging.getLogger(__name__)

def show_pedidos_page(df_pedidos, df_listas):
    # Configuración de pestañas
    tab1, tab2, tab3, tab4 = st.tabs(["Crear Pedido", "Consultar Pedidos", "Modificar Pedido", "Eliminar Pedido"])
    
    def convert_to_firestore_type(value):
        """Convierte los valores a tipos compatibles con Firestore"""
        if pd.isna(value) or value is None or value == "":
            return None
            
        # Manejo de fechas
        if isinstance(value, (date, pd.Timestamp)):
            if isinstance(value, date):
                return datetime.combine(value, datetime.min.time())
            elif isinstance(value, pd.Timestamp):
                return value.to_pydatetime()
                
        # Manejo de booleanos
        if isinstance(value, bool):
            return value
            
        # Manejo de números
        try:
            if isinstance(value, (int, float)):
                return value
            if float(value):
                return float(value)
        except (ValueError, TypeError):
            pass
            
        return str(value)
    
    # ===== Pestaña 1: Crear Pedido =====
    with tab1:
        st.subheader("Crear Nuevo Pedido")
        
        with st.form("nuevo_pedido_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                producto = st.selectbox(
                    "Producto*",
                    [""] + df_listas['Producto'].dropna().unique().tolist(),
                    key="new_producto"
                )
                cliente = st.text_input("Cliente*", key="new_cliente")
                telefono = st.text_input("Teléfono*", key="new_telefono")
                club = st.text_input("Club", key="new_club")
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
                    value=date.today(),
                    key="new_fecha_entrada"
                )
                fecha_salida = st.date_input(
                    "Fecha salida", 
                    value=None,
                    key="new_fecha_salida"
                )
                precio = st.number_input("Precio*", min_value=0.0, value=0.0, key="new_precio")
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
                pendiente = st.checkbox("Pendiente", value=True, key="new_pendiente")
            
            if st.form_submit_button("Guardar Nuevo Pedido"):
                if not cliente or not telefono or not producto or precio <= 0:
                    st.error("Por favor complete los campos obligatorios (*)")
                else:
                    try:
                        new_id = get_next_id(df_pedidos, 'ID')
                        new_pedido = {
                            'ID': new_id,
                            'Producto': producto,
                            'Cliente': cliente,
                            'Telefono': telefono,
                            'Club': club,
                            'Talla': talla,
                            'Tela': tela,
                            'Breve Descripción': descripcion,
                            'Fecha entrada': fecha_entrada,
                            'Fecha Salida': fecha_salida if fecha_salida else None,
                            'Precio': float(precio),
                            'Precio Factura': float(precio_factura),
                            'Tipo de pago': tipo_pago if tipo_pago else None,
                            'Adelanto': float(adelanto),
                            'Observaciones': observaciones,
                            'Inicio Trabajo': bool(empezado),
                            'Trabajo Terminado': bool(terminado),
                            'Cobrado': bool(cobrado),
                            'Retirado': bool(retirado),
                            'Pendiente': bool(pendiente),
                            'id_documento_firestore': None
                        }
                        
                        # Convertir tipos para Firestore
                        for key, value in new_pedido.items():
                            new_pedido[key] = convert_to_firestore_type(value)
                        
                        # Añadir al DataFrame
                        new_pedido_df = pd.DataFrame([new_pedido])
                        df_pedidos = pd.concat([df_pedidos, new_pedido_df], ignore_index=True)
                        
                        # Guardar en Firestore
                        if save_dataframe_firestore(df_pedidos, 'pedidos'):
                            st.success(f"Pedido {new_id} creado correctamente!")
                            st.session_state.data['df_pedidos'] = df_pedidos
                            st.rerun()
                        else:
                            st.error("Error al crear el pedido")
                    except Exception as e:
                        logger.error(f"Error creando pedido: {e}")
                        st.error(f"Error al crear el pedido: {str(e)}")

    # Resto del código de las otras pestañas permanece igual...
    # [Aquí irían las otras pestañas sin cambios en el manejo de fechas]