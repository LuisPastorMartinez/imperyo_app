import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime, date

from utils.firestore_utils import update_document_firestore
from utils.data_utils import limpiar_telefono
from .helpers import convert_to_firestore_type, safe_select_index


def safe_to_date(value):
    if value is None:
        return datetime.now().date()
    try:
        if pd.isna(value):
            return datetime.now().date()
    except Exception:
        pass
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except Exception:
            return datetime.now().date()
    return datetime.now().date()


def parse_productos(value):
    if not value:
        return []
    try:
        if isinstance(value, str):
            return json.loads(value)
        if isinstance(value, list):
            return value
    except Exception:
        pass
    return []


def show_modify(df_pedidos, df_listas):
    st.subheader("✏️ Modificar Pedido")
    st.write("---")

    if df_pedidos is None or df_pedidos.empty:
        st.info("📭 No hay pedidos.")
        return

    df_pedidos["Año"] = pd.to_numeric(
        df_pedidos["Año"], errors="coerce"
    ).fillna(datetime.now().year).astype(int)

    años = sorted(df_pedidos["Año"].unique(), reverse=True)
    año = st.selectbox("📅 Año del pedido", años, key="mod_year")

    df_año = df_pedidos[df_pedidos["Año"] == año]
    if df_año.empty:
        st.info("📭 No hay pedidos ese año.")
        return

    df_año["ID"] = pd.to_numeric(df_año["ID"], errors="coerce").fillna(0).astype(int)
    max_id = int(df_año["ID"].max())

    pedido_id = st.number_input(
        "🆔 ID del pedido",
        min_value=1,
        value=max_id,
        step=1,
        key="mod_id"
    )

    pedido_df = df_año[df_año["ID"] == pedido_id]
    if pedido_df.empty:
        st.warning("⚠️ No existe ese pedido.")
        return

    pedido = pedido_df.iloc[0]

    pedido_key = f"{año}_{pedido_id}"

    if st.session_state.get("pedido_key") != pedido_key:
        productos = parse_productos(pedido.get("Productos"))
        if not productos:
            productos = [{"Producto": "", "Tela": "", "PrecioUnitario": 0.0, "Cantidad": 1}]
        st.session_state.productos_modificar = [dict(p) for p in productos]
        st.session_state.pedido_key = pedido_key

    productos = st.session_state.productos_modificar

    productos_lista = [""] + (
        df_listas["Producto"].dropna().unique().tolist()
        if df_listas is not None and "Producto" in df_listas.columns else []
    )
    telas_lista = [""] + (
        df_listas["Tela"].dropna().unique().tolist()
        if df_listas is not None and "Tela" in df_listas.columns else []
    )

    st.markdown("### 🧵 Productos del pedido")

    total = 0.0
    for i, p in enumerate(productos):
        cols = st.columns([3, 3, 2, 2])
        with cols[0]:
            p["Producto"] = st.selectbox(
                f"Producto {i+1}",
                productos_lista,
                index=safe_select_index(productos_lista, p.get("Producto", "")),
                key=f"mod_prod_{pedido_key}_{i}"
            )
        with cols[1]:
            p["Tela"] = st.selectbox(
                f"Tela {i+1}",
                telas_lista,
                index=safe_select_index(telas_lista, p.get("Tela", "")),
                key=f"mod_tela_{pedido_key}_{i}"
            )
        with cols[2]:
            p["PrecioUnitario"] = st.number_input(
                "Precio €",
                min_value=0.0,
                value=float(p.get("PrecioUnitario", 0.0)),
                step=0.5,
                key=f"mod_precio_{pedido_key}_{i}"
            )
        with cols[3]:
            p["Cantidad"] = st.number_input(
                "Cantidad",
                min_value=1,
                value=int(p.get("Cantidad", 1)),
                step=1,
                key=f"mod_cantidad_{pedido_key}_{i}"
            )
        total += p["PrecioUnitario"] * p["Cantidad"]

    st.markdown(f"**💰 Subtotal productos:** {total:.2f} €")
