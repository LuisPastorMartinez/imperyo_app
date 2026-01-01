import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime, date
from utils.firestore_utils import save_dataframe_firestore
from utils.data_utils import limpiar_telefono
from .helpers import convert_to_firestore_type, safe_select_index


def safe_to_date(value):
    """Convierte un valor a date de forma segura."""
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except Exception:
            return datetime.now().date()
    if isinstance(value, datetime):
        return value.date()
    return datetime.now().date()


def show_modify(df_pedidos, df_listas):
    st.subheader("✏️ Modificar Pedido")

    if df_pedidos is None or df_pedidos.empty:
        st.info("📭 No hay pedidos registrados.")
        return

    # ---------- ASEGURAR COLUMNA AÑO ----------
    if "Año" not in df_pedidos.columns:
        df_pedidos["Año"] = datetime.now().year

    df_pedidos["Año"] = pd.to_numeric(
        df_pedidos["Año"], errors="coerce"
    ).fillna(datetime.now().year).astype("int64")

    # ---------- SELECTOR DE AÑO ----------
    año_actual = datetime.now().year

    años_disponibles = sorted(
        df_pedidos["Año"].dropna().unique(),
        reverse=True
    )

    if año_actual not in años_disponibles:
        años_disponibles.insert(0, año_actual)

    año_seleccionado = st.selectbox(
        "📅 Año del pedido",
        años_disponibles,
        key="modify_año_selector"
    )

    # ---------- FILTRAR POR AÑO ----------
    df_year = df_pedidos[df_pedidos["Año"] == año_seleccionado].copy()

    if df_year.empty:
        st.info(f"📭 No hay pedidos en {año_seleccionado}")
        return

    # ---------- SELECCIÓN DE ID ----------
    mod_id = st.number_input(
        "ID del pedido",
        min_value=1,
        step=1,
        key="modify_id_input"
    )

    pedido_df = df_year[df_year["ID"] == mod_id]

    if pedido_df.empty:
        st.warning("⚠️ No existe un pedido con ese ID en este año.")
        return

    pedido = pedido_df.iloc[0]

    # ---------- PRODUCTOS ----------
    try:
        productos = (
            json.loads(pedido["Productos"])
            if isinstance(pedido.get("Productos"), str) and pedido["Productos"].strip()
            else pedido.get("Productos", [])
        )
    except Exception:
        productos = []

    if not productos:
        productos = [{"Producto": "", "Tela": "", "PrecioUnitario": 0.0, "Cantidad": 1}]

    st.markdown("### 🧵 Productos del pedido")

    productos_lista = [""] + (
        df_listas["Producto"].dropna().unique().tolist()
        if "Producto" in df_listas.columns else []
    )
    telas_lista = [""] + (
        df_listas["Tela"].dropna().unique().tolist()
        if "Tela" in df_listas.columns else []
    )

    total_productos = 0.0

    for i, p in enumerate(productos):
        cols = st.columns([3, 3, 2, 2])
        with cols[0]:
            p["Producto"] = st.selectbox(
                f"Producto {i+1}",
                productos_lista,
                index=safe_select_index(productos_lista, p.get("Producto", "")),
                key=f"mod_producto_{i}"
            )
        with cols[1]:
            p["Tela"] = st.selectbox(
                f"Tela {i+1}",
                telas_lista,
                index=safe_select_index(telas_lista, p.get("Tela", "")),
                key=f"mod_tela_{i}"
            )
        with cols[2]:
            p["PrecioUnitario"] = st.number_input(
                "Precio €",
                min_value=0.0,
                value=float(p.get("PrecioUnitario", 0.0)),
                key=f"mod_precio_{i}"
            )
        with cols[3]:
            p["Cantidad"] = st.number_input(
                "Cantidad",
                min_value=1,
                value=int(p.get("Cantidad", 1)),
                key=f"mod_cantidad_{i}"
            )

        total_productos += p["PrecioUnitario"] * p["Cantidad"]

    st.markdown(f"**💰 Subtotal productos:** {total_productos:.2f} €")
    st.write("---")

    # ---------- FORMULARIO ----------
    with st.form("modificar_pedido_form"):
        col1, col2 = st.columns(2)

        with col1:
            cliente = st.text_input("Cliente*", value=pedido.get("Cliente", ""))
            telefono = st.text_input("Teléfono*", value=pedido.get("Telefono", ""))
            club = st.text_input("Club*", value=pedido.get("Club", ""))
            descripcion = st.text_area("Descripción", value=pedido.get("Breve Descripción", ""))

        with col2:
            fecha_entrada = st.date_input(
                "Fecha entrada",
                value=safe_to_date(pedido.get("Fecha entrada"))
            )
            fecha_salida = st.date_input(
                "Fecha salida",
                value=safe_to_date(pedido.get("Fecha Salida"))
                if pedido.get("Fecha Salida") else datetime.now().date()
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

        st.write("**Estado del pedido**")
        col_a, col_b, col_c, col_d, col_e = st.columns(5)

        with col_a:
            empezado = st.checkbox("Empezado", value=bool(pedido.get("Inicio Trabajo", False)))
        with col_b:
            terminado = st.checkbox("Terminado", value=bool(pedido.get("Trabajo Terminado", False)))
        with col_c:
            cobrado = st.checkbox("Cobrado", value=bool(pedido.get("Cobrado", False)))
        with col_d:
            retirado = st.checkbox("Retirado", value=bool(pedido.get("Retirado", False)))
        with col_e:
            pendiente = st.checkbox("Pendiente", value=bool(pedido.get("Pendiente", False)))

        guardar = st.form_submit_button("💾 Guardar cambios", type="primary")

    # ---------- GUARDAR CAMBIOS ----------
    if guardar:
        if not cliente or not telefono or not club:
            st.error("❌ Cliente, Teléfono y Club son obligatorios.")
            return

        telefono_limpio = limpiar_telefono(telefono)
        if not telefono_limpio:
            st.error("❌ Teléfono inválido.")
            return

        updated_pedido = {
            "ID": mod_id,
            "Año": año_seleccionado,
            "Productos": json.dumps(productos),
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
            "id_documento_firestore": pedido["id_documento_firestore"]
        }

        idx = df_pedidos.index[
            (df_pedidos["Año"] == año_seleccionado) &
            (df_pedidos["ID"] == mod_id)
        ].tolist()

        if not idx:
            st.error("❌ No se encontró el pedido para actualizar.")
            return

        df_pedidos.loc[idx[0]] = updated_pedido

        if not save_dataframe_firestore(df_pedidos, "pedidos"):
            st.error("❌ Error al guardar cambios.")
            return

        st.success(f"✅ Pedido {mod_id} del año {año_seleccionado} actualizado correctamente")
        st.balloons()
        time.sleep(1)

        st.session_state.data["df_pedidos"] = df_pedidos
        st.rerun()
