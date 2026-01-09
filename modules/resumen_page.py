import streamlit as st
import pandas as pd
from datetime import datetime
import io


# =====================================================
# PREPARAR DATAFRAME PARA EXCEL
# =====================================================
def preparar_df_para_excel(df: pd.DataFrame) -> pd.DataFrame:
    df_export = df.copy()

    for col in df_export.columns:
        if pd.api.types.is_datetime64tz_dtype(df_export[col]):
            df_export[col] = df_export[col].dt.tz_convert(None)

    for col in df_export.columns:
        def clean_value(v):
            try:
                if pd.isna(v):
                    return None
            except Exception:
                pass

            if isinstance(v, pd.Timestamp):
                return v.tz_convert(None) if v.tzinfo else v
            if isinstance(v, datetime):
                return v.replace(tzinfo=None) if v.tzinfo else v
            if isinstance(v, (list, dict)):
                return str(v)
            return v

        df_export[col] = df_export[col].apply(clean_value)

    return df_export


# =====================================================
# RESUMEN
# =====================================================
def show_resumen_page(df_pedidos):
    st.header("📊 Resumen de Pedidos")
    st.write("---")

    if df_pedidos is None or df_pedidos.empty:
        st.info("📭 No hay pedidos.")
        return

    # =================================================
    # 🔒 NORMALIZAR (IGUAL QUE consultar_pedidos.py)
    # =================================================
    df_pedidos = df_pedidos.copy()

    df_pedidos["Año"] = pd.to_numeric(
        df_pedidos["Año"], errors="coerce"
    ).fillna(datetime.now().year).astype(int)

    df_pedidos["ID"] = pd.to_numeric(
        df_pedidos["ID"], errors="coerce"
    ).fillna(0).astype(int)

    # =================================================
    # 🔥 ELIMINAR DUPLICADOS (SOLO VISTA)
    # =================================================
    if "id_documento_firestore" in df_pedidos.columns:
        df_pedidos = df_pedidos.drop_duplicates(
            subset=["Año", "ID", "id_documento_firestore"]
        )
    else:
        df_pedidos = df_pedidos.drop_duplicates(
            subset=["Año", "ID"]
        )

    # =================================================
    # SELECTORES (SIDEBAR)
    # =================================================
    años_disponibles = sorted(
        df_pedidos["Año"].unique(),
        reverse=True
    )

    año = st.sidebar.selectbox(
        "📅 Año",
        años_disponibles,
        index=0,
        key="resumen_year_select"
    )

    vistas = [
        "Todos los pedidos",
        "Nuevos pedidos",
        "Trabajos empezados",
        "Pedidos pendientes",
        "Trabajos terminados",
        "Trabajos completados",
    ]

    vista = st.sidebar.radio(
        "📂 Ver",
        vistas,
        index=0,
        key="resumen_view_select"
    )

    # =================================================
    # FILTRAR POR AÑO
    # =================================================
    df = df_pedidos[df_pedidos["Año"] == año].copy()
    if df.empty:
        st.info(f"📭 No hay pedidos en {año}.")
        return

    # =================================================
    # FILTRO POR VISTA
    # =================================================
    if vista == "Todos los pedidos":
        filtered = df

    elif vista == "Nuevos pedidos":
        filtered = df[
            (~df["Inicio Trabajo"]) &
            (~df["Pendiente"]) &
            (~df["Trabajo Terminado"]) &
            (~df["Cobrado"]) &
            (~df["Retirado"])
        ]

    elif vista == "Trabajos empezados":
        filtered = df[
            (df["Inicio Trabajo"]) &
            (~df["Trabajo Terminado"])
        ]

    elif vista == "Pedidos pendientes":
        filtered = df[df["Pendiente"]]

    elif vista == "Trabajos terminados":
        filtered = df[
            (df["Trabajo Terminado"]) &
            ~(df["Cobrado"] & df["Retirado"])
        ]

    elif vista == "Trabajos completados":
        filtered = df[
            (df["Trabajo Terminado"]) &
            (df["Cobrado"]) &
            (df["Retirado"])
        ]

    else:
        filtered = df

    # =================================================
    # KPIs
    # =================================================
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric("📦 Total", len(filtered))
    with c2:
        st.metric(
            "✔️ Completados",
            len(df[
                (df["Trabajo Terminado"]) &
                (df["Cobrado"]) &
                (df["Retirado"])
            ])
        )
    with c3:
        st.metric("📌 Pendientes", len(df[df["Pendiente"]]))
    with c4:
        st.metric("🔵 Empezados", len(df[df["Inicio Trabajo"]]))
    with c5:
        st.metric(
            "🆕 Nuevos",
            len(df[
                (~df["Inicio Trabajo"]) &
                (~df["Pendiente"]) &
                (~df["Trabajo Terminado"]) &
                (~df["Cobrado"]) &
                (~df["Retirado"])
            ])
        )

    st.write("---")

    if filtered.empty:
        st.info("📭 No hay pedidos en esta vista.")
        return

    # =================================================
    # TABLA
    # =================================================
    df_show = filtered.copy()
    df_show["Pedido"] = df_show.apply(
        lambda r: f"{int(r['ID'])} / {int(r['Año'])}", axis=1
    )

    for col in ["Fecha entrada", "Fecha Salida"]:
        if col in df_show.columns:
            df_show[col] = (
                pd.to_datetime(df_show[col], errors="coerce")
                .dt.strftime("%Y-%m-%d")
                .fillna("")
            )

    columnas = [
        "Pedido", "Cliente", "Club", "Telefono",
        "Fecha entrada", "Fecha Salida",
        "Precio", "Precio Factura"
    ]
    columnas = [c for c in columnas if c in df_show.columns]

    st.dataframe(
        df_show.sort_values("ID", ascending=False)[columnas],
        use_container_width=True,
        hide_index=True
    )

    st.caption(f"Mostrando {len(filtered)} pedidos · {vista} · {año}")

    # =================================================
    # EXPORTAR
    # =================================================
    buffer = io.BytesIO()
    df_export = preparar_df_para_excel(filtered)

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Resumen")

    st.download_button(
        "📥 Descargar Excel",
        buffer.getvalue(),
        f"resumen_{vista.replace(' ', '_').lower()}_{año}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
