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
# PARSE ROBUSTO DE PRODUCTOS (CLAVE DEL PROBLEMA)
# =====================================================
def parse_productos(value):
    """
    Convierte el campo Productos a una lista REAL de productos,
    aunque venga como JSON anidado, string, etc.
    """
    if not value:
        return []

    current = value

    for _ in range(3):  # máximo 3 niveles
        if isinstance(current, list):
            return current
        if isinstance(current, str):
            try:
                current = json.loads(current)
                continue
            except Exception:
                break
        break

    return []


# =====================================================
# PÁGINA MODIFICAR PEDIDO
# =====================================================
def show_modify(df_pedidos, df_listas):
    st.subheader("✏️ Modificar Pedido")
    st.write("---")

    if df_pedidos is None or df_pedidos.empty:
        st.info("📭 No hay pedidos.")
        return

    # ---------- AÑO ----------
    if "Año" not in df_pedidos.columns:
        df_pedidos["Año"] = datetime.now().year

    df_pedidos["Año"] = pd.to_numeric(
        df_pedidos["Año"], errors="coerce"
    ).fillna(datetime.now().year).astype(int)

    años = sorted(df_pedidos["Año"].unique(), reverse=True)
    año = st.selectbox("📅 Año del pedido", años, key="mod_year")

    df_año = df_pedidos[df_pedidos["Año"] == año]
    if df_año.empty:
        st.info("No hay pedidos ese año.")
        return

    pedido_id = st.number_input(
        "🆔 ID del pedido",
        min_value=1,
        step=1,
        key="mod_id"
    )

    pedido_df = df_año[df_año["ID"] == pedido_id]
    if pedido_df.empty:
        st.warning("No existe ese pedido.")
        return

    pedido = pedido_df.iloc[0]

    # =====================================================
    # PRODUCTOS — CARGA CORRECTA
    # =====================================================
    pedido_key = f"{año}_{pedido_id}"

    if (
        "productos_modificar" not in st.session_state
        or st.session_state.get("pedido_key") != pedido_key
    ):
        st.session_state.productos_modificar = parse_productos(
            pedido.get("Productos")
        )
        st.session_state.pedido_key = pedido_key

    if not st.session_state.productos_modificar:
        st.session_state.productos_modificar = [
            {"Producto": "", "Tela": "", "PrecioUnitario": 0.0, "Cantidad": 1}
        ]

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

    for i, p in enumerate(st.session_state.productos_modificar):
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

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("➕ Añadir producto", key=f"add_prod_{pedido_key}"):
            st.session_state.productos_modificar.append(
                {"Producto": "", "Tela": "", "PrecioUnitario": 0.0, "Cantidad": 1}
            )
            st.rerun()

    with col_b:
        if (
            len(st.session_state.productos_modificar) > 1
            and st.button("➖ Quitar último producto", key=f"del_prod_{pedido_key}")
        ):
            st.session_state.productos_modificar.pop()
            st.rerun()

    st.write("---")

    # =====================================================
    # FORMULARIO DATOS GENERALES
    # =====================================================
    with st.form("form_modificar_pedido"):
        col1, col2 = st.columns(2)

        with col1:
            cliente = st.text_input("Cliente*", value=pedido.get("Cliente", ""))
            telefono = st.text_input("Teléfono*", value=pedido.get("Telefono", ""))
            club = st.text_input("Club*", value=pedido.get("Club", ""))
            descripcion = st.text_area(
                "Descripción", value=pedido.get("Breve Descripción", "")
            )

        with col2:
            fecha_entrada = st.date_input(
                "Fecha entrada", safe_to_date(pedido.get("Fecha entrada"))
            )
            fecha_salida = st.date_input(
                "Fecha salida", safe_to_date(pedido.get("Fecha Salida"))
            )
            precio = st.number_input(
                "Precio total (€)", min_value=0.0, value=float(pedido.get("Precio", 0.0))
            )
            precio_factura = st.number_input(
                "Precio factura (€)",
                min_value=0.0,
                value=float(pedido.get("Precio Factura", 0.0)),
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
    # GUARDAR EN FIRESTORE
    # =====================================================
    if guardar:
        telefono_limpio = limpiar_telefono(telefono)
        if not cliente or not telefono_limpio or not club:
            st.error("Campos obligatorios incorrectos.")
            return

        doc_id = pedido.get("id_documento_firestore")
        if not doc_id:
            st.error("Pedido sin ID de Firestore.")
            return

        productos_limpios = [
            {
                "Producto": p.get("Producto", ""),
                "Tela": p.get("Tela", ""),
                "PrecioUnitario": float(p.get("PrecioUnitario", 0.0)),
                "Cantidad": int(p.get("Cantidad", 1)),
            }
            for p in st.session_state.productos_modificar
            if p.get("Producto") or p.get("Tela")
        ]

        data_update = {
            "ID": int(pedido_id),
            "Año": int(año),
            "Productos": json.dumps(productos_limpios),
            "Cliente": convert_to_firestore_type(cliente),
            "Telefono": convert_to_firestore_type(telefono_limpio),
            "Club": convert_to_firestore_type(club),
            "Breve Descripción": convert_to_firestore_type(descripcion),
            "Fecha entrada": convert_to_firestore_type(fecha_entrada),
            "Fecha Salida": convert_to_firestore_type(fecha_salida),
            "Precio": convert_to_firestore_type(precio),
            "Precio Factura": convert_to_firestore_type(precio_factura),
            "Inicio Trabajo": convert_to_firestore_type(empezado),
            "Trabajo Terminado": convert_to_firestore_type(terminado),
            "Cobrado": convert_to_firestore_type(cobrado),
            "Retirado": convert_to_firestore_type(retirado),
            "Pendiente": convert_to_firestore_type(pendiente),
        }

        if not update_document_firestore("pedidos", doc_id, data_update):
            st.error("❌ Error al actualizar el pedido.")
            return

        # limpiar estado
        st.session_state.pop("productos_modificar", None)
        st.session_state.pop("pedido_key", None)
        st.session_state.data["df_pedidos"] = None

        st.success(f"✅ Pedido {pedido_id} / {año} actualizado correctamente")
        st.balloons()
        time.sleep(1)
        st.rerun()
