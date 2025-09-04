# pages/pedidos_page.py
import streamlit as st
from pages.pedido import show_create, show_consult, show_modify, show_delete
from utils import load_dataframes_firestore

def show_pedidos_page(df_pedidos=None, df_listas=None):
    """
    Entry page para Streamlit. Si df_pedidos/df_listas son None,
    intenta cargar desde st.session_state.data o desde load_dataframes_firestore().
    """
    # Preferir parámetros si se pasaron
    if df_pedidos is None or df_listas is None:
        # intentar obtener de session_state
        data = st.session_state.get('data')
        if data and 'df_pedidos' in data and 'df_listas' in data:
            df_pedidos = data['df_pedidos']
            df_listas = data['df_listas']
        else:
            # cargar desde Firestore si está disponible
            data = load_dataframes_firestore()
            if not data:
                st.error("No se pudieron cargar los datos. Revisa la conexión a Firestore.")
                return
            df_pedidos = data['df_pedidos']
            df_listas = data['df_listas']
            st.session_state['data'] = data

    tab1, tab2, tab3, tab4 = st.tabs(["Crear Pedido", "Consultar Pedidos", "Modificar Pedido", "Eliminar Pedido"])

    with tab1:
        show_create(df_pedidos, df_listas)

    with tab2:
        show_consult(df_pedidos, df_listas)

    with tab3:
        show_modify(df_pedidos, df_listas)

    with tab4:
        show_delete(df_pedidos, df_listas)

# Cuando Streamlit ejecute este fichero, mostramos la página:
if __name__ == "__main__" or True:
    # si otra parte del proyecto importa show_pedidos_page con args, se respetará;
    # en ejecución directa garantizamos que la página se muestre
    show_pedidos_page()
