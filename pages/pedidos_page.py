import streamlit as st
from pages.pedido.crear_pedido import show_create
from pages.pedido.consultar_pedido import show_consult
from pages.pedido.modificar_pedido import show_modify
from pages.pedido.eliminar_pedido import show_delete

def show_pedidos_page(df_pedidos=None, df_listas=None):
    st.title("Gestión de Pedidos")

    # Protección por si no llegan los DataFrames desde app.py
    if df_pedidos is None:
        st.error("No se han cargado los pedidos. Asegúrate de pasar df_pedidos desde app.py")
        return
    if df_listas is None:
        st.error("No se han cargado las listas. Asegúrate de pasar df_listas desde app.py")
        return

    # Menú lateral para navegar entre secciones
    menu = st.sidebar.radio(
        "Selecciona una acción:",
        ["Crear Pedido", "Consultar Pedido", "Modificar Pedido", "Eliminar Pedido"]
    )

    if menu == "Crear Pedido":
        show_create(df_pedidos, df_listas)
    elif menu == "Consultar Pedido":
        show_consult(df_pedidos)
    elif menu == "Modificar Pedido":
        show_modify(df_pedidos, df_listas)
    elif menu == "Eliminar Pedido":
        show_delete(df_pedidos)

# Solo ejecutar si corres este archivo directamente (útil para pruebas aisladas)
if __name__ == "__main__":
    import pandas as pd
    df_pedidos = pd.DataFrame()
    df_listas = pd.DataFrame()
    show_pedidos_page(df_pedidos, df_listas)
