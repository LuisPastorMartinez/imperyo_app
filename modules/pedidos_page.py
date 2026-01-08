import streamlit as st
import pandas as pd
from datetime import datetime

from modules.pedido import (
    show_create,
    show_consult,
    show_modify,
    show_delete
)


def _empty_pedidos_df():
    return pd.DataFrame(columns=[
        "ID",
        "Año",
        "Cliente",
        "Telefono",
        "Club",
        "Precio",
        "Productos",
        "id_documento_firestore"
    ])


def show_pedidos_page(df_pedidos=None, df_listas=None):

    # =================================================
    # SESSION INIT
    # =================================================
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = 0  # Crear

    # 👉 VIENE DESDE CONSULTAR
    if st.session_state.get("go_to_modify"):
        st.session_state.active_tab = 2  # Modificar
        st.session_state.pop("go_to_modify")

    # =================================================
    # CARGA DATOS
    # =================================================
    if df_pedidos is None or df_listas is None:
        data = st.session_state.get("data", {})
        df_pedidos = data.get("df_pedidos")
        df_listas = data.get("df_listas")

    if df_listas is None:
        st.error("No se pudieron cargar las listas.")
        return

    if df_pedidos is None or df_pedidos.empty:
        df_pedidos = _empty_pedidos_df()
    else:
        if "Año" not in df_pedidos.columns:
            df_pedidos["Año"] = datetime.now().year

        df_pedidos["Año"] = (
            pd.to_numeric(df_pedidos["Año"], errors="coerce")
            .fillna(datetime.now().year)
            .astype("int64")
        )

    # =================================================
    # AÑO ACTIVO
    # =================================================
    años = sorted(df_pedidos["Año"].dropna().unique(), reverse=True)
    if not años:
        años = [datetime.now().year]

    año = st.sidebar.selectbox(
        "📅 Año",
        años,
        index=0,
        key="pedidos_year_select"
    )

    st.session_state.selected_year = año

    df_filtrado = df_pedidos[df_pedidos["Año"] == año].copy()

    st.header(f"📦 Pedidos — {año}")
    st.write("---")

    # =================================================
    # TABS (CONTROLADAS)
    # =================================================
    tab_labels = [
        "➕ Crear Pedido",
        "🔍 Consultar",
        "✏️ Modificar",
        "🗑️ Eliminar"
    ]

    tabs = st.tabs(tab_labels)

    # =================================================
    # RENDER TAB ACTIVA
    # =================================================
    with tabs[0]:
        if st.session_state.active_tab == 0:
            show_create(df_filtrado, df_listas)

    with tabs[1]:
        if st.session_state.active_tab == 1:
            if df_filtrado.empty:
                st.info("📭 No hay pedidos para este año.")
            else:
                show_consult(df_filtrado, df_listas)

    with tabs[2]:
        if st.session_state.active_tab == 2:
            if df_pedidos.empty:
                st.info("📭 No hay pedidos para modificar.")
            else:
                show_modify(df_pedidos, df_listas)

    with tabs[3]:
        if st.session_state.active_tab == 3:
            if df_pedidos.empty:
                st.info("📭 No hay pedidos para eliminar.")
            else:
                show_delete(df_pedidos, df_listas)

    # =================================================
    # ACTUALIZAR TAB ACTIVA (CUANDO EL USUARIO CAMBIA)
    # =================================================
    for i, tab in enumerate(tabs):
        if tab:
            st.session_state.active_tab = i
