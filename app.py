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

# --- FUNCIÓN DE AUTENTICACIÓN ---
def check_password():
    """Verifica la contraseña usando st.secrets o un valor predeterminado."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        password = st.text_input("Contraseña:", type="password", key="password_input")
        if password:
            correct_password = st.secrets.get("PASSWORD", "mipassword123")  # Usa secrets.toml o un valor predeterminado
            if hashlib.sha256(password.encode()).hexdigest() == correct_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
                return False
        return False
    return True

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
    
    # Limpiar precios (incluyendo Adelanto)
    for col_precio in ['Precio', 'Precio Factura', 'Precio factura', 'Adelanto']:
        if col_precio in df.columns:
            df[col_precio] = df[col_precio].apply(limpiar_precio)
    
    return df

# --- LÓGICA PRINCIPAL DE LA APLICACIÓN ---
if check_password():
    # --- CARGA Y CORRECCIÓN DE DATOS ---
    if 'data_loaded' not in st.session_state:
        st.session_state.data = load_dataframes_firestore()
        
        if 'df_pedidos' in st.session_state.data:
            st.session_state.data['df_pedidos'] = unificar_columnas(st.session_state.data['df_pedidos'])
        
        st.session_state.data_loaded = True

    # --- NAVEGACIÓN ---
    st.sidebar.title("Navegación")
    page = st.sidebar.radio("Selecciona una página:", ["Pedidos", "Ver Datos"])

    # Obtener DataFrames desde session_state
    df_pedidos = st.session_state.data.get('df_pedidos', pd.DataFrame())

    if page == "Pedidos":
        st.header("Gestión de Pedidos")
        tab_guardar, tab_buscar, tab_modificar, tab_eliminar = st.tabs(["Guardar Nuevo", "Buscar Pedido", "Modificar Pedido", "Eliminar Pedido"])

        with tab_guardar:
            st.subheader("Guardar Nuevo Pedido")
            next_pedido_id = get_next_id(df_pedidos, 'ID')
            st.write(f"ID del Nuevo Pedido: **{next_pedido_id}**")

            with st.form("form_guardar_pedido", clear_on_submit=True):
                col1, col2 = st.columns(2)

                with col1:
                    producto = st.text_input("Producto", key="new_producto")
                    cliente = st.text_input("Cliente", key="new_cliente")
                    club = st.text_input("Club", key="new_club")
                    telefono = st.text_input("Teléfono", key="new_telefono")

                with col2:
                    descripcion = st.text_area("Breve Descripción", key="new_descripcion")
                    fecha_entrada = st.date_input("Fecha Entrada", key="new_fecha_entrada")
                    fecha_salida = st.date_input("Fecha Salida", key="new_fecha_salida")
                    precio = st.number_input("Precio", min_value=0, value=0, step=1, key="new_precio")
                    precio_factura = st.number_input("Precio Factura", min_value=0, value=0, step=1, key="new_precio_factura")
                    tipo_pago = st.selectbox("Tipo de Pago", ["Efectivo", "Transferencia", "Tarjeta"], key="new_tipo_pago")
                    adelanto = st.number_input("Adelanto/Pago Inicial", min_value=0, value=0, step=1, key="new_adelanto")
                    observaciones = st.text_area("Observaciones", key="new_observaciones")

                submitted = st.form_submit_button("Guardar Pedido")

                if submitted:
                    new_record = {
                        'ID': next_pedido_id,
                        'Producto': producto,
                        'Cliente': cliente,
                        'Club': club,
                        'Telefono': telefono,
                        'Breve Descripción': descripcion,
                        'Fecha entrada': fecha_entrada.strftime("%Y-%m-%d"),
                        'Fecha Salida': fecha_salida.strftime("%Y-%m-%d"),
                        'Precio': precio,
                        'Precio Factura': precio_factura,
                        'Tipo de pago': tipo_pago,
                        'Adelanto': adelanto,
                        'Observaciones': observaciones
                    }
                    df_pedidos.loc[len(df_pedidos)] = new_record
                    save_dataframe_firestore('pedidos', df_pedidos)
                    st.success("Pedido guardado exitosamente!")

        with tab_modificar:
            st.subheader("Modificar Pedido")
            pedido_id = st.text_input("ID del Pedido a modificar:", key="mod_pedido_id")
            
            if pedido_id:
                pedido = df_pedidos[df_pedidos['ID'] == int(pedido_id)]
                if not pedido.empty:
                    st.session_state.modifying_pedido = pedido.iloc[0].to_dict()
                    st.success("Pedido encontrado. Edita los campos necesarios:")
            
            if st.session_state.get('modifying_pedido'):
                current_pedido = st.session_state.modifying_pedido
                row_index = df_pedidos[df_pedidos['ID'] == current_pedido['ID']].index[0]
                
                with st.form("form_modificar_pedido", clear_on_submit=False):
                    col1_mod, col2_mod = st.columns(2)

                    with col1_mod:
                        producto_mod = st.text_input("Producto", value=current_pedido.get('Producto', ''), key="mod_producto")
                        cliente_mod = st.text_input("Cliente", value=current_pedido.get('Cliente', ''), key="mod_cliente")
                        club_mod = st.text_input("Club", value=current_pedido.get('Club', ''), key="mod_club")
                        telefono_mod = st.text_input("Teléfono", value=current_pedido.get('Telefono', ''), key="mod_telefono")

                    with col2_mod:
                        descripcion_mod = st.text_area("Breve Descripción", value=current_pedido.get('Breve Descripción', ''), key="mod_descripcion")
                        fecha_entrada_mod = st.date_input("Fecha Entrada", value=datetime.strptime(current_pedido.get('Fecha entrada', '2000-01-01'), "%Y-%m-%d"), key="mod_fecha_entrada")
                        fecha_salida_mod = st.date_input("Fecha Salida", value=datetime.strptime(current_pedido.get('Fecha Salida', '2000-01-01'), "%Y-%m-%d"), key="mod_fecha_salida")
                        precio_mod = st.number_input("Precio", min_value=0, value=int(current_pedido.get('Precio', 0)), step=1, key="mod_precio")
                        precio_factura_mod = st.number_input("Precio Factura", min_value=0, value=int(current_pedido.get('Precio Factura', 0)), step=1, key="mod_precio_factura")
                        tipo_pago_mod = st.selectbox("Tipo de Pago", ["Efectivo", "Transferencia", "Tarjeta"], index=["Efectivo", "Transferencia", "Tarjeta"].index(current_pedido.get('Tipo de pago', 'Efectivo')), key="mod_tipo_pago")
                        adelanto_mod = st.number_input("Adelanto/Pago Inicial", min_value=0, value=int(current_pedido.get('Adelanto', 0)), step=1, key="mod_adelanto")
                        observaciones_mod = st.text_area("Observaciones", value=current_pedido.get('Observaciones', ''), key="mod_observaciones")

                    submitted_mod = st.form_submit_button("Actualizar Pedido")

                    if submitted_mod:
                        st.session_state.data['df_pedidos'].loc[row_index] = {
                            'ID': current_pedido['ID'],
                            'Producto': producto_mod,
                            'Cliente': cliente_mod,
                            'Club': club_mod,
                            'Telefono': telefono_mod,
                            'Breve Descripción': descripcion_mod,
                            'Fecha entrada': fecha_entrada_mod.strftime("%Y-%m-%d"),
                            'Fecha Salida': fecha_salida_mod.strftime("%Y-%m-%d"),
                            'Precio': precio_mod,
                            'Precio Factura': precio_factura_mod,
                            'Tipo de pago': tipo_pago_mod,
                            'Adelanto': adelanto_mod,
                            'Observaciones': observaciones_mod
                        }
                        save_dataframe_firestore('pedidos', df_pedidos)
                        st.success("Pedido actualizado exitosamente!")
                        st.session_state.modifying_pedido = None

    elif page == "Ver Datos":
        st.header("Datos Cargados de Firestore")
        st.subheader("Colección 'pedidos'")
        if not df_pedidos.empty:
            new_column_order = [
                'ID', 'Producto', 'Cliente', 'Club', 'Telefono', 'Breve Descripción',
                'Fecha entrada', 'Fecha Salida', 'Precio', 'Precio Factura',
                'Tipo de pago', 'Adelanto', 'Observaciones'
            ]
            st.dataframe(df_pedidos[new_column_order])
        else:
            st.warning("No hay datos de pedidos cargados.")