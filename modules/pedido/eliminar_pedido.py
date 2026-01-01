import streamlit as st
import pandas as pd
import time

from utils.firestore_utils import delete_document_firestore, save_dataframe_firestore


def reindexar_ids_por_año(df, año):
    """
    Reasigna IDs consecutivos SOLO dentro del año indicado.
    """
    df_año = df[df["Año"] == año].sort_values("ID").reset_index(drop=True)
    df_año["ID"] = range(1, len(df_año) + 1)
    df.update(df_año)
    return df


def show_delete(df_pedidos, df_listas=None):
    st.subheader("🗑️ Eliminar Pedido")
    st.write("---")

    if df_pedidos is None or df_pedidos.empty:
        st.info("No hay pedidos.")
        return

    # -------- AÑOS DISPONIBLES --------
    años_disponibles = sorted(
        df_pedidos["Año"].dropna().unique(),
        reverse=True
    )

    año = st.selectbox(
        "📅 Año del pedido",
        años_disponibles,
        index=0
    )

    df_año = df_pedidos[df_pedidos["Año"] == año].copy()
    if df_año.empty:
        st.info(f"No hay pedidos en {año}.")
        return

    pedido_id = st.number_input(
        "🆔 ID del pedido (del año seleccionado)",
        min_value=1,
        step=1
    )

    pedido = df_año[df_año["ID"] == pedido_id]
    if pedido.empty:
        st.warning(f"No existe el pedido {pedido_id} / {año}.")
        return

    pedido = pedido.iloc[0]

    st.warning(f"⚠️ Vas a eliminar el pedido **{pedido_id} / {año}**")

    st.markdown(
        f"""
        **Cliente:** {pedido.get('Cliente', '')}  
        **Club:** {pedido.get('Club', '')}  
        **Precio:** {pedido.get('Precio', 0):.2f} €
        """
    )

    if st.button("🗑️ ELIMINAR DEFINITIVAMENTE", type="primary"):
        doc_id = pedido.get("id_documento_firestore")
        if not doc_id:
            st.error("Pedido sin ID de Firestore.")
            return

        if not delete_document_firestore("pedidos", doc_id):
            st.error("Error eliminando el pedido en Firestore.")
            return

        # Eliminar del DataFrame
        df_pedidos = df_pedidos[
            ~((df_pedidos["ID"] == pedido_id) & (df_pedidos["Año"] == año))
        ].reset_index(drop=True)

        # Reindexar IDs SOLO de ese año
        df_pedidos = reindexar_ids_por_año(df_pedidos, año)

        if save_dataframe_firestore(df_pedidos, "pedidos"):
            st.success(f"Pedido {pedido_id} / {año} eliminado correctamente.")
            st.balloons()
            time.sleep(1)

            st.session_state.data["df_pedidos"] = df_pedidos
            st.rerun()
        else:
            st.error("Error guardando los cambios.")
