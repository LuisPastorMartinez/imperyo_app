# pages/pedido/consultar_pedidos.py
import streamlit as st
import pandas as pd


def show_consult(df_pedidos, df_listas):
    st.subheader("📋 Consultar Pedidos")

    if df_pedidos.empty:
        st.info("No hay pedidos registrados.")
        return

    # Mostrar pedidos en tabla con acciones
    for _, row in df_pedidos.iterrows():
        col1, col2, col3, col4, col5 = st.columns([1, 3, 3, 2, 2])

        with col1:
            st.markdown(f"**{row['ID']}**")  # ID en negrita

        with col2:
            st.write(row.get("Cliente", ""))

        with col3:
            st.write(row.get("Producto", ""))

        with col4:
            # Botón Modificar
            if st.button("✏️ Modificar", key=f"mod_{row['ID']}"):
                st.session_state.modify_id_input = int(row['ID'])
                st.session_state.active_pedido_tab = "Modificar"
                st.rerun()

        with col5:
            # Botón Eliminar
            if st.button("🗑️ Eliminar", key=f"del_{row['ID']}"):
                st.session_state.delete_id_input = int(row['ID'])
                st.session_state.active_pedido_tab = "Eliminar"
                st.rerun()
