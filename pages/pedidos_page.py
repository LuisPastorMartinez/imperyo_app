import streamlit as st
from pages.pedido.crear_pedido import show_create
from pages.pedido.consultar_pedido import show_consult
from pages.pedido.modificar_pedido import show_modify
from pages.pedido.eliminar_pedido import show_delete

def show_pedidos_page(df_pedidos=None, df_listas=None):
    st.title("Gestión de Pedidos")

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

# ⚠️ IMPORTANTE: solo ejecutar si se corre este archivo directamente
# Si se importa desde app.py, la autenticación se gestiona allí
if __name__ == "__main__":
    show_pedidos_page()
