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


def show_consult(df_pedidos, df_listas=None):
    st.subheader("🔍 Consultar Pedido")
    st.write("---")

    df_pedidos["Año"] = pd.to_numeric(
        df_pedidos["Año"], errors="coerce"
    ).fillna(datetime.now().year).astype(int)

    df_pedidos["ID"] = pd.to_numeric(
        df_pedidos["ID"], errors="coerce"
    ).fillna(0).astype(int)

    años = sorted(df_pedidos["Año"].unique(), reverse=True)
    año = st.selectbox("Año", años, key="consult_year")

    df_año = df_pedidos[df_pedidos["Año"] == año]
    max_id = int(df_año["ID"].max())

    pedido_id = st.number_input(
        "ID",
        min_value=1,
        value=max_id,
        step=1,
        key="consult_id"
    )

    pedido = df_año[df_año["ID"] == pedido_id]
    if pedido.empty:
        st.info("No existe ese pedido.")
        return

    pedido = pedido.iloc[0]

    st.dataframe(pd.DataFrame([{
        "Pedido": f"{pedido_id}/{año}",
        "Cliente": pedido.get("Cliente"),
        "Teléfono": pedido.get("Telefono"),
        "Club": pedido.get("Club"),
        "Precio": pedido.get("Precio"),
        "Precio factura": pedido.get("Precio Factura")
    }]), use_container_width=True, hide_index=True)

    if st.button("✏️ Ir a modificar este pedido", type="primary"):
        st.session_state.mod_year = año
        st.session_state.mod_id = pedido_id
        st.session_state.go_to_modify = True
        st.rerun()
