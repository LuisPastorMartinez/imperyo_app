import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime

from utils.firestore_utils import add_document_firestore, get_next_id_por_año
from utils.data_utils import limpiar_telefono
from .helpers import convert_to_firestore_type


def show_create(df_pedidos, df_listas):
    st.subheader("➕ Crear Pedido")
    st.write("---")

    if df_pedidos is None:
        st.error("No hay datos de pedidos.")
        return

    año_actual = datetime.now().year
    st.info(f"📅 Año del pedido: {año_actual}")

    # ===============================
    # PRODUCTOS
    # ===============================
    if "productos_crear" not in st.session_state:
        st.session_state.productos_crear = [
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

    total_productos = 0.0

    for i, p in enumerate(st.session_state.productos_crear):
        c1, c2, c3, c4 = st.columns([3, 3, 2, 2])

        p["Producto"] = c1.selectbox(
            f"Producto {i+1}",
            productos_lista,
            index=productos_lista.index(p["Producto"])
            if p["Producto"] in productos_lista else 0,
            key=f"create_producto_{i}"
        )

        p["Tela"] = c2.selectbox(
            f"Tela {i+1}",
            telas_lista,
            index=telas_lista.index(p["Tela"])
            if p["Tela"] in telas_lista else 0,
            key=f"create_tela_{i}"
        )

        p["PrecioUnitario"] = c3.number_input(
            "Precio €",
            min_value=0.0,
            value=float(p["PrecioUnitario"]),
            key=f"create_precio_{i}"
        )

        p["Cantidad"] = c4.number_input(
            "Cantidad",
            min_value=1,
            value=int(p["Cantidad"]),
            key=f"create_cantidad_{i}"
        )

        total_productos += p["PrecioUnitario"] * p["Cantidad"]

    st.markdown(f"**💰 Subtotal productos:** {total_productos:.2f} €")

    # ===============================
    # ID
    # ===============================
    df_año = df_pedidos[df_pedidos["Año"] == año_actual].copy()
    next_id = get_next_id_por_año(df_año, año_actual)

    st.markdown(f"### 🆔 ID del pedido: **{next_id}**")

    # ===============================
    # FORMULARIO
    # ===============================
    with st.form("crear_pedido_form"):
        col1, col2 = st.columns(2)

        with col1:
            cliente = st.text_input("Cliente*")
            telefono = st.text_input("Teléfono*")
            club = st.text_input("Club*")

        with col2:
            precio = st.number_input("Precio total (€)", min_value=0.0)
            precio_factura = st.number_input("Precio factura (€)", min_value=0.0)

        e1, e2, e3, e4, e5 = st.columns(5)
        empezado = e1.checkbox("Empezado")
        terminado = e2.checkbox("Terminado")
        cobrado = e3.checkbox("Cobrado")
        retirado = e4.checkbox("Retirado")
        pendiente = e5.checkbox("Pendiente")

        crear = st.form_submit_button("✅ Crear Pedido", type="primary")

    # ===============================
    # GUARDAR (CORRECTO)
    # ===============================
    if crear:
        if not cliente or not telefono or not club:
            st.error("❌ Cliente, Teléfono y Club obligatorios")
            return

        telefono_limpio = limpiar_telefono(telefono)
        if not telefono_limpio:
            st.error("❌ Teléfono inválido")
            return

        nuevo_pedido = {
            "ID": next_id,
            "Año": año_actual,
            "Productos": json.dumps(st.session_state.productos_crear),
            "Cliente": convert_to_firestore_type(cliente),
            "Telefono": convert_to_firestore_type(telefono_limpio),
            "Club": convert_to_firestore_type(club),
            "Precio": precio,
            "Precio Factura": precio_factura,
            "Inicio Trabajo": empezado,
            "Trabajo Terminado": terminado,
            "Cobrado": cobrado,
            "Retirado": retirado,
            "Pendiente": pendiente,
        }

        add_document_firestore("pedidos", nuevo_pedido)

        st.success(f"✅ Pedido {next_id} / {año_actual} creado correctamente")
        time.sleep(1)
        st.session_state.pop("productos_crear", None)
        st.session_state.data_loaded = False
        st.rerun()
