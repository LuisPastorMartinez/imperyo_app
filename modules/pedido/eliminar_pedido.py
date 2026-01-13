import streamlit as st
import pandas as pd
import time
from datetime import datetime

from utils.firestore_utils import (
    delete_document_firestore,
    update_document_firestore
)


def show_delete(df_pedidos, df_listas=None):
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
    año = st.selectbox("📅 Año del pedido", años, key="delete_year")

    df_año = df_pedidos[df_pedidos["Año"] == año].sort_values("ID")
    if df_año.empty:
        st.info(f"📭 No hay pedidos en {año}.")
        return

    max_id = int(df_año["ID"].max())

    if "delete_id" not in st.session_state:
        st.session_state.delete_id = max_id

    pedido_id = st.number_input(
        "🆔 ID del pedido",
        min_value=1,
        step=1,
        key="delete_id"
    )

    pedido_df = df_año[df_año["ID"] == pedido_id]
    if pedido_df.empty:
        st.warning("⚠️ No existe ese pedido.")
        return

    pedido = pedido_df.iloc[0]

    # =================================================
    # INFO DEL PEDIDO (TABLA)
    # =================================================
    st.markdown("### 📄 Pedido seleccionado")

    info_df = pd.DataFrame([{
        "ID": pedido_id,
        "Cliente": pedido.get("Cliente", ""),
        "Club": pedido.get("Club", ""),
        "Teléfono": pedido.get("Telefono", ""),
    }])

    st.dataframe(info_df, use_container_width=True, hide_index=True)

    # =================================================
    # CONFIRMACIÓN
    # =================================================
    st.warning(
        f"⚠️ ¿Quiere usted borrar el pedido "
        f"**ID {pedido_id}** del cliente "
        f"**{pedido.get('Cliente', '')}** "
        f"({pedido.get('Club', '')})?"
    )

    confirmar = st.checkbox(
        "Sí, confirmo que quiero eliminar este pedido definitivamente"
    )

    # =================================================
    # ELIMINAR + RENUMERAR
    # =================================================
    if confirmar and st.button("🗑️ BORRAR DEFINITIVAMENTE", type="primary"):
        doc_id = pedido.get("id_documento_firestore")
        if not doc_id:
            st.error("❌ Pedido sin ID de Firestore.")
            return

        # 1️⃣ BORRAR
        if not delete_document_firestore("pedidos", doc_id):
            st.error("❌ Error eliminando el pedido.")
            return

        # 2️⃣ RENUMERAR IDS DEL AÑO
        restantes = df_año[df_año["ID"] != pedido_id].sort_values("ID")

        for new_id, (_, row) in enumerate(restantes.iterrows(), start=1):
            if row["ID"] != new_id:
                update_document_firestore(
                    "pedidos",
                    row["id_documento_firestore"],
                    {"ID": new_id}
                )

        # 3️⃣ RECARGA
        st.session_state.pop("data", None)
        st.session_state["data_loaded"] = False

        st.balloons()
        st.success("✅ Pedido eliminado y IDs reordenados correctamente")
        st.session_state.pop("pedido_section", None)
        time.sleep(1.2)
        st.rerun()
