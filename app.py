import streamlit as st
import pandas as pd
from utils.firestore_utils import load_dataframes_firestore, save_dataframe_firestore, get_next_id

# Configuración de página
st.set_page_config(layout="wide")

# Función para reordenar columnas
def reorder_columns(df):
    """Ordena columnas poniendo ID, Cliente, Teléfono y Producto primero"""
    base_columns = ['ID', 'Cliente', 'Teléfono', 'Producto']
    other_columns = [col for col in df.columns if col not in base_columns]
    return df[base_columns + other_columns]

# Vista de Resumen mejorada
def view_resumen():
    st.header("Resumen de Pedidos")
    
    # Cargar y ordenar datos
    df_pedidos = st.session_state.data['df_pedidos'].sort_values('ID', ascending=False)
    df_pedidos = reorder_columns(df_pedidos)  # Aplicar nuevo orden
    
    # Filtros
    view_options = {
        "Todos": None,
        "En Progreso": "Inicio Trabajo",
        "Terminados": "Trabajo Terminado",
        "Pendientes": "Pendiente"
    }
    
    selected = st.selectbox("Filtrar por:", list(view_options.keys()))
    
    if view_options[selected]:
        filtered = df_pedidos[df_pedidos[view_options[selected]]]
    else:
        filtered = df_pedidos
    
    # Mostrar tabla
    if not filtered.empty:
        st.dataframe(
            filtered,
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "Cliente": st.column_config.TextColumn("Cliente", width="medium"),
                "Teléfono": st.column_config.TextColumn("Teléfono", width="medium"),
                "Producto": st.column_config.TextColumn("Producto", width="large")
            },
            height=600,
            use_container_width=True
        )
    else:
        st.warning(f"No hay pedidos {selected.lower()}")

# Formulario de Pedidos mejorado
def view_pedidos():
    st.header("Gestión de Pedidos")
    tab1, tab2 = st.tabs(["Nuevo Pedido", "Buscar Pedidos"])
    
    with tab1:
        with st.form("nuevo_pedido", clear_on_submit=True):
            st.subheader("Nuevo Pedido")
            
            # Generar ID
            next_id = get_next_id(st.session_state.data['df_pedidos'], 'ID')
            
            # Campos en el orden solicitado
            cols = st.columns(4)
            with cols[0]:
                st.text_input("ID", value=next_id, disabled=True)
            with cols[1]:
                cliente = st.text_input("Cliente*")
            with cols[2]:
                telefono = st.text_input("Teléfono")
            with cols[3]:
                producto = st.selectbox("Producto*", 
                                     options=st.session_state.data['df_listas']['Producto'].unique())
            
            # Resto del formulario...
            if st.form_submit_button("Guardar"):
                # Lógica para guardar
                pass

# Estructura principal
if 'data' not in st.session_state:
    st.session_state.data = load_dataframes_firestore()

# Menú
page = st.sidebar.radio("Navegación", ["Resumen", "Pedidos"])

if page == "Resumen":
    view_resumen()
elif page == "Pedidos":
    view_pedidos()