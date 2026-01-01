import streamlit as st
import pandas as pd
import io
from datetime import datetime


def preparar_df_para_excel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara un DataFrame para exportar a Excel:
    - Elimina NaT / NaN
    - Convierte datetimes con timezone a naive
    - Convierte listas y dicts a string
    """
    df_export = df.copy()

    # 1️⃣ Columnas datetime con timezone
    for col in df_export.columns:
        if pd.api.types.is_datetime64tz_dtype(df_export[col]):
            df_export[col] = df_export[col].dt.tz_convert(None)

    # 2️⃣ Limpiar valores individuales
    for col in df_export.columns:
        def clean_value(v):
            # NaT / NaN
            try:
                if pd.isna(v):
                    return None
            except Exception:
                pass

            # pandas Timestamp
            if isinstance(v, pd.Timestamp):
                if v.tzinfo is not None:
                    return v.tz_convert(None)
                return v

            # datetime con timezone
            if isinstance(v, datetime):
                if v.tzinfo is not None:
                    return v.replace(tzinfo=None)
                return v

            # listas / dicts
            if isinstance(v, (list, dict)):
                return str(v)

            return v

        df_export[col] = df_export[col].apply(clean_value)

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
        df[columnas_visibles].sort_values("ID", ascending=False),
        use_container_width=True
    )

    st.write("---")
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
