import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime, date

from utils.firestore_utils import update_document_firestore
from utils.data_utils import limpiar_telefono
from .helpers import convert_to_firestore_type, safe_select_index


# =========================
# UTILIDADES
# =========================
def safe_to_date(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
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
            return None
    return None


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


# =========================
# MODIFICAR PEDIDO
# =========================
def show_modify(df_pedidos, df_listas):
    st.subheader("✏️ Modificar Pedido")
    st.write("---")

    if df_pedidos is None or df_pedidos.empty:
        st.info("📭 No hay pedidos.")
        return

    # ---------- AÑOS ----------
    df_pedidos = df_pedidos.copy()
    df_pedidos["Año"] = pd.to_numeric(
        df_pedidos["Año"], errors="coerce"
    ).fillna(datetime.now().year).astype(int)

    años = sorted(df_pedidos["Año"].unique(), reverse=True)

    if "mod_year" not in st.session_state:
        st.session_state.mod_year = años[0]

    año = st.selectbox("📅 Año del pedido", años, key="mod_year")

    df_año = df_pedidos[df_pedidos["Año"] == año]
    if df_año.empty:
        st.info("📭 No hay pedidos ese año.")
        return

    # ---------- ID ----------
    df_año["ID"] = pd.to_numeric(df_año["ID"], errors="coerce").fillna(0).astype(int)
    max_id = int(df_año["ID"].max())

    if "mod_id" not in st.session_state:
        st.session_state.mod_id = max_id

    pedido_id = st.number_input(
        "🆔 ID del pedido",
        min_value=1,
        step=1,
        key="mod_id"
    )

    pedido_df = df_año[df_año["ID"] == pedido_id]
    if pedido_df.empty:
        st.warning("⚠️ No existe ese pedido.")
        return

    pedido = pedido_df.iloc[0]

    # ---------- PRODUCTOS ----------
    pedido_key = f"{año}_{pedido_id}"
    if st.session_state.get("pedido_key") != pedido_key:
        productos = parse_productos(pedido.get("Productos"))
        if not productos:
            productos = [{
                "Producto": "",
                "Tela": "",
                "PrecioUnitario": 0.0,
                "Cantidad": 1
            }]
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

    st.markdown("### 🧵 Productos")

    total = 0.0
    for i, p in enumerate(productos):
        c1, c2, c3, c4 = st.columns([3, 3, 2, 2])
        p["Producto"] = c1.selectbox(
            f"Producto {i+1}",
            productos_lista,
            index=safe_select_index(productos_lista, p.get("Producto", "")),
            key=f"mod_prod_{pedido_key}_{i}"
        )
        p["Tela"] = c2.selectbox(
            f"Tela {i+1}",
            telas_lista,
            index=safe_select_index(telas_lista, p.get("Tela", "")),
            key=f"mod_tela_{pedido_key}_{i}"
        )
        p["PrecioUnitario"] = c3.number_input(
            "Precio €",
            min_value=0.0,
            step=0.5,
            value=float(p.get("PrecioUnitario", 0.0)),
            key=f"mod_precio_{pedido_key}_{i}"
        )
        p["Cantidad"] = c4.number_input(
            "Cantidad",
            min_value=1,
            step=1,
            value=int(p.get("Cantidad", 1)),
            key=f"mod_cantidad_{pedido_key}_{i}"
        )
        total += p["PrecioUnitario"] * p["Cantidad"]

    st.markdown(f"**💰 Total productos:** {total:.2f} €")
    st.write("---")

    # ---------- FORMULARIO ----------
    with st.form("form_modificar"):
        col1, col2 = st.columns(2)

        with col1:
            cliente = st.text_input("Cliente", pedido.get("Cliente", ""))
            telefono = st.text_input("Teléfono", pedido.get("Telefono", ""))
            club = st.text_input("Club", pedido.get("Club", ""))

        with col2:
            precio = st.number_input(
                "Precio total (€)",
                min_value=0.0,
                value=float(pedido.get("Precio", 0.0))
            )
            precio_factura = st.number_input(
                "Precio factura (€)",
                min_value=0.0,
                value=float(pedido.get("Precio Factura", 0.0))
            )

            # ✅ FECHA SALIDA (NUEVO)
            fecha_salida = st.date_input(
                "📦 Fecha salida",
                value=safe_to_date(pedido.get("Fecha salida")),
                key="fecha_salida_mod"
            )

        st.markdown("### 🚦 Estado del pedido")
        e1, e2, e3, e4, e5 = st.columns(5)

        empezado = e1.checkbox("Empezado", bool(pedido.get("Inicio Trabajo", False)))
        terminado = e2.checkbox("Terminado", bool(pedido.get("Trabajo Terminado", False)))
        cobrado = e3.checkbox("Cobrado", bool(pedido.get("Cobrado", False)))
        retirado = e4.checkbox("Retirado", bool(pedido.get("Retirado", False)))
        pendiente = e5.checkbox("Pendiente", bool(pedido.get("Pendiente", False)))

        guardar = st.form_submit_button("💾 Guardar cambios", type="primary")

    # ---------- GUARDAR ----------
    if guardar:
        doc_id = pedido.get("id_documento_firestore")
        if not doc_id:
            st.error("❌ Pedido sin ID de Firestore.")
            return

        data_update = {
            "Cliente": convert_to_firestore_type(cliente),
            "Telefono": convert_to_firestore_type(limpiar_telefono(telefono)),
            "Club": convert_to_firestore_type(club),
            "Precio": precio,
            "Precio Factura": precio_factura,
            "Fecha salida": convert_to_firestore_type(fecha_salida),
            "Inicio Trabajo": empezado,
            "Trabajo Terminado": terminado,
            "Cobrado": cobrado,
            "Retirado": retirado,
            "Pendiente": pendiente,
            "Productos": json.dumps(productos)
        }

        if update_document_firestore("pedidos", doc_id, data_update):
            st.success("✅ Pedido actualizado correctamente")
            st.session_state.data_loaded = False
            st.session_state.pop("pedido_key", None)
            st.session_state.pedido_section = None
            time.sleep(1)
            st.rerun()
