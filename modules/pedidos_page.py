import streamlit as st

from modules.pedido.crear_pedido import show_create
from modules.pedido.consultar_pedidos import show_consult
from modules.pedido.modificar_pedido import show_modify
from modules.pedido.eliminar_pedido import show_delete


def show_pedidos_page(df_pedidos, df_listas):

    st.header("📦 Pedidos")
    st.write("---")

    # =================================================
    # ESTADO DE NAVEGACIÓN REAL (NO WIDGET)
    # =================================================
    if "pedido_view" not in st.session_state:
        st.session_state.pedido_view = "menu"

    view = st.session_state.pedido_view

    # =================================================
    # VISTAS INTERNAS (SIN MENÚ)
    # =================================================
    if view == "crear":
        show_create(df_pedidos, df_listas)
        return

    if view == "consultar":
        show_consult(df_pedidos, df_listas)
        return

    if view == "modificar":
        show_modify(df_pedidos, df_listas)
        return

    if view == "eliminar":
        show_delete(df_pedidos, df_listas)
        return

    # =================================================
    # MENÚ (SOLO AQUÍ)
    # =================================================
    opcion = st.radio(
        "¿Qué quieres hacer?",
        [
            "➕ Crear",
            "🔍 Consultar",
            "✏️ Modificar",
            "🗑️ Eliminar",
        ],
        key="pedido_menu_radio",
        horizontal=True
    )

    if opcion == "➕ Crear":
        st.session_state.pedido_view = "crear"
        st.rerun()

    if opcion == "🔍 Consultar":
        st.session_state.pedido_view = "consultar"
        st.rerun()

    if opcion == "✏️ Modificar":
        st.session_state.pedido_view = "modificar"
        st.rerun()

    if opcion == "🗑️ Eliminar":
        st.session_state.pedido_view = "eliminar"
        st.rerun()
