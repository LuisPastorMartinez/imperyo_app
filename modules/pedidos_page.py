import streamlit as st

from modules.pedido.crear_pedido import show_create
from modules.pedido.consultar_pedidos import show_consult
from modules.pedido.modificar_pedido import show_modify
from modules.pedido.eliminar_pedido import show_delete


def show_pedidos_page(df_pedidos, df_listas):

    st.header("📦 Pedidos")
    st.write("---")

    section = st.session_state.get("pedido_section")

    # =================================================
    # SI ESTAMOS DENTRO DE UNA ACCIÓN → NO MENÚ
    # =================================================
    if section == "➕ Crear":
        show_create(df_pedidos, df_listas)
        return

    if section == "🔍 Consultar":
        show_consult(df_pedidos, df_listas)
        return

    if section == "✏️ Modificar":
        show_modify(df_pedidos, df_listas)
        return

    #if section == "🗑️ Eliminar":
        #show_delete(df_pedidos, df_listas)
       # return

    # =================================================
    # MENÚ PRINCIPAL
    # =================================================
    opciones = [
        "— Selecciona una opción —",
        "➕ Crear",
        "🔍 Consultar",
        "✏️ Modificar",
        "🗑️ Eliminar",
    ]

    st.radio(
        "¿Qué quieres hacer?",
        opciones,
        index=0,
        key="pedido_section",
        horizontal=True
    )

    st.info("👆 Selecciona una opción para continuar.")
