# pages/pedidos_page.py
import streamlit as st
from pages.pedido.crear_pedido import show_create
from pages.pedido.consultar_pedidos import show_consult
from pages.pedido.modificar_pedido import show_modify
from pages.pedido.eliminar_pedido import show_delete
from utils import load_dataframes_firestore


def show_pedidos_page(df_pedidos=None, df_listas=None):
    """
    Página principal de gestión de pedidos
    """

    # Cargar datos si no vienen como argumento
    if df_pedidos is None or df_listas is None:
        data = st.session_state.get('data')
        if data and 'df_pedidos' in data and 'df_listas' in data:
            df_pedidos = data['df_pedidos']
            df_listas = data['df_listas']
        else:
            data = load_dataframes_firestore()
            if not data:
                st.error("No se pudieron cargar los datos desde Firestore.")
                return
            df_pedidos = data['df_pedidos']
            df_listas = data['df_listas']
            st.session_state['data'] = data

    # Leer pestaña activa desde session_state (si venimos de consultar)
    default_tab = st.session_state.get("active_pedido_tab", "Crear Pedido")

    # Siempre mostrar las 4 pestañas
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Crear Pedido", "Consultar Pedidos", "Modificar", "Eliminar"]
    )

    with tab1:
        show_create(df_pedidos, df_listas)

    with tab2:
        show_consult(df_pedidos, df_listas)

    with tab3:
        show_modify(df_pedidos, df_listas)

    with tab4:
        show_delete(df_pedidos, df_listas)

    # 🔹 Limpiar el indicador después de usarlo
    if "active_pedido_tab" in st.session_state:
        del st.session_state["active_pedido_tab"]
