import streamlit as st

from modules.pedido.crear_pedido import show_create
from modules.pedido.consultar_pedidos import show_consult
from modules.pedido.modificar_pedido import show_modify
from modules.pedido.eliminar_pedido import show_delete


def show_pedidos_page(df_pedidos, df_listas):

    st.header("📦 Pedidos")
    st.write("---")

    # =================================================
    # INICIALIZAR ESTADOS
    # =================================================
    if "pedido_modo" not in st.session_state:
        st.session_state.pedido_modo = "menu"

    if "pedido_section" not in st.session_state:
        st.session_state.pedido_section = None

    # =================================================
    # MODO MENÚ (SIEMPRE PRIMERO)
    # =================================================
    if st.session_state.pedido_modo == "menu":

        opciones = [
            "➕ Crear",
            "🔍 Consultar",
            "✏️ Modificar",
            "🗑️ Eliminar",
        ]

        seleccion = st.radio(
            "¿Qué quieres hacer?",
            opciones,
            key="pedido_radio",
            horizontal=True
        )

        if seleccion:
            st.session_state.pedido_section = seleccion
            st.session_state.pedido_modo = "accion"
            st.rerun()

        st.info("👆 Selecciona una opción para continuar.")
        return

    # =================================================
    # MODO ACCIÓN
    # =================================================
    section = st.session_state.pedido_section

    if section == "➕ Crear":
        show_create(df_pedidos, df_listas)
        return

    if section == "🔍 Consultar":
        show_consult(df_pedidos, df_listas)
        return

    if section == "✏️ Modificar":
        show_modify(df_pedidos, df_listas)
        return

    if section == "🗑️ Eliminar":
        show_delete(df_pedidos, df_listas)
        return
