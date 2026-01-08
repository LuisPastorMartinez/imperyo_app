import streamlit as st
import pandas as pd
from datetime import datetime

from modules.pedido import (
    show_create,
    show_consult,
    show_modify,
    show_delete
)


def show_pedidos_page(df_pedidos, df_listas):

    st.header("📦 Pedidos")
    st.write("---")

    if "pedido_section" not in st.session_state:
        st.session_state.pedido_section = "➕ Crear"

    if st.session_state.get("go_to_modify"):
        st.session_state.pedido_section = "✏️ Modificar"
        st.session_state.pop("go_to_modify")

    section = st.radio(
        "Sección",
        ["➕ Crear", "🔍 Consultar", "✏️ Modificar", "🗑️ Eliminar"],
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
