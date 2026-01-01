import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime, date

from utils.firestore_utils import save_dataframe_firestore
from utils.data_utils import limpiar_telefono
from .helpers import convert_to_firestore_type


def get_next_id_por_año(df_pedidos, año):
    """
    Devuelve el siguiente ID disponible SOLO para el año indicado.
    """
    if df_pedidos is None or df_pedidos.empty:
        return 1

    df_year = df_pedidos[df_pedidos["Año"] == año]

    if df_year.empty:
        return 1

    ids = pd.to_numeric(df_year["ID"], errors="coerce").dropna()

    if ids.empty:
        return 1

    return int(ids.max()) + 1


def show_create(df_pedidos, df_listas):
    st.subheader("➕ Crear Pedido")

    # ---------- ASEGURAR DATAFRAME ----------
    if df_pedidos is None:
        st.error("❌ No hay datos de pedidos.")
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
        key="create_año_selector"
    )

    # ---------- CALCULAR ID ----------
    next_id = get_next_id_por_año(df_pedidos, año_seleccionado)

    st.markdown(
        f"### 🆔 ID del pedido: **{next_id}**  \n"
        f"📆 Año: **{año_seleccionado}**"
    )

    st.write("---")

    # ---------- PRODUCTOS ----------
    st.markdown("### 🧵 Productos")

    if "productos_crear" not in st.session_state:
        st.session_state.productos_crear = [
            {"Producto": "", "Tela": "", "PrecioUnitario": 0.0, "Cantidad": 1}
        ]

    productos_lista = [""] + (
        df_listas["Producto"].dropna().unique().tolist()
        if "Producto" in df_listas.columns else []
    )
    telas_lista = [""] + (
        df_listas["Tela"].dropna().unique().tolist()
        if "Tela" in df_listas.columns else []
    )

    total_productos = 0.0

    for i, p in enumerate(st.session_state.productos_crear):
        cols = st.columns([3, 3, 2, 2])

        with cols[0]:
            p["Producto"] = st.selectbox(
                f"Producto {i+1}",
                productos_lista,
                index=productos_lista.index(p.get("Producto", ""))
                if p.get("Producto", "") in productos_lista else 0,
                key=f"create_producto_{i}"
            )

        with cols[1]:
            p["Tela"] = st.selectbox(
                f"Tela {i+1}",
                telas_lista,
                index=telas_lista.index(p.get("Tela", ""))
                if p.get("Tela", "") in telas_lista else 0,
                key=f"create_tela_{i}"
            )

        with cols[2]:
            p["PrecioUnitario"] = st.number_input(
                "Precio €",
                min_value=0.0,
                value=float(p.get("PrecioUnitario", 0.0)),
                key=f"create_precio_{i}"
            )

        with cols[3]:
            p["Cantidad"] = st.number_input(
                "Cantidad",
                min_value=1,
                value=int(p.get("Cantidad", 1)),
                key=f"create_cantidad_{i}"
            )

        total_productos += p["PrecioUnitario"] * p["Cantidad"]

    st.markdown(f"**💰 Subtotal productos:** {total_productos:.2f} €")

    col_add, col_remove = st.columns(2)

    with col_add:
        if st.button("➕ Añadir producto"):
            st.session_state.productos_crear.append(
                {"Producto": "", "Tela": "", "PrecioUnitario": 0.0, "Cantidad": 1}
            )
            st.rerun()

    with col_remove:
        if len(st.session_state.productos_crear) > 1:
            if st.button("➖ Quitar último producto"):
                st.session_state.productos_crear.pop()
                st.rerun()

    st.write("---")

    # ---------- FORMULARIO ----------
    with st.form("crear_pedido_form"):
        col1, col2 = st.columns(2)

        with col1:
            cliente = st.text_input("Cliente*", "")
            telefono = st.text_input("Teléfono*", "")
            club = st.text_input("Club*", "")
            descripcion = st.text_area("Descripción")

        with col2:
            fecha_entrada = st.date_input("Fecha entrada", datetime.now().date())
            precio = st.number_input("Precio total (€)", min_value=0.0, value=0.0)
            precio_factura = st.number_input("Precio factura (€)", min_value=0.0, value=0.0)

        crear = st.form_submit_button("✅ Crear Pedido", type="primary")

    # ---------- CREAR PEDIDO ----------
    if crear:
        if not cliente or not telefono or not club:
            st.error("❌ Cliente, Teléfono y Club son obligatorios.")
            return

        telefono_limpio = limpiar_telefono(telefono)
        if not telefono_limpio:
            st.error("❌ Teléfono inválido.")
            return

        nuevo_pedido = {
            "ID": next_id,
            "Año": año_seleccionado,
            "Productos": json.dumps(st.session_state.productos_crear),
            "Cliente": convert_to_firestore_type(cliente),
            "Telefono": convert_to_firestore_type(telefono_limpio),
            "Club": convert_to_firestore_type(club),
            "Breve Descripción": convert_to_firestore_type(descripcion),
            "Fecha entrada": convert_to_firestore_type(fecha_entrada),
            "Fecha Salida": None,
            "Precio": convert_to_firestore_type(precio),
            "Precio Factura": convert_to_firestore_type(precio_factura),
            "Inicio Trabajo": False,
            "Trabajo Terminado": False,
            "Cobrado": False,
            "Retirado": False,
            "Pendiente": False
        }

        df_pedidos = pd.concat(
            [df_pedidos, pd.DataFrame([nuevo_pedido])],
            ignore_index=True
        )

        if not save_dataframe_firestore(df_pedidos, "pedidos"):
            st.error("❌ Error al guardar el pedido.")
            return

        st.success(f"✅ Pedido {next_id} del año {año_seleccionado} creado correctamente")
        st.balloons()
        time.sleep(1)

        # Limpiar estado
        if "productos_crear" in st.session_state:
            del st.session_state.productos_crear

        st.session_state.data["df_pedidos"] = df_pedidos
        st.rerun()
