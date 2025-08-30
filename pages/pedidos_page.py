# pages/pedidos_page.py
import streamlit as st
from pages.pedido import show_create, show_consult, show_modify, show_delete
from utils import load_dataframes_firestore

def show_pedidos_page(df_pedidos=None, df_listas=None):
    """
    Entry page para Streamlit. Si df_pedidos/df_listas son None,
    intenta cargar desde st.session_state.data o desde load_dataframes_firestore().
    """
    if df_pedidos is None or df_listas is None:
        data = st.session_state.get('data')
        if data and 'df_pedidos' in data and 'df_listas' in data:
            df_pedidos = data['df_pedidos']
            df_listas = data['df_listas']
        else:
            data = load_dataframes_firestore()
            if not data:
                st.error("No se pudieron cargar los datos. Revisa la conexión a Firestore.")
                return
            df_pedidos = data['df_pedidos']
            df_listas = data['df_listas']
            st.session_state['data'] = data

    # INICIALIZACIÓN: Inicializar la pestaña activa en 'Crear Pedido' si no existe
    if 'active_tab' not in st.session_state:
        st.session_state['active_tab'] = "Crear Pedido"

    # COMPROBAR REDIRECCIÓN: Si la bandera 'redirect_to_consult' está activa, cambiar la pestaña
    if st.session_state.get('redirect_to_consult'):
        st.session_state['active_tab'] = "Consultar Pedidos"
        del st.session_state['redirect_to_consult'] # Limpiar la bandera para el siguiente ciclo

    # Mostrar las pestañas y el contenido basado en la variable de estado
    tab1, tab2, tab3, tab4 = st.tabs(["Crear Pedido", "Consultar Pedidos", "Modificar Pedido", "Eliminar Pedido"])

    if st.session_state['active_tab'] == "Crear Pedido":
        with tab1:
            show_create(df_pedidos, df_listas)
    elif st.session_state['active_tab'] == "Consultar Pedidos":
        with tab2:
            show_consult(df_pedidos, df_listas)
    elif st.session_state['active_tab'] == "Modificar Pedido":
        with tab3:
            show_modify(df_pedidos, df_listas)
    elif st.session_state['active_tab'] == "Eliminar Pedido":
        with tab4:
            show_delete(df_pedidos, df_listas)