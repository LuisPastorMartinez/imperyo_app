import streamlit as st
import pandas as pd
import time
from datetime import datetime

from utils.firestore_utils import (
    delete_document_firestore,
    update_document_firestore
)


def show_delete(df_pedidos, df_listas=None):

    # =================================================
    # HEADER + VOLVER
    # =================================================
    col1, col2 = st.columns([1, 6])

    with col1:
        if st.button("⬅️ Volver"):
            st.session_state.pop("pedido_section", None)
            st.rerun()

    with col2:
        st.subheader("🗑️ Eliminar Pedido")

    st.write("---")

    if df_pedidos is None or df_pedidos.empty:
        st.info("📭 No hay pedidos.")
        return

    # =================================================
    # NORMALIZAR
    # =================================================
    df_pedidos = df_pedidos.copy()

    df_pedidos["Año"] = pd.to_numeric(
        df_pedidos["Año"], errors="coerce"
    ).fillna(datetime.now().year).astype(int)

    df_pedidos["ID"] = pd.to_numeric(
        df_pedidos["ID"], errors="coerce"
    ).fillna(0).astype(int)

    # =================================================
    # SELECTORES
    # =================================================
    años = sorted(df_pedidos["Año"].unique(), reverse=True)
    año = st.selectbox("📅 Año del pedido", años)

    df_año = df_pedidos[df_pedidos["Año"] == año].sort_values("ID")
    if df_año.empty:
        st.info(f"📭 No hay pedidos en {año}.")
        return

    pedido_id = st.number_input(
        "🆔 ID del pedido",
        min_value=1,
        step=1
    )

    pedido_df = df_año[df_año["ID"] == pedido_id]
    if pedido_df.empty:
        st.warning("⚠️ No existe ese pedido.")
        return

    pedido = pedido_df.iloc[0]

    # =================================================
    # INFO
    # =================================================
    st.markdown("### 📄 Pedido seleccionado")

    st.dataframe(pd.DataFrame([{
        "ID": pedido_id,
        "Cliente": pedido.get("Cliente", ""),
        "Club": pedido.get("Club", ""),
        "Teléfono": pedido.get("Telefono", ""),
    }]), use_container_width=True, hide_index=True)

    st.warning(
        f"⚠️ Vas a eliminar el pedido **{pedido_id}/{año}** "
        f"del cliente **{pedido.get('Cliente', '')}**"
    )

    # =================================================
    # FORMULARIO DE CONFIRMACIÓN (CLAVE)
    # =================================================
    with st.form("form_delete"):
        confirmar = st.checkbox(
            "Confirmo que quiero eliminar este pedido definitivamente"
        )

        eliminar = st.form_submit_button(
            "🗑️ BORRAR DEFINITIVAMENTE",
            type="primary"
        )

    # =================================================
    # ELIMINAR
    # =================================================
    if eliminar:
        if not confirmar:
            st.error("❌ Debes confirmar antes de eliminar")
            return

        doc_id = pedido.get("id_documento_firestore")
        if not doc_id:
            st.error("❌ Pedido sin ID de Firestore")
            return

        delete_document_firestore("pedidos", doc_id)

        # RENUMERAR IDS
        restantes = df_año[df_año["ID"] != pedido_id].sort_values("ID")

        for new_id, (_, row) in enumerate(restantes.iterrows(), start=1):
            update_document_firestore(
                "pedidos",
                row["id_documento_firestore"],
                {"ID": new_id}
            )

        st.session_state.pop("data", None)
        st.session_state["data_loaded"] = False
        st.session_state.pop("pedido_section", None)

        st.balloons()
        st.success("✅ Pedido eliminado correctamente")
        time.sleep(1)
        st.rerun()
