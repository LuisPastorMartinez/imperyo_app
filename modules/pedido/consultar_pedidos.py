import streamlit as st
import pandas as pd
import json
from datetime import datetime
import io
from utils.data_utils import limpiar_telefono

def cargar_productos_seguro(productos_json):
    try:
        if isinstance(productos_json, str):
            return json.loads(productos_json) if productos_json.strip() else []
        if isinstance(productos_json, list):
            return productos_json
        return []
    except Exception:
        return []

def formatear_primer_producto(productos_json):
    productos = cargar_productos_seguro(productos_json)
    if not productos:
        return "Sin productos"

    p = productos[0]
    nombre = p.get("Producto", "")
    tela = p.get("Tela", "")
    cantidad = int(p.get("Cantidad", 1))
    precio_total = float(p.get("PrecioUnitario", 0.0)) * cantidad

    resumen = nombre
    if tela:
        resumen += f" ({tela})"
    resumen += f" x{cantidad} → {precio_total:.2f}€"
    if len(productos) > 1:
        resumen += " +P"

    return resumen

def show_consult(df_pedidos, df_listas):
    st.subheader("📋 Consultar Pedidos")
    st.write("---")

    if df_pedidos is None or df_pedidos.empty:
        st.info("No hay pedidos registrados.")
        return

    # ✅ AÑOS DISPONIBLES (mayor → menor)
    años_disponibles = sorted(
        df_pedidos['Año'].dropna().unique(),
        reverse=True
    )

    año_seleccionado = st.selectbox(
        "📅 Año del pedido",
        años_disponibles,
        index=0,
        key="consulta_año_select"
    )

    st.session_state.selected_year = año_seleccionado

    # ✅ FILTRAR POR AÑO
    df = df_pedidos[df_pedidos['Año'] == año_seleccionado].copy()

    if df.empty:
        st.info(f"No hay pedidos en el año {año_seleccionado}.")
        return

    # --- KPIs ---
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("✔️ Completados", len(df[(df['Trabajo Terminado']) & (df['Cobrado']) & (df['Retirado'])]))
    with col2:
        st.metric("📌 Pendientes", len(df[df['Pendiente']]))
    with col3:
        st.metric("🔵 Empezados", len(df[df['Inicio Trabajo']]))
    with col4:
        st.metric("✅ Terminados", len(df[df['Trabajo Terminado']]))
    with col5:
        st.metric("🆕 Nuevos", len(df[
            (~df['Inicio Trabajo']) &
            (~df['Pendiente']) &
            (~df['Trabajo Terminado']) &
            (~df['Cobrado']) &
            (~df['Retirado'])
        ]))

    st.write("---")

    # --- BÚSQUEDA GLOBAL ---
    search = st.text_input("🔍 Buscar (Cliente, Producto, Teléfono, ID...)")

    if search:
        df = df[df.apply(lambda r: search.lower() in str(r).lower(), axis=1)]

    # --- FORMATEO ---
    df_display = df.copy()

    if 'Productos' in df_display.columns:
        df_display['Productos'] = df_display['Productos'].apply(formatear_primer_producto)

    for col in ['Fecha entrada', 'Fecha Salida']:
        if col in df_display.columns:
            df_display[col] = pd.to_datetime(df_display[col], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')

    df_display['Pedido'] = df_display.apply(
        lambda r: f"{int(r['ID'])} / {int(r['Año'])}",
        axis=1
    )

    columnas = [
        'Pedido', 'Productos', 'Cliente', 'Club', 'Telefono',
        'Fecha entrada', 'Fecha Salida', 'Precio', 'Precio Factura'
    ]
    columnas = [c for c in columnas if c in df_display.columns]

    df_display = df_display.sort_values('ID', ascending=False)

    st.dataframe(
        df_display[columnas],
        use_container_width=True,
        hide_index=True
    )

    st.caption(f"Mostrando {len(df_display)} pedidos del año {año_seleccionado}")

    # --- EXPORTAR ---
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Pedidos")

    st.download_button(
        "📥 Descargar Excel",
        buffer.getvalue(),
        f"pedidos_{año_seleccionado}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
