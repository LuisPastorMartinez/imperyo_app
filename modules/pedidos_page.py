import streamlit as st

from modules.pedido.crear_pedido import show_create
from modules.pedido.consultar_pedidos import show_consult
from modules.pedido.modificar_pedido import show_modify
from modules.pedido.eliminar_pedido import show_delete


def show_pedidos_page(df_pedidos, df_listas):

    st.header("📦 Pedidos")
    st.write("---")

    # =================================================
    # MENÚ SIEMPRE VISIBLE (SIN SELECCIÓN POR DEFECTO)
    # =================================================
    opciones = [
        "— Selecciona una opción —",
        "➕ Crear",
        "🔍 Consultar",
        "✏️ Modificar",
        "🗑️ Eliminar",
    ]

    section = st.radio(
        "¿Qué quieres hacer?",
        opciones,
        index=0,
        key="pedido_section",
        horizontal=True
    )

    st.write("---")

    # =================================================
    # MOSTRAR SECCIÓN SOLO SI SE ELIGE UNA OPCIÓN
    # =================================================
    if section == "➕ Crear":
        show_create(df_pedidos, df_listas)

    elif section == "🔍 Consultar":
        show_consult(df_pedidos, df_listas)

    elif section == "✏️ Modificar":
        show_modify(df_pedidos, df_listas)

    elif section == "🗑️ Eliminar":
        show_delete(df_pedidos, df_listas)

    else:
        st.info("👆 Selecciona una opción del menú para empezar.")
