import streamlit as st
import pandas as pd
import time
from datetime import datetime

from utils.firestore_utils import delete_document_firestore, save_dataframe_firestore


def show_delete(df_pedidos, df_listas=None):
    st.subheader("🗑️ Eliminar Pedido")
    st.write("---")

    if df_pedidos is None or df_pedidos.empty:
        st.info("📭 No hay pedidos.")
        return

    df_pedidos["Año"] = pd.to_numeric(
        df_pedidos["Año"], errors="coerce"
    ).fillna(datetime.now().year).astype(int)

    df_pedidos["ID"] = pd.to_numeric(
        df_pedidos["ID"], errors="coerce"
    ).fillna(0).astype(int)

    años = sorted(df_pedidos["Año"].unique(), reverse=True)
    año = st.selectbox("📅 Año del pedido", años, key="delete_year")

    df_año = df_pedidos[df_pedidos["Año"] == año]
    if df_año.empty:
        st.info(f"📭 No hay pedidos en {año}.")
        return

    max_id = int(df_año["ID"].max())

    pedido_id = st.number_input(
        "🆔 ID del pedido",
        min_value=1,
        value=max_id,
        step=1,
        key="delete_id"
    )

    pedido_df = df_año[df_año["ID"] == pedido_id]
    if pedido_df.empty:
        st.warning("⚠️ No existe ese pedido.")
        return

    pedido = pedido_df.iloc[0]

    st.warning(f"⚠️ Vas a eliminar el pedido **{pedido_id} / {año}**")

    if st.button("🗑️ ELIMINAR DEFINITIVAMENTE", type="primary"):
        doc_id = pedido.get("id_documento_firestore")
        if not doc_id:
            st.error("❌ Pedido sin ID de Firestore.")
            return

        if not delete_document_firestore("pedidos", doc_id):
            st.error("❌ Error eliminando el pedido.")
            return

        df_pedidos = df_pedidos[
            ~((df_pedidos["Año"] == año) & (df_pedidos["ID"] == pedido_id))
        ]

        if not save_dataframe_firestore(df_pedidos, "pedidos"):
            st.error("❌ Error guardando cambios.")
            return

        st.success("✅ Pedido eliminado correctamente.")
        time.sleep(1)
        st.rerun()
