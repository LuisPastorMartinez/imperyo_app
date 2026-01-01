import streamlit as st
import pandas as pd
import time
import json
from datetime import datetime
from utils.firestore_utils import delete_document_firestore, save_dataframe_firestore


def reindexar_ids_por_año(df_pedidos, año):
    """
    Reindexa los IDs visibles SOLO dentro de un año concreto.
    """
    df_year = df_pedidos[df_pedidos["Año"] == año].copy()
    if df_year.empty:
        return df_pedidos

    df_year = df_year.sort_values("ID").reset_index(drop=True)
    df_year["ID"] = range(1, len(df_year) + 1)

    df_pedidos.update(df_year)
    return df_pedidos


def show_delete(df_pedidos, df_listas):
    st.subheader("🗑️ Eliminar Pedido")

    if df_pedidos is None or df_pedidos.empty:
        st.info("📭 No hay pedidos registrados.")
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
        key="delete_año_selector"
    )

    # ---------- FILTRAR POR AÑO ----------
    df_year = df_pedidos[df_pedidos["Año"] == año_seleccionado].copy()

    if df_year.empty:
        st.info(f"📭 No hay pedidos en {año_seleccionado}")
        return

    # ---------- ELIMINAR PEDIDO INDIVIDUAL ----------
    st.markdown("### 🗑️ Eliminar pedido individual")

    del_id = st.number_input(
        "ID del pedido",
        min_value=1,
        step=1,
        key="delete_id_input"
    )

    pedido = df_year[df_year["ID"] == del_id]

    if pedido.empty:
        st.warning("⚠️ No existe un pedido con ese ID en este año.")
        return

    pedido = pedido.iloc[0]

    # ---------- MOSTRAR RESUMEN ----------
    st.markdown("**Pedido seleccionado:**")
    st.markdown(
        f"""
        - **Año:** {año_seleccionado}  
        - **ID:** {pedido['ID']}  
        - **Cliente:** {pedido.get('Cliente','')}  
        - **Club:** {pedido.get('Club','')}  
        - **Precio:** {pedido.get('Precio',0):.2f} €  
        """
    )

    # ---------- CONFIRMACIÓN ----------
    confirmar = st.checkbox(
        "⚠️ Confirmo que quiero eliminar este pedido definitivamente",
        key="confirm_delete_checkbox"
    )

    if st.button("🗑️ Eliminar Pedido", type="primary", disabled=not confirmar):
        doc_id = pedido.get("id_documento_firestore")

        if not doc_id:
            st.error("❌ El pedido no tiene ID de Firestore.")
            return

        # Eliminar de Firestore
        if not delete_document_firestore("pedidos", doc_id):
            st.error("❌ Error al eliminar el pedido en Firestore.")
            return

        # Eliminar del DataFrame
        df_pedidos = df_pedidos[
            ~(
                (df_pedidos["Año"] == año_seleccionado) &
                (df_pedidos["ID"] == del_id)
            )
        ].reset_index(drop=True)

        # Reindexar IDs SOLO de ese año
        df_pedidos = reindexar_ids_por_año(df_pedidos, año_seleccionado)

        # Guardar cambios
        if not save_dataframe_firestore(df_pedidos, "pedidos"):
            st.error("❌ Error al guardar cambios tras eliminar.")
            return

        st.success(f"✅ Pedido {del_id} del año {año_seleccionado} eliminado correctamente")
        st.balloons()
        time.sleep(1)

        # Actualizar sesión
        st.session_state.data["df_pedidos"] = df_pedidos
        st.rerun()
