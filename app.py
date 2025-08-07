import streamlit as st
import pandas as pd
import os
import hashlib
import re
from datetime import datetime
from utils.firestore_utils import load_dataframes_firestore, save_dataframe_firestore, delete_document_firestore, get_next_id

# --- CONFIGURACIÓN BÁSICA DE LA PÁGINA ---
st.set_page_config(
    page_title="ImperYo",
    page_icon="https://www.dropbox.com/scl/fi/opp61pwyq2lxleaj3hxs3/Logo-Movil-e-instagran.png?rlkey=4cruzlufwlz9vfr2myezjkz1d&dl=1",
    layout="wide"
)

# [Resto del código de configuración CSS y header permanece igual...]

# --- FUNCIÓN PARA LIMPIAR PRECIOS ---
def limpiar_precio(precio):
    """Convierte el precio a entero (sin decimales)"""
    if pd.isna(precio):
        return 0
    try:
        return int(float(precio))
    except:
        return 0

# --- FUNCIÓN PARA UNIFICAR COLUMNAS ---
def unificar_columnas(df):
    # Eliminar solo columnas no deseadas (manteniendo Pago Inicial/Adelanto)
    columnas_a_eliminar = ['Fechas Entrada']
    for col in columnas_a_eliminar:
        if col in df.columns:
            df = df.drop(columns=[col])
    
    # Unificar nombres para Pago Inicial/Adelanto
    if 'Pago Inicial' in df.columns and 'Adelanto' in df.columns:
        df['Adelanto'] = df['Adelanto'].combine_first(df['Pago Inicial'])
        df = df.drop(columns=['Pago Inicial'])
    elif 'Pago Inicial' in df.columns:
        df = df.rename(columns={'Pago Inicial': 'Adelanto'})
    
    # [Resto de la función unificar_columnas permanece igual...]
    
    # Limpiar precios (incluyendo Adelanto)
    for col_precio in ['Precio', 'Precio Factura', 'Precio factura', 'Adelanto']:
        if col_precio in df.columns:
            df[col_precio] = df[col_precio].apply(limpiar_precio)
    
    return df

# [Resto del código de autenticación permanece igual...]

# --- LÓGICA PRINCIPAL DE LA APLICACIÓN ---
if check_password():
    # --- CARGA Y CORRECCIÓN DE DATOS ---
    if 'data_loaded' not in st.session_state:
        st.session_state.data = load_dataframes_firestore()
        
        if 'df_pedidos' in st.session_state.data:
            st.session_state.data['df_pedidos'] = unificar_columnas(st.session_state.data['df_pedidos'])
        
        st.session_state.data_loaded = True

    # [Resto del código de navegación permanece igual...]

    elif page == "Pedidos":
        st.header("Gestión de Pedidos")
        tab_guardar, tab_buscar, tab_modificar, tab_eliminar = st.tabs(["Guardar Nuevo", "Buscar Pedido", "Modificar Pedido", "Eliminar Pedido"])

        with tab_guardar:
            st.subheader("Guardar Nuevo Pedido")
            next_pedido_id = get_next_id(df_pedidos, 'ID')
            st.write(f"ID del Nuevo Pedido: **{next_pedido_id}**")

            with st.form("form_guardar_pedido", clear_on_submit=True):
                col1, col2 = st.columns(2)

                with col1:
                    # [Campos anteriores permanecen igual...]
                    pass

                with col2:
                    # [Otros campos permanecen igual...]
                    adelanto = st.number_input("Adelanto/Pago Inicial", min_value=0, value=0, step=1, key="new_adelanto")
                    # [Resto de campos...]

                # [Resto del formulario permanece igual...]

                if submitted:
                    new_record = {
                        # [Otros campos...]
                        'Adelanto': st.session_state.new_adelanto,
                        # [Resto de campos...]
                    }

        with tab_modificar:
            st.subheader("Modificar Pedido")
            # [Código de búsqueda permanece igual...]
            
            if st.session_state.get('modifying_pedido'):
                current_pedido = st.session_state.modifying_pedido
                
                with st.form("form_modificar_pedido", clear_on_submit=False):
                    col1_mod, col2_mod = st.columns(2)

                    with col2_mod:
                        # [Otros campos...]
                        adelanto_mod = st.number_input("Adelanto/Pago Inicial", 
                                                     min_value=0, 
                                                     value=int(current_pedido.get('Adelanto', 0)), 
                                                     step=1, 
                                                     key="mod_adelanto")
                        # [Resto de campos...]

                    # [Resto del formulario permanece igual...]

                    if submitted_mod:
                        st.session_state.data['df_pedidos'].loc[row_index] = {
                            # [Otros campos...]
                            'Adelanto': st.session_state.mod_adelanto,
                            # [Resto de campos...]
                        }

        # [Resto de pestañas y funcionalidades permanece igual...]

    elif page == "Ver Datos":
        st.header("Datos Cargados de Firestore")
        st.subheader("Colección 'pedidos'")
        if not df_pedidos.empty:
            # Asegurarse de incluir la columna Adelanto
            new_column_order = [
                'ID', 'Producto', 'Cliente', 'Club', 'Telefono', 'Breve Descripción',
                'Fecha entrada', 'Fecha Salida', 'Precio', 'Precio Factura',
                'Tipo de pago', 'Adelanto', 'Observaciones'
            ]
            # [Resto del código de visualización...]

    # [Resto del código de la aplicación permanece igual...]