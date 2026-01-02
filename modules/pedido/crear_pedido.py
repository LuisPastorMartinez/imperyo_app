import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime

from utils.firestore_utils import save_dataframe_firestore, get_next_id_por_año
from utils.data_utils import limpiar_telefono
from .helpers import convert_to_firestore_type


def show_create(df_pedidos, df_listas):
    st.subheader("➕ Crear Pedido")
    st.write("---")

    if df_pedidos is None:
        st.error("No hay datos de pedidos.")
        return

    # -------- ASEGURAR COLUMNA AÑO --------
    if "Año" not in df_pedidos.columns:
        df_pedidos["Año"] = datetime.now().year

    df_pedidos["Año"] = (
        pd.to_numeric(df_pedidos["Año"], errors="coerce")
        .fillna(datetime.now().year)
        .astype("int64")
    )

    # -------- AÑO ACTUAL --------
    año_actual = datetime.now().year
    st.info(f"📅 Año del pedido: {año_actual}")

    # ==========================================================
    # 📋 COPIAR DATOS DE OTRO PEDIDO
    # ==========================================================
    with st.expander("📋 Copiar datos de un pedido anterior (opcional)"):
        col_c1, col_c2 = st.columns(2)

        with col_c1:
            copiar_año = st.number_input(
                "Año del pedido",
                min_value=2000,
                value=año_actual,
                step=1,
                key="copiar_año"
            )

        with col_c2:
            copiar_id = st.number_input(
                "ID del pedido",
                min_value=1,
                step=1,
                key="copiar_id"
            )

        if st.button("📥 Copiar datos", use_container_width=True):
            pedido_origen = df_pedidos[
                (df_pedidos["Año"] == copiar_año) &
                (df_pedidos["ID"] == copiar_id)
            ]

            if pedido_origen.empty:
                st.error("❌ No se encontró ese pedido.")
            else:
                pedido_origen = pedido_origen.iloc[0]

                st.session_state["crear_cliente"] = pedido_origen.get("Cliente", "")
                st.session_state["crear_telefono"] = pedido_origen.get("Telefono", "")
                st.session_state["crear_club"] = pedido_origen.get("Club", "")
                st.session_state["crear_descripcion"] = pedido_origen.get(
                    "Breve Descripción", ""
                )

                st.success("✅ Datos copiados. Revisa y crea el pedido.")

    # -------- PRODUCTOS --------
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
        cols = st.columns([3, 3, 2, 2])

        with cols[0]:
            p["Producto"] = st.selectbox(
                f"Producto {i+1}",
                productos_lista,
                index=productos_lista.index(p["Producto"])
                if p["Producto"] in productos_lista else 0,
                key=f"create_producto_{i}"
            )

        with cols[1]:
            p["Tela"] = st.selectbox(
                f"Tela {i+1}",
                telas_lista,
                index=telas_lista.index(p["Tela"])
                if p["Tela"] in telas_lista else 0,
                key=f"create_tela_{i}"
            )

        with cols[2]:
            p["PrecioUnitario"] = st.number_input(
                "Precio €",
                min_value=0.0,
                value=float(p["PrecioUnitario"]),
                key=f"create_precio_{i}"
            )

        with cols[3]:
            p["Cantidad"] = st.number_input(
                "Cantidad",
                min_value=1,
                value=int(p["Cantidad"]),
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

    # -------- ID (INICIAL) --------
    df_año = df_pedidos[df_pedidos["Año"] == año_actual].copy()
    next_id = get_next_id_por_año(df_año, año_actual)

    st.markdown(f"### 🆔 ID del pedido: **{next_id}**")

    # -------- FORMULARIO --------
    with st.form("crear_pedido_form"):
        col1, col2 = st.columns(2)

        with col1:
            cliente = st.text_input(
                "Cliente*",
                value=st.session_state.get("crear_cliente", "")
            )
            telefono = st.text_input(
                "Teléfono*",
                value=st.session_state.get("crear_telefono", "")
            )
            club = st.text_input(
                "Club*",
                value=st.session_state.get("crear_club", "")
            )
            descripcion = st.text_area(
                "Descripción",
                value=st.session_state.get("crear_descripcion", "")
            )

        with col2:
            fecha_entrada = st.date_input("Fecha entrada", datetime.now().date())
            precio = st.number_input("Precio total (€)", min_value=0.0)
            precio_factura = st.number_input("Precio factura (€)", min_value=0.0)

        crear = st.form_submit_button("✅ Crear Pedido", type="primary")

    # -------- CREAR PEDIDO --------
    if crear:
        if not cliente or not telefono or not club:
            st.error("Cliente, Teléfono y Club son obligatorios.")
            return

        telefono_limpio = limpiar_telefono(telefono)
        if not telefono_limpio:
            st.error("Teléfono inválido.")
            return

        # 🔒 PARCHE DEFINITIVO CONTRA IDs DUPLICADOS
        df_actual = st.session_state.data.get("df_pedidos", df_pedidos)
        df_actual_año = df_actual[df_actual["Año"] == año_actual]

        ids_existentes = (
            pd.to_numeric(df_actual_año["ID"], errors="coerce")
            .dropna()
            .astype(int)
            .tolist()
        )

        while next_id in ids_existentes:
            next_id += 1

        nuevo_pedido = {
            "ID": next_id,
            "Año": año_actual,
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
            "Pendiente": False,
            "id_documento_firestore": None
        }

        df_pedidos = pd.concat(
            [df_pedidos, pd.DataFrame([nuevo_pedido])],
            ignore_index=True
        )

        if save_dataframe_firestore(df_pedidos, "pedidos"):
            st.success(f"✅ Pedido {next_id} / {año_actual} creado correctamente")
            st.balloons()
            time.sleep(1)

            # Limpiar estados temporales
            for k in [
                "productos_crear",
                "crear_cliente",
                "crear_telefono",
                "crear_club",
                "crear_descripcion"
            ]:
                st.session_state.pop(k, None)

            st.session_state.data["df_pedidos"] = df_pedidos
            st.rerun()
        else:
            st.error("❌ Error al guardar el pedido")
