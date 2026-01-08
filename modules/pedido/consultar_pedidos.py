import streamlit as st
import pandas as pd
import json
from datetime import datetime
import io


# =====================================================
# UTILIDADES
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
# CONSULTAR PEDIDO
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

    # =================================================
    # DATOS DEL PEDIDO (TABLA 1 FILA)
    # =================================================
    st.markdown("### 📄 Datos del pedido")

    datos_pedido = pd.DataFrame([{
        "Pedido": f"{pedido_id} / {año}",
        "Cliente": pedido.get("Cliente", ""),
        "Teléfono": pedido.get("Telefono", ""),
        "Club": pedido.get("Club", ""),
        "Precio (€)": float(pedido.get("Precio", 0)),
        "Precio factura (€)": float(pedido.get("Precio Factura", 0)),
    }])

    st.dataframe(
        datos_pedido,
        use_container_width=True,
        hide_index=True
    )

    # =================================================
    # BOTÓN IR A MODIFICAR
    # =================================================
    if st.button("✏️ Ir a modificar este pedido", type="primary"):
        st.session_state["mod_year"] = año
        st.session_state["mod_id"] = pedido_id
        st.session_state["go_to_modify"] = True
        st.rerun()

    if pedido.get("Breve Descripción"):
        st.caption(f"📝 {pedido.get('Breve Descripción')}")

    st.write("---")

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
        st.dataframe(df_prod, use_container_width=True, hide_index=True)
    else:
        st.info("No hay productos en este pedido.")

    st.write("---")

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

    st.dataframe(
        estados_df,
        use_container_width=True,
        hide_index=True
    )

    st.write("---")

    # =================================================
    # EXPORTAR ESTE PEDIDO
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
