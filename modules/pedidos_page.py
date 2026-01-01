import streamlit as st
import pandas as pd
from datetime import datetime

# Importamos las funciones del módulo pedido
try:
    from modules.pedido import show_create, show_consult, show_modify, show_delete
except ImportError as e:
    st.error(f"❌ Error al importar 'modules.pedido': {e}")
    st.stop()


def show_pedidos_page(df_pedidos=None, df_listas=None):
    """
    Página principal de Pedidos.
    Toda la lógica trabaja SIEMPRE con (Año + ID).
    """

    # ---------- CARGA DE DATOS ----------
    if df_pedidos is None or df_listas is None:
        data = st.session_state.get("data", {})
        if "df_pedidos" in data and "df_listas" in data:
            df_pedidos = data["df_pedidos"]
            df_listas = data["df_listas"]
        else:
            st.error("❌ No se encontraron los datos necesarios.")
            return

    if df_pedidos.empty:
        st.info("📭 No hay pedidos registrados aún.")
        return

    # ---------- ASEGURAR COLUMNA AÑO ----------
    if "Año" not in df_pedidos.columns:
        df_pedidos["Año"] = datetime.now().year

    df_pedidos["Año"] = pd.to_numeric(
        df_pedidos["Año"],
        errors="coerce"
    ).fillna(datetime.now().year).astype("int64")

    # ---------- SELECTOR DE AÑO ----------
    año_actual = datetime.now().year

    años_disponibles = sorted(
        df_pedidos["Año"].dropna().unique(),
        reverse=True
    )

    # Asegurar que el año actual siempre aparece
    if año_actual not in años_disponibles:
        años_disponibles.insert(0, año_actual)

    año_seleccionado = st.sidebar.selectbox(
        "📅 Filtrar por Año",
        options=años_disponibles,
        index=(
            años_disponibles.index(st.session_state.get("selected_year", año_actual))
            if st.session_state.get("selected_year", año_actual) in años_disponibles
            else 0
        ),
        key="pedidos_año_selector"
    )

    # Guardar año en sesión (global)
    st.session_state.selected_year = año_seleccionado

    # ---------- FILTRAR PEDIDOS POR AÑO ----------
    df_pedidos_filtrado = df_pedidos[
        df_pedidos["Año"] == año_seleccionado
    ].copy()

    # ---------- CALCULAR ESTADO (VISUAL) ----------
    def calcular_estado(row):
        if row.get("Pendiente", False):
            return "Pendiente"
        if (
            row.get("Trabajo Terminado", False)
            and row.get("Cobrado", False)
            and row.get("Retirado", False)
        ):
            return "Completado"
        if row.get("Trabajo Terminado", False):
            return "Terminado"
        if row.get("Inicio Trabajo", False):
            return "Empezado"
        return "Nuevo"

    if not df_pedidos_filtrado.empty:
        df_pedidos_filtrado["Estado"] = df_pedidos_filtrado.apply(
            calcular_estado, axis=1
        )

    # ---------- TÍTULO ----------
    st.subheader(f"📋 Gestión de Pedidos — Año {año_seleccionado}")
    st.write("---")

    # ---------- PESTAÑAS ----------
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "➕ Crear Pedido",
            "🔍 Consultar Pedidos",
            "✏️ Modificar Pedido",
            "🗑️ Eliminar Pedido",
        ]
    )

    # ---------- CREAR ----------
    with tab1:
        show_create(df_pedidos_filtrado, df_listas)

    # ---------- CONSULTAR ----------
    with tab2:
        show_consult(df_pedidos_filtrado, df_listas)

    # ---------- MODIFICAR ----------
    with tab3:
        show_modify(df_pedidos_filtrado, df_listas)

    # ---------- ELIMINAR ----------
    with tab4:
        show_delete(df_pedidos_filtrado, df_listas)
