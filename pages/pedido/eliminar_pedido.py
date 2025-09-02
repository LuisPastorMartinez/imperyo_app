# pages/pedido/eliminar_pedido.py
import streamlit as st
import pandas as pd
import time
from utils import delete_document_firestore, save_dataframe_firestore


def reindex_pedidos(df_pedidos):
    """Reordena los IDs de los pedidos para que sean consecutivos desde 1 hasta N."""
    df_pedidos = df_pedidos.sort_values(by="ID").reset_index(drop=True)
    df_pedidos["ID"] = range(1, len(df_pedidos) + 1)
    return df_pedidos


def show_delete(df_pedidos, df_listas):
    st.subheader("🗑️ Eliminar Pedido")

    # Cargar ID automáticamente si viene desde consultar
    del_id = st.session_state.get("delete_id_input", None)
    if del_id is None:
        del_id = st.number_input("ID del pedido a eliminar:", min_value=1, key="delete_id_input")

    if st.button("Buscar Pedido", key="search_pedido_button") or (
        "pedido_a_eliminar" not in st.session_state and del_id
    ):
        pedido = df_pedidos[df_pedidos['ID'] == del_id]
        if not pedido.empty:
            st.session_state.pedido_a_eliminar = pedido.iloc[0].to_dict()
            st.success(f"Pedido {del_id} cargado para eliminar")
        else:
            st.warning(f"No existe un pedido con ID {del_id}")
            st.session_state.pedido_a_eliminar = None

    if 'pedido_a_eliminar' in st.session_state and st.session_state.pedido_a_eliminar:
        pedido = st.session_state.pedido_a_eliminar

        st.markdown(f"### ⚠️ Pedido a eliminar: **{pedido['ID']}**")

        with st.form("eliminar_pedido_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Cliente", value=str(pedido.get('Cliente','')), disabled=True)
                st.text_input("Teléfono", value=str(pedido.get('Telefono','')), disabled=True)
                st.text_input("Club", value=str(pedido.get('Club','')), disabled=True)
                st.text_input("Producto", value=str(pedido.get('Producto','')), disabled=True)
                st.text_input("Talla", value=str(pedido.get('Talla','')), disabled=True)
                st.text_input("Tela", value=str(pedido.get('Tela','')), disabled=True)
                st.text_area("Descripción", value=str(pedido.get('Breve Descripción','')), disabled=True)

            with col2:
                st.text_input("Fecha entrada", value=str(pedido.get('Fecha entrada','')), disabled=True)
                st.text_input("Fecha salida", value=str(pedido.get('Fecha Salida','')), disabled=True)
                st.text_input("Precio", value=str(pedido.get('Precio','')), disabled=True)
                st.text_input("Precio factura", value=str(pedido.get('Precio Factura','')), disabled=True)
                st.text_input("Tipo de pago", value=str(pedido.get('Tipo de pago','')), disabled=True)
                st.text_input("Adelanto", value=str(pedido.get('Adelanto','')), disabled=True)
                st.text_area("Observaciones", value=str(pedido.get('Observaciones','')), disabled=True)

            st.write("**Estado del pedido:**")
            estado_cols = st.columns(5)
            with estado_cols[0]:
                st.checkbox("Empezado", value=bool(pedido.get('Inicio Trabajo', False)), disabled=True)
            with estado_cols[1]:
                st.checkbox("Terminado", value=bool(pedido.get('Trabajo Terminado', False)), disabled=True)
            with estado_cols[2]:
                st.checkbox("Cobrado", value=bool(pedido.get('Cobrado', False)), disabled=True)
            with estado_cols[3]:
                st.checkbox("Retirado", value=bool(pedido.get('Retirado', False)), disabled=True)
            with estado_cols[4]:
                st.checkbox("Pendiente", value=bool(pedido.get('Pendiente', False)), disabled=True)

            eliminar = st.form_submit_button("🗑️ Eliminar Definitivamente", type="primary")

            if eliminar:
                if "delete_confirm_step" not in st.session_state:
                    # Primera pulsación → pedir confirmación
                    st.session_state.delete_confirm_step = True
                    st.warning("⚠️ Pulsa de nuevo 'Eliminar Definitivamente' para confirmar.")
                else:
                    try:
                        df_pedidos = df_pedidos[df_pedidos['ID'] != del_id]

                        # 🔹 Reindexar IDs después de eliminar
                        df_pedidos = reindex_pedidos(df_pedidos)

                        doc_id = pedido['id_documento_firestore']
                        if delete_document_firestore('pedidos', doc_id):
                            if save_dataframe_firestore(df_pedidos, 'pedidos'):
                                success_placeholder = st.empty()
                                success_placeholder.success(f"Pedido {del_id} eliminado y IDs reindexados correctamente!")
                                time.sleep(5)
                                success_placeholder.empty()

                                # 🔹 Limpiar session_state
                                keys_to_delete = [k for k in st.session_state.keys() if k.startswith("delete_")]
                                for k in keys_to_delete:
                                    del st.session_state[k]
                                if 'pedido_a_eliminar' in st.session_state:
                                    del st.session_state['pedido_a_eliminar']
                                if "delete_confirm_step" in st.session_state:
                                    del st.session_state["delete_confirm_step"]

                                # Actualizar datos en cache
                                if 'data' not in st.session_state:
                                    st.session_state['data'] = {}
                                st.session_state.data['df_pedidos'] = df_pedidos

                                # 🔹 Volver a "Consultar Pedidos"
                                st.session_state.active_pedido_tab = "Consultar Pedidos"
                                st.rerun()

                            else:
                                st.error("Error al guardar los cambios en Firestore")
                        else:
                            st.error("Error al eliminar el pedido de Firestore")
                    except Exception as e:
                        st.error(f"Error al eliminar el pedido: {str(e)}")
