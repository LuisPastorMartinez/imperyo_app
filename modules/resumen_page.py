import streamlit as st
import pandas as pd
from datetime import datetime
import io


def preparar_df_para_excel(df: pd.DataFrame) -> pd.DataFrame:
    df_export = df.copy()

    # Columnas datetime con timezone
    for col in df_export.columns:
        if pd.api.types.is_datetime64tz_dtype(df_export[col]):
            df_export[col] = df_export[col].dt.tz_convert(None)

    # Limpiar valores
    for col in df_export.columns:
        def clean_value(v):
            try:
                if pd.isna(v):
                    return None
            except Exception:
                pass

            if isinstance(v, pd.Timestamp):
                if v.tzinfo is not None:
                    return v.tz_convert(None)
                return v

            if isinstance(v, datetime):
                if v.tzinfo is not None:
                    return v.replace(tzinfo=None)
                return v

            if isinstance(v, (list, dict)):
                return str(v)

            return v

        df_export[col] = df_export[col].apply(clean_value)

    return df_export


def show_resumen_page(df_pedidos, current_view):
    st.header("📊 Resumen de Pedidos")
    st.write("---")

    if df_pedidos is None or df_pedidos.empty:
        st.info("No hay pedidos.")
        return

    # ✅ AÑOS DISPONIBLES (mayor → menor)
    años_disponibles = sorted(
        df_pedidos['Año'].dropna().unique(),
        reverse=True
    )

    año = st.sidebar.selectbox(
        "📅 Año",
        años_disponibles,
        index=0,
        key="resumen_year_select"
    )

    st.session_state.selected_year = año

    df = df_pedidos[df_pedidos['Año'] == año].copy()
    if df.empty:
        st.info(f"No hay pedidos en {año}.")
        return

    # --- FILTRO POR VISTA ---
    if current_view == "Todos los Pedidos":
        filtered = df
    elif current_view == "Trabajos Empezados":
        filtered = df[(df['Inicio Trabajo']) & (~df['Pendiente'])]
    elif current_view == "Trabajos Terminados":
        filtered = df[(df['Trabajo Terminado']) & ~(df['Cobrado'] & df['Retirado'])]
    elif current_view == "Trabajos Completados":
        filtered = df[(df['Trabajo Terminado']) & (df['Cobrado']) & (df['Retirado'])]
    elif current_view == "Pedidos Pendientes":
        filtered = df[df['Pendiente']]
    elif current_view == "Nuevos Pedidos":
        filtered = df[
            (~df['Inicio Trabajo']) &
            (~df['Pendiente']) &
            (~df['Trabajo Terminado']) &
            (~df['Cobrado']) &
            (~df['Retirado'])
        ]
    else:
        filtered = df

    # --- KPIs ---
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("📦 Total", len(filtered))
    with c2:
        st.metric(
            "✔️ Completados",
            len(filtered[(filtered['Trabajo Terminado']) & (filtered['Cobrado']) & (filtered['Retirado'])])
        )
    with c3:
        st.metric("📌 Pendientes", len(filtered[filtered['Pendiente']]))
    with c4:
        st.metric("🔵 Empezados", len(filtered[filtered['Inicio Trabajo']]))
    with c5:
        st.metric(
            "🆕 Nuevos",
            len(filtered[
                (~filtered['Inicio Trabajo']) &
                (~filtered['Pendiente']) &
                (~filtered['Trabajo Terminado']) &
                (~filtered['Cobrado']) &
                (~filtered['Retirado'])
            ])
        )

    st.write("---")

    # --- CASO VACÍO (CLAVE) ---
    if filtered.empty:
        st.info("📭 No hay pedidos en esta vista.")
        return

    # --- FORMATEO ---
    df_show = filtered.copy()

    df_show['Pedido'] = df_show.apply(
        lambda r: f"{int(r['ID'])} / {int(r['Año'])}",
        axis=1
    )

    for col in ['Fecha entrada', 'Fecha Salida']:
        if col in df_show.columns:
            df_show[col] = (
                pd.to_datetime(df_show[col], errors='coerce')
                .dt.strftime('%Y-%m-%d')
                .fillna('')
            )

    columnas = [
        'Pedido', 'Cliente', 'Club', 'Telefono',
        'Fecha entrada', 'Fecha Salida', 'Precio', 'Precio Factura'
    ]
    columnas = [c for c in columnas if c in df_show.columns]

    df_show = df_show.sort_values('ID', ascending=False)

    st.dataframe(
        df_show[columnas],
        use_container_width=True,
        hide_index=True
    )

    st.caption(f"Mostrando {len(df_show)} pedidos del año {año}")

    # --- EXPORTAR ---
    buffer = io.BytesIO()
    df_export = preparar_df_para_excel(filtered)

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Resumen")

    st.download_button(
        "📥 Descargar Excel",
        buffer.getvalue(),
        f"resumen_{current_view.replace(' ', '_').lower()}_{año}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
