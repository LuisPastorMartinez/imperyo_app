import streamlit as st
import pandas as pd
import json
from datetime import datetime


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


def safe_date(v):
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d")
    return str(v)


def show_consult(df_pedidos, df_listas=None):

    # ===============================
    # SALIR
    # ===============================
    if st.button(⬅️ Volver a Pedidos"):
        st.session_state.pop("pedido_section", None)
        st.rerun()

    st.subheader("🔍 Consultar Pedido")
    st.write("---")

    if df_pedidos is None or df_pedidos.empty:
        st.info("📭 No hay pedidos.")
        return

    df_pedidos = df_pedidos.copy()
    df_pedidos["Año"] = pd.to_numeric(
        df_pedidos["Año"], errors="coerce"
    ).fillna(datetime.now().year).astype(int)

    años = sorted(df_pedidos["Año"].unique(), reverse=True)
    año = st.selectbox("📅 Año", años)

    df_año = df_pedidos[df_pedidos["Año"] == año]
    if df_año.empty:
        st.info("No hay pedidos ese año.")
        return

    pedido_id = st.number_input(
        "🆔 ID del pedido",
        min_value=1,
        value=int(df_año["ID"].max())
    )

    pedido_df = df_año[df_año["ID"] == pedido_id]
    if pedido_df.empty:
        st.warning("No existe ese pedido.")
        return

    pedido = pedido_df.iloc[0]

    st.markdown("### 📄 Datos del pedido")

    st.dataframe(pd.DataFrame([{
        "Pedido": f"{pedido_id}/{año}",
        "Cliente": pedido.get("Cliente", ""),
        "Teléfono": pedido.get("Telefono", ""),
        "Club": pedido.get("Club", ""),
        "Precio": pedido.get("Precio", 0),
        "Factura": pedido.get("Precio Factura", 0),
    }]), hide_index=True, use_container_width=True)

    st.markdown("### 🧵 Productos")

    productos = parse_productos(pedido.get("Productos"))
    if productos:
        df_prod = pd.DataFrame(productos)
        df_prod["Total"] = (
            df_prod["PrecioUnitario"].astype(float) *
            df_prod["Cantidad"].astype(int)
        )
        st.dataframe(df_prod, hide_index=True, use_container_width=True)
    else:
        st.info("No hay productos.")
