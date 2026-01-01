import streamlit as st
import pandas as pd
from datetime import datetime

from modules.pedido import show_create, show_consult, show_modify, show_delete

def show_pedidos_page(df_pedidos=None, df_listas=None):

    if df_pedidos is None or df_listas is None:
        data = st.session_state.get('data', {})
        df_pedidos = data.get('df_pedidos')
        df_listas = data.get('df_listas')

    if df_pedidos is None or df_listas is None:
        st.error("No se pudieron cargar los datos.")
        return

    # ✅ AÑOS DISPONIBLES (mayor → menor)
    años = sorted(
        df_pedidos['Año'].dropna().unique(),
        reverse=True
    ) if not df_pedidos.empty else [datetime.now().year]

    año = st.sidebar.selectbox(
        "📅 Año",
        años,
        index=0,
        key="pedidos_year_select"
    )

    st.session_state.selected_year = año

    df_filtrado = df_pedidos[df_pedidos['Año'] == año].copy()

    st.header(f"📦 Pedidos — {año}")
    st.write("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Crear Pedido",
        "🔍 Consultar",
        "✏️ Modificar",
        "🗑️ Eliminar"
    ])

    with tab1:
        show_create(df_filtrado, df_listas)

    with tab2:
        show_consult(df_filtrado, df_listas)

    with tab3:
        show_modify(df_pedidos, df_listas)

    with tab4:
        show_delete(df_pedidos, df_listas)
