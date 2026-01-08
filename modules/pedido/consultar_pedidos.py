import streamlit as st
import pandas as pd
import json
from datetime import datetime


# =====================================================
# UTILIDADES
# =====================================================
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
    """
    Convierte fechas a string seguro.
    Soporta None, NaT, datetime y string.
    """
    if v is None:
        return ""

    # NaT de pandas
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass

    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d")

    return str(v)


# =====================================================
# CONSULTAR PEDIDO
# =====================================================
def show_consult(df_pedidos, df_listas=None):
    st.subheader("🔍 Consultar Pedido")
    st.write("---")

    if df_pedidos is None or df_pedidos.empty:
        st.info("📭 No hay pedidos.")
        return

    # ---------- NORMALIZAR ----------
    df_pedidos = df_pedidos.copy()

    df_pedidos["Año"] = pd.to_numeric(
        df_pedidos["Año"], errors="coerce"
    ).fillna(datetime.now().year).astype(int)

    df_pedidos["ID"] = pd.to_numeric(
        df_pedidos["ID"], errors="coerce"
    ).fillna(0).astype(int)

    # ---------- SELECTORES ----------
    años = sorted(df_pedidos["Año"].unique(), reverse=True)
    año = st.selectbox("📅 Año", años, key="consult_year")

    df_año = df_pedidos[df_pedidos["Año"] == año]
    if df_año.empty:
        st.info("📭 No hay pedidos ese año.")
        return

    max_id = int(df_año["ID"].max())
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

    # =================================================
    # DATOS PRINCIPALES (1 FILA)
    # =================================================
    st.markdown("### 📄 Datos del pedido")

    datos_pedido = pd.DataFrame([{
        "Pedido": f"{pedido_id} / {año}",
        "Cliente": pedido.get("Cliente", ""),
        "Teléfono": pedido.get("Telefono", ""),
        "Club": pedido.get("Club", ""),
        "Precio (€)": float(pedido.get("Precio", 0) or 0),
        "Precio factura (€)": float(pedido.get("Precio Factura", 0) or 0),
    }])

    st.dataframe(datos_pedido, use_container_width=True, hide_index=True)

    if pedido.get("Breve Descripción"):
        st.caption(f"📝 {pedido.get('Breve Descripción')}")

    # =================================================
    # FECHAS
    # =================================================
    st.markdown("### 📅 Fechas")

    fechas_df = pd.DataFrame([{
        "Entrada": safe_date(pedido.get("Fecha entrada")),
        "Salida": safe_date(pedido.get("Fecha Salida")),
    }])

    st.dataframe(fechas_df, hide_index=True, use_container_width=True)

    # =================================================
    # ESTADOS
    # =================================================
    st.markdown("### 🚦 Estado del pedido")

    estados_df = pd.DataFrame([{
        "Empezado": "Sí" if pedido.get("Inicio Trabajo") else "No",
        "Terminado": "Sí" if pedido.get("Trabajo Terminado") else "No",
        "Cobrado": "Sí" if pedido.get("Cobrado") else "No",
        "Retirado": "Sí" if pedido.get("Retirado") else "No",
        "Pendiente": "Sí" if pedido.get("Pendiente") else "No",
    }])

    st.dataframe(estados_df, hide_index=True, use_container_width=True)

    # =================================================
    # PRODUCTOS
    # =================================================
    st.markdown("### 🧵 Productos")

    productos = parse_productos(pedido.get("Productos"))
    if productos:
        df_prod = pd.DataFrame(productos)
        df_prod["Total (€)"] = (
            df_prod["PrecioUnitario"].astype(float) *
            df_prod["Cantidad"].astype(int)
        )
        st.dataframe(df_prod, hide_index=True, use_container_width=True)
    else:
        st.info("No hay productos.")

    st.write("---")

    # =================================================
    # IR A MODIFICAR
    # =================================================
    if st.button("✏️ Ir a modificar este pedido", type="primary"):
        st.session_state.mod_year = año
        st.session_state.mod_id = pedido_id
        st.session_state.go_to_modify = True
        st.rerun()
