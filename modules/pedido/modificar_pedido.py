import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime, date

from utils.firestore_utils import update_document_firestore
from utils.data_utils import limpiar_telefono
from .helpers import convert_to_firestore_type, safe_select_index


# =====================================================
# FECHAS SEGURAS
# =====================================================
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


# =====================================================
# PARSE PRODUCTOS
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


# =====================================================
# MODIFICAR PEDIDO
# =====================================================
def show_modify(df_pedidos, df_listas):
    st.subheader("✏️ Modificar Pedido")
    st.write("---")

    if df_pedidos is None or df_pedidos.empty:
        st.info("📭 No hay pedidos.")
        return

    # ---------- AÑO ----------
    df_pedidos["Año"] = pd.to_numeric(
        df_pedidos["Año"], errors="coerce"
    ).fillna(datetime.now().year).astype(int)

    años = sorted(df_pedidos["Año"].unique(), reverse=True)
    año = st.selectbox("📅 Año del pedido", años, key="mod_year")

    df_año = df_pedidos[df_pedidos["Año"] == año]
    if df_año.empty:
        st.info("📭 No hay pedidos ese año.")
        return

    # ---------- ID POR DEFECTO = MÁS ALTO ----------
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

    # =====================================================
    # PRODUCTOS (CARGA SEGURA)
    # =====================================================
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
    st.write("---")

    # =====================================================
    # FORMULARIO DATOS GENERALES (⬅️ AQUÍ ESTABA LO QUE FALTABA)
    # =====================================================
    with st.form("form_modificar_pedido"):
        col1, col2 = st.columns(2)

        with col1:
            cliente = st.text_input("Cliente*", value=pedido.get("Cliente", ""))
            telefono = st.text_input("Teléfono*", value=pedido.get("Telefono", ""))
            club = st.text_input("Club*", value=pedido.get("Club", ""))
            descripcion = st.text_area(
                "Descripción",
                value=pedido.get("Breve Descripción", "")
            )

        with col2:
            fecha_entrada = st.date_input(
                "Fecha entrada",
                safe_to_date(pedido.get("Fecha entrada"))
            )
            fecha_salida = st.date_input(
                "Fecha salida",
                safe_to_date(pedido.get("Fecha Salida"))
            )
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

        st.write("Estado del pedido")
        c1, c2, c3, c4, c5 = st.columns(5)
        empezado = c1.checkbox("Empezado", bool(pedido.get("Inicio Trabajo", False)))
        terminado = c2.checkbox("Terminado", bool(pedido.get("Trabajo Terminado", False)))
        cobrado = c3.checkbox("Cobrado", bool(pedido.get("Cobrado", False)))
        retirado = c4.checkbox("Retirado", bool(pedido.get("Retirado", False)))
        pendiente = c5.checkbox("Pendiente", bool(pedido.get("Pendiente", False)))

        guardar = st.form_submit_button("💾 Guardar cambios", type="primary")

    # =====================================================
    # GUARDAR
    # =====================================================
    if guardar:
        telefono_limpio = limpiar_telefono(telefono)
        if not cliente or not telefono_limpio or not club:
            st.error("❌ Cliente, teléfono y club son obligatorios.")
            return

        doc_id = pedido.get("id_documento_firestore")
        if not doc_id:
            st.error("❌ Pedido sin ID de Firestore.")
            return

        productos_limpios = [
            {
                "Producto": p["Producto"],
                "Tela": p["Tela"],
                "PrecioUnitario": float(p["PrecioUnitario"]),
                "Cantidad": int(p["Cantidad"]),
            }
            for p in productos
            if p["Producto"] or p["Tela"]
        ]

        data_update = {
            "Productos": json.dumps(productos_limpios),
            "Cliente": convert_to_firestore_type(cliente),
            "Telefono": convert_to_firestore_type(telefono_limpio),
            "Club": convert_to_firestore_type(club),
            "Breve Descripción": convert_to_firestore_type(descripcion),
            "Fecha entrada": convert_to_firestore_type(fecha_entrada),
            "Fecha Salida": convert_to_firestore_type(fecha_salida),
            "Precio": convert_to_firestore_type(precio),
            "Precio Factura": convert_to_firestore_type(precio_factura),
            "Inicio Trabajo": empezado,
            "Trabajo Terminado": terminado,
            "Cobrado": cobrado,
            "Retirado": retirado,
            "Pendiente": pendiente,
        }

        if not update_document_firestore("pedidos", doc_id, data_update):
            st.error("❌ Error al actualizar el pedido.")
            return

        # 🔄 RECARGAR DATOS
        st.session_state.pop("data", None)
        st.session_state["data_loaded"] = False
        st.session_state.pop("productos_modificar", None)
        st.session_state.pop("pedido_key", None)

        st.success(f"✅ Pedido {pedido_id} / {año} actualizado correctamente")
        time.sleep(1)
        st.rerun()
