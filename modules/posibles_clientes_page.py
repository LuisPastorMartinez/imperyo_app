import streamlit as st
import pandas as pd
from datetime import datetime

from utils.firestore_utils import (
    load_dataframes_firestore,
    update_document_firestore,
    delete_document_firestore,
    add_document_firestore,
)
from utils.helpers import convert_to_firestore_type
from utils.data_utils import limpiar_telefono


ESTADOS = [
    "Nuevo",
    "Contactado",
    "Pensándolo",
    "En negociación",
    "Perdido",
    "Cerrado",
]

INTERESES = [
    "Ciclismo",
    "Trail",
    "Ambos",
]


def show_posibles_clientes_page():
    st.header("📋 Posibles clientes")
    st.write("---")

    data = load_dataframes_firestore()
    df = data.get("df_posibles_clientes", pd.DataFrame())

    if df.empty:
        df = pd.DataFrame(columns=[
            "Nombre",
            "Telefono",
            "Club",
            "Interes",
            "Estado",
            "Notas",
            "Fecha_creacion",
            "Ultima_actualizacion",
            "id_documento_firestore",
        ])

    df = df.copy()

    # ============================
    # SELECCIÓN
    # ============================
    st.subheader("✏️ Crear / Editar posible cliente")

    opciones = ["➕ Nuevo cliente"]
    if not df.empty:
        opciones += [
            f"{row['Nombre']} ({row['Telefono']})"
            for _, row in df.iterrows()
        ]

    seleccion = st.selectbox("Seleccionar", opciones)
    editar = seleccion != "➕ Nuevo cliente"

    if editar:
        idx = opciones.index(seleccion) - 1
        cliente = df.iloc[idx]
    else:
        cliente = {}

    # ============================
    # FORMULARIO
    # ============================
    nombre = st.text_input("Nombre *", value=cliente.get("Nombre", ""))
    telefono = st.text_input("Teléfono *", value=cliente.get("Telefono", ""))
    club = st.text_input("Club", value=cliente.get("Club", ""))

    interes = st.selectbox(
        "Interés",
        INTERESES,
        index=INTERESES.index(cliente.get("Interes", "Ciclismo"))
        if cliente.get("Interes") in INTERESES else 0
    )

    estado = st.selectbox(
        "Estado",
        ESTADOS,
        index=ESTADOS.index(cliente.get("Estado", "Nuevo"))
        if cliente.get("Estado") in ESTADOS else 0
    )

    notas = st.text_area(
        "Notas / Seguimiento",
        value=cliente.get("Notas", ""),
        height=150
    )

    # ============================
    # GUARDAR
    # ============================
    if st.button("💾 Guardar", type="primary"):
        if not nombre or not telefono:
            st.error("❌ Nombre y teléfono son obligatorios")
            return

        telefono_limpio = limpiar_telefono(telefono)
        now = datetime.now()

        data_save = {
            "Nombre": nombre,
            "Telefono": telefono_limpio or telefono,
            "Club": club,
            "Interes": interes,
            "Estado": estado,
            "Notas": notas,
            "Ultima_actualizacion": now,
        }

        if editar:
            update_document_firestore(
                "posibles_clientes",
                cliente["id_documento_firestore"],
                {k: convert_to_firestore_type(v) for k, v in data_save.items()}
            )
            st.success("✅ Cliente actualizado")
        else:
            data_save["Fecha_creacion"] = now
            add_document_firestore(
                "posibles_clientes",
                {k: convert_to_firestore_type(v) for k, v in data_save.items()}
            )
            st.success("✅ Cliente creado")

        st.rerun()

    # ============================
    # CONVERTIR EN PEDIDO (PASO 2)
    # ============================
    st.write("---")
    st.subheader("➡️ Convertir en pedido")

    if not editar:
        st.info("Selecciona un posible cliente guardado para poder crear un pedido.")
    else:
        if st.button("📄 Crear pedido con este cliente", type="primary"):
            st.session_state["pedido_desde_cliente"] = {
                "Cliente": cliente.get("Nombre", ""),
                "Telefono": cliente.get("Telefono", ""),
                "Club": cliente.get("Club", ""),
            }
            st.session_state.current_page = "Pedidos"
            st.success("➡️ Datos enviados a creación de pedido")
            st.rerun()

    # ============================
    # LISTA
    # ============================
    st.write("---")
    st.subheader("📊 Lista de seguimiento")

    if df.empty:
        st.info("No hay posibles clientes todavía.")
        return

    df_show = df.copy()
    df_show["Última actualización"] = pd.to_datetime(
        df_show["Ultima_actualizacion"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    columnas = [
        "Nombre",
        "Telefono",
        "Club",
        "Interes",
        "Estado",
        "Última actualización",
    ]

    st.dataframe(
        df_show.sort_values("Ultima_actualizacion", ascending=False)[columnas],
        use_container_width=True,
        hide_index=True
    )

    # ============================
    # BORRAR
    # ============================
    st.write("---")
    st.subheader("🗑️ Borrar cliente")

    borrar = st.selectbox(
        "Selecciona cliente a borrar",
        ["—"] + opciones[1:]
    )

    if borrar != "—" and st.button("🗑️ Borrar definitivamente"):
        idx = opciones.index(borrar) - 1
        doc_id = df.iloc[idx]["id_documento_firestore"]
        delete_document_firestore("posibles_clientes", doc_id)
        st.success("🗑️ Cliente eliminado")
        st.rerun()
