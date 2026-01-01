import streamlit as st
import pandas as pd
import io
from datetime import datetime


def preparar_df_para_excel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte todas las columnas a tipos seguros para Excel.
    """
    df_export = df.copy()

    for col in df_export.columns:
        # Convertir listas / dicts / JSON a string
        df_export[col] = df_export[col].apply(
            lambda x: str(x) if isinstance(x, (list, dict)) else x
        )

    # Convertir NaT / NaN a None
    df_export = df_export.where(pd.notna(df_export), None)

    return df_export


def show_consult(df_pedidos, df_listas=None):
    st.subheader("🔍 Consultar Pedidos")
    st.write("---")

    if df_pedidos is None or df_pedidos.empty:
        st.info("📭 No hay pedidos.")
        return

    # ---------- ASEGURAR TIPOS ----------
    if "Año" in df_pedidos.columns:
        df_pedidos["Año"] = pd.to_numeric(
            df_pedidos["Año"], errors="coerce"
        ).fillna(datetime.now().year).astype("int64")

    if "ID" in df_pedidos.columns:
        df_pedidos["ID"] = pd.to_numeric(
            df_pedidos["ID"], errors="coerce"
        ).fillna(0).astype("int64")

    # ---------- FILTRO POR AÑO ----------
    años = sorted(
        df_pedidos["Año"].dropna().unique(),
        reverse=True
    )

    año = st.selectbox(
        "📅 Año",
        años,
        index=0,
        key="consult_year_selector"
    )

    df = df_pedidos[df_pedidos["Año"] == año].copy()

    if df.empty:
        st.info(f"📭 No hay pedidos en {año}.")
        return

    st.markdown(f"### 📦 Pedidos del año {año}")

    columnas_visibles = [
        "ID",
        "Cliente",
        "Club",
        "Precio",
        "Precio Factura",
        "Inicio Trabajo",
        "Trabajo Terminado",
        "Cobrado",
        "Retirado",
        "Pendiente",
    ]

    columnas_visibles = [c for c in columnas_visibles if c in df.columns]

    st.dataframe(
        df[columnas_visibles]
        .sort_values("ID", ascending=False),
        use_container_width=True
    )

    st.write("---")

    # ---------- EXPORTAR A EXCEL ----------
    st.markdown("### 📥 Exportar pedidos")

    buffer = io.BytesIO()

    df_export = preparar_df_para_excel(df)

    try:
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_export.to_excel(
                writer,
                index=False,
                sheet_name="Pedidos"
            )

        st.download_button(
            label="📥 Descargar Excel",
            data=buffer.getvalue(),
            file_name=f"pedidos_{año}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error("❌ Error al generar el Excel.")
        st.exception(e)
