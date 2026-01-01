import streamlit as st
import pandas as pd
import time
from datetime import datetime

from utils.firestore_utils import delete_document_firestore, save_dataframe_firestore


def reindexar_ids_por_año(df, año):
    """
    Reasigna IDs consecutivos SOLO dentro del año indicado,
    sin afectar a otros años.
    """
    df = df.copy()

    mask = df["Año"] == año
    df_año = df.loc[mask].sort_values("ID").reset_index(drop=True)

    df_año["ID"] = range(1, len(df_año) + 1)

    df.loc[mask, "ID"] = df_año["ID"].values
    return df


def show_delete(df_pedidos, df_listas=None):
    st.subheader("🗑️ Eliminar Pedido")
    st.write("---")

    if df_pedidos is None or df_pedidos.empty:
        st.info("📭 No hay pedidos.")
        return

    # ---------- ASEGURAR COLUMNA AÑO ----------
    if "Año" not in df_pedidos.columns:
        df_pedidos["Año"] = datetime.now().year

    df_pedidos["Año"] = (
        pd.to_numeric(df_pedidos["Año"], errors="coerce")
        .fillna(datetime.now().year)
        .astype("int64")
    )

    df_pedidos["ID"] = (
        pd.to_numeric(df_pedidos["ID"], errors="coerce")
        .fillna(0)
        .astype("int64")
    )

    # ---------- AÑOS DISPONIBLES ----------
    años_disponibles = sorted(
        df_pedidos["Año"].dropna().unique(),
        reverse=True
    )

    año = st.selectbox(
        "📅 Año del pedido",
        años_disponibles,
        index=0,
        key="delete_year_selector"
    )

    df_año = df_pedidos[df_pedidos["Año"] == año].copy()

    if df_año.empty:
        st.info(f"📭 No hay pedidos en {año}.")
        return

    pedido_id = st.number_input(
        "🆔 ID del pedido",
        min_value=1,
        step=1,
        key="delete_id_input"
    )

    pedido_df = df_año[df_año["ID"] == pedido_id]

    if pedido_df.empty:
        st.warning(f"⚠️ No existe el pedido {pedido_id} / {año}.")
        return

    pedido = pedido_df.iloc[0]

    st.warning(f"⚠️ Vas a eliminar el pedido **{pedido_id} / {año}**")

    st.markdown(
        f"""
        **Cliente:** {pedido.get('Cliente', '')}  
        **Club:** {pedido.get('Club', '')}  
        **Precio:** {float(pedido.get('Precio', 0) or 0):.2f} €
        """
    )

    if st.button("🗑️ ELIMINAR DEFINITIVAMENTE", type="primary"):
        doc_id = pedido.get("id_documento_firestore")

        if not doc_id:
            st.error("❌ Pedido sin ID de Firestore.")
            return

        if not delete_document_firestore("pedidos", doc_id):
            st.error("❌ Error eliminando el pedido en Firestore.")
            return

        # Eliminar del DataFrame
        df_pedidos = df_pedidos[
            ~(
                (df_pedidos["ID"] == pedido_id) &
                (df_pedidos["Año"] == año)
            )
        ].reset_index(drop=True)

        # Reindexar IDs SOLO del año afectado
        df_pedidos = reindexar_ids_por_año(df_pedidos, año)

        if not save_dataframe_firestore(df_pedidos, "pedidos"):
            st.error("❌ Error guardando los cambios.")
            return

        st.success(f"✅ Pedido {pedido_id} / {año} eliminado correctamente.")
        st.balloons()
        time.sleep(1)

        st.session_state.data["df_pedidos"] = df_pedidos
        st.rerun()
