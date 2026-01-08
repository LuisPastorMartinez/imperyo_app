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
    # AÑO ACTIVO (SIDEBAR)
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
    # TABS (FORMA CORRECTA)
    # =================================================
    tab_crear, tab_consultar, tab_modificar, tab_eliminar = st.tabs([
        "➕ Crear Pedido",
        "🔍 Consultar",
        "✏️ Modificar",
        "🗑️ Eliminar"
    ])

    # =================================================
    # CREAR
    # =================================================
    with tab_crear:
        show_create(df_filtrado, df_listas)

    # =================================================
    # CONSULTAR
    # =================================================
    with tab_consultar:
        if df_filtrado.empty:
            st.info("📭 No hay pedidos para este año.")
        else:
            show_consult(df_filtrado, df_listas)

    # =================================================
    # MODIFICAR
    # =================================================
    with tab_modificar:
        if df_pedidos.empty:
            st.info("📭 No hay pedidos para modificar.")
        else:
            show_modify(df_pedidos, df_listas)

    # =================================================
    # ELIMINAR
    # =================================================
    with tab_eliminar:
        if df_pedidos.empty:
            st.info("📭 No hay pedidos para eliminar.")
        else:
            show_delete(df_pedidos, df_listas)
