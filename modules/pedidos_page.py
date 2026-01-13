import streamlit as st

from modules.pedido.crear_pedido import show_create
from modules.pedido.consultar_pedidos import show_consult
from modules.pedido.modificar_pedido import show_modify
from modules.pedido.eliminar_pedido import show_delete


def show_pedidos_page(df_pedidos, df_listas):

    st.header("📦 Pedidos")
    st.write("---")

    if "pedido_section" not in st.session_state:
        st.session_state.pedido_section = None

    section = st.radio(
        "¿Qué quieres hacer?",
        ["➕ Crear", "🔍 Consultar", "✏️ Modificar", "🗑️ Eliminar"],
        index=None,
        key="pedido_section"
    )

    if section == "➕ Crear":
        show_create(df_pedidos, df_listas)

    elif section == "🔍 Consultar":
        show_consult(df_pedidos, df_listas)

    elif section == "✏️ Modificar":
        show_modify(df_pedidos, df_listas)

    elif section == "🗑️ Eliminar":
        show_delete(df_pedidos, df_listas)
