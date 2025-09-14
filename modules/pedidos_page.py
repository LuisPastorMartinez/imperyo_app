# pages/pedidos_page.py
import streamlit as st
from modules.pedido import show_create, show_consult, show_modify, show_delete
from utils.firestore_utils import load_dataframes_firestore

def show_pedidos_page(df_pedidos=None, df_listas=None):
    """
    Entry page para Streamlit. Si df_pedidos/df_listas son None,
    intenta cargar desde st.session_state.data o desde load_dataframes_firestore().
    """
    # Preferir parámetros si se pasaron
    if df_pedidos is None or df_listas is None:
        # Intentar obtener de session_state
        data = st.session_state.get('data')
        if data and 'df_pedidos' in data and 'df_listas' in data:
            df_pedidos = data['df_pedidos']
            df_listas = data['df_listas']
        else:
            # Cargar desde Firestore si está disponible
            try:
                data = load_dataframes_firestore()
                if not data:
                    st.error("No se pudieron cargar los datos. Revisa la conexión a Firestore.")
                    return
                df_pedidos = data['df_pedidos']
                df_listas = data['df_listas']
                st.session_state['data'] = data
            except Exception as e:
                st.error(f"Error al cargar datos desde Firestore: {e}")
                return

    # Verificar que ambos DataFrames estén disponibles
    if df_pedidos is None or df_listas is None:
        st.error("Faltan datos esenciales: df_pedidos o df_listas.")
        return

    # Opcional: advertir si están vacíos
    if df_pedidos.empty:
        st.warning("No hay pedidos registrados aún.")
    if df_listas.empty:
        st.warning("No se encontraron listas de referencia (productos, clubes, etc.).")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Crear Pedido",
        "Consultar Pedidos", 
        "Modificar Pedido",
        "Eliminar Pedido"
    ])

    with tab1:
        show_create(df_pedidos, df_listas)

    with tab2:
        show_consult(df_pedidos, df_listas)

    with tab3:
        show_modify(df_pedidos, df_listas)

    with tab4:
        show_delete(df_pedidos, df_listas)

# Solo se ejecuta si se llama directamente (para pruebas)
if __name__ == "__main__":
    show_pedidos_page()