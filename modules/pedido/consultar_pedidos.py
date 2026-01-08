import streamlit as st
import pandas as pd
import json
from datetime import datetime
import io


# =====================================================
# UTIL
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

            if isinstance(v, (list, dict)):
                return str(v)
            if isinstance(v, datetime):
                return v.replace(tzinfo=None)
            return v

        df_export[col] = df_export[col].apply(clean_value)

    return df_export


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


# =====================================================
# CONSULTAR
# =====================================================
def show_consult(df_pedidos, df_listas=None):
    st.subheader("🔍 Consultar Pedido por ID")
    st.write("---")

    if df_pedidos is None or df_pedidos.empty:
        st.info("📭 No hay pedidos.")
        return

    # ---------- TIPOS ----------
    df_pedidos["Año"] = pd.to_numeric(
        df_pedidos["Año"], errors="coerce"
    ).fillna(datetime.now().year).astype(int)

    df_pedidos["ID"] = pd.to_numeric(
        df_pedidos["ID"], errors="coerce"
    ).fillna(0).astype(int)

    # ---------- SELECTORES ----------
    años = sorted(df_pedidos["Año"].unique(), reverse=True)

    col_a, col_b = st.columns(2)
    with col_a:
        año = st.selectbox("📅 Año", años, key="consult_year")
    with col_b:
        pedido_id = st.number_input(
            "🆔 ID del pedido",
            min_value=1,
            step=1,
            key="consult_id"
        )

    pedido_df = df_pedidos[
        (df_pedidos["Año"] == año) &
        (df_pedidos["ID"] == pedido_id)
    ]

    if pedido_df.empty:
        st.info("Introduce un ID válido para ver el pedido.")
        return

    pedido = pedido_df.iloc[0]

    # =================================================
    # DATOS GENERALES
    # =================================================
    st.markdown("### 📄 Datos del pedido")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Cliente", pedido.get("Cliente", ""))
    with c2:
        st.metric("Teléfono", pedido.get("Telefono", ""))
    with c3:
        st.metric("Club", pedido.get("Club", ""))

    c4, c5, c6 = st.columns(3)
    with c4:
        st.metric("Precio", f"{float(pedido.get('Precio', 0)):.2f} €")
    with c5:
        st.metric("Precio factura", f"{float(pedido.get('Precio Factura', 0)):.2f} €")
    with c6:
        st.metric("Estado",
            "Pendiente" if pedido.get("Pendiente") else
            "Completado" if (
                pedido.get("Trabajo Terminado")
                and pedido.get("Cobrado")
                and pedido.get("Retirado")
            ) else
            "En proceso"
        )

    if pedido.get("Breve Descripción"):
        st.markdown(f"**📝 Descripción:** {pedido.get('Breve Descripción')}")

    st.write("---")

    # =================================================
    # PRODUCTOS
    # =================================================
    st.markdown("### 🧵 Productos")

    productos = parse_productos(pedido.get("Productos"))

    if productos:
        df_prod = pd.DataFrame(productos)
        df_prod["Total"] = (
            df_prod["PrecioUnitario"].astype(float) *
            df_prod["Cantidad"].astype(int)
        )
        st.dataframe(df_prod, use_container_width=True, hide_index=True)
    else:
        st.info("No hay productos en este pedido.")

    st.write("---")

    # =================================================
    # ESTADOS
    # =================================================
    st.markdown("### 🚦 Estado del pedido")

    e1, e2, e3, e4, e5 = st.columns(5)
    e1.metric("Empezado", "Sí" if pedido.get("Inicio Trabajo") else "No")
    e2.metric("Terminado", "Sí" if pedido.get("Trabajo Terminado") else "No")
    e3.metric("Cobrado", "Sí" if pedido.get("Cobrado") else "No")
    e4.metric("Retirado", "Sí" if pedido.get("Retirado") else "No")
    e5.metric("Pendiente", "Sí" if pedido.get("Pendiente") else "No")

    st.write("---")

    # =================================================
    # EXPORTAR SOLO ESTE PEDIDO
    # =================================================
    buffer = io.BytesIO()
    df_export = preparar_df_para_excel(pedido_df)

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Pedido")

    st.download_button(
        "📥 Descargar este pedido (Excel)",
        buffer.getvalue(),
        f"pedido_{pedido_id}_{año}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
