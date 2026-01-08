import streamlit as st
import pandas as pd
import json
from datetime import datetime
import io


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


def show_consult(df_pedidos, df_listas=None):
    st.subheader("🔍 Consultar Pedido por ID")
    st.write("---")

    if df_pedidos is None or df_pedidos.empty:
        st.info("📭 No hay pedidos.")
        return

    df_pedidos["Año"] = pd.to_numeric(
        df_pedidos["Año"], errors="coerce"
    ).fillna(datetime.now().year).astype(int)

    df_pedidos["ID"] = pd.to_numeric(
        df_pedidos["ID"], errors="coerce"
    ).fillna(0).astype(int)

    años = sorted(df_pedidos["Año"].unique(), reverse=True)

    col_a, col_b = st.columns(2)
    with col_a:
        año = st.selectbox("📅 Año", años, key="consult_year")

    df_año = df_pedidos[df_pedidos["Año"] == año]
    if df_año.empty:
        st.info("📭 No hay pedidos ese año.")
        return

    max_id = int(df_año["ID"].max())

    with col_b:
        pedido_id = st.number_input(
            "🆔 ID del pedido",
            min_value=1,
            value=max_id,
            step=1,
            key="consult_id"
        )

    pedido_df = df_año[df_año["ID"] == pedido_id]
    if pedido_df.empty:
        st.info("No existe ese pedido.")
        return

    pedido = pedido_df.iloc[0]

    st.markdown("### 📄 Datos del pedido")
    st.write(f"**Cliente:** {pedido.get('Cliente','')}")
    st.write(f"**Club:** {pedido.get('Club','')}")
    st.write(f"**Precio:** {float(pedido.get('Precio',0)):.2f} €")

    st.markdown("### 🧵 Productos")
    productos = parse_productos(pedido.get("Productos"))
    if productos:
        st.dataframe(pd.DataFrame(productos), use_container_width=True, hide_index=True)
    else:
        st.info("No hay productos.")
