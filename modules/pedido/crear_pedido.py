import streamlit as st
import json
import time
from datetime import datetime

from utils.firestore_utils import add_document_firestore, get_next_id_por_año
from utils.data_utils import limpiar_telefono
from .helpers import convert_to_firestore_type


def show_create(df_pedidos, df_listas):

    # =================================================
    # BOTÓN SALIR SIN GUARDAR
    # =================================================
    col1, col2 = st.columns([1, 6])

    with col1:
        if st.button("⬅️ Salir sin guardar"):
            st.session_state.pop("pedido_section", None)
            st.session_state.pop("productos_crear", None)
            st.rerun()

    with col2:
        st.subheader("➕ Crear Pedido")

    st.write("---")

    if df_pedidos is None:
        st.error("No hay datos de pedidos.")
        return

    # ===============================
    # FECHA ENTRADA (AUTOMÁTICA)
    # ===============================
    fecha_entrada = datetime.now().date()
    año_actual = fecha_entrada.year

    st.info(f"📅 Fecha de entrada: **{fecha_entrada.strftime('%d/%m/%Y')}**")
    st.info(f"📅 Año del pedido: **{año_actual}**")

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

        notas = st.text_area(
            "📝 Notas / Observaciones",
            placeholder="Ej: Llamar en 15 días, colores pendientes, espera confirmación del club..."
        )

        st.markdown("### 🚦 Estado del pedido")
        e1, e2, e3, e4, e5 = st.columns(5)
        empezado = e1.checkbox("Empezado")
        terminado = e2.checkbox("Terminado")
        cobrado = e3.checkbox("Cobrado")
        retirado = e4.checkbox("Retirado")
        pendiente = e5.checkbox("Pendiente")

        crear = st.form_submit_button("✅ Crear Pedido", type="primary")

    # ===============================
    # GUARDAR
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
            "Fecha entrada": convert_to_firestore_type(fecha_entrada),
            "Cliente": convert_to_firestore_type(cliente),
            "Telefono": convert_to_firestore_type(telefono_limpio),
            "Club": convert_to_firestore_type(club),
            "Precio": precio,
            "Precio Factura": precio_factura,
            "Notas": convert_to_firestore_type(notas),
            "Inicio Trabajo": empezado,
            "Trabajo Terminado": terminado,
            "Cobrado": cobrado,
            "Retirado": retirado,
            "Pendiente": pendiente,
        }

        add_document_firestore("pedidos", nuevo_pedido)

        st.success(f"✅ Pedido {next_id}/{año_actual} creado correctamente")

        st.session_state.data_loaded = False
        st.session_state.pop("pedido_section", None)
        time.sleep(1)
        st.rerun()
