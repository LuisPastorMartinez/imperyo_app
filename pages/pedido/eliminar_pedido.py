# pages/pedido/eliminar_pedido.py
import streamlit as st
import pandas as pd
from utils import delete_document_firestore, save_dataframe_firestore

def show_delete(df_pedidos, df_listas):
    st.subheader("Eliminar Pedido")

    del_id = st.number_input("ID del pedido a eliminar:", min_value=1, key="delete_id_input")
    if st.button("Buscar Pedido", key="search_pedido_button"):
        pedido = df_pedidos[df_pedidos['ID'] == del_id]
        if not pedido.empty:
            st.session_state.pedido_a_eliminar = pedido.iloc[0].to_dict()
            st.success(f"Pedido {del_id} encontrado")
        else:
            st.warning(f"No existe un pedido con ID {del_id}")
            st.session_state.pedido_a_eliminar = None

    if 'pedido_a_eliminar' in st.session_state and st.session_state.pedido_a_eliminar:
        pedido = st.session_state.pedido_a_eliminar
        st.warning("⚠️ **Detalles del pedido a eliminar:**")
        st.json({
            "ID": pedido['ID'],
            "Cliente": pedido['Cliente'],
            "Producto": pedido['Producto'],
            "Fecha entrada": str(pedido['Fecha entrada']),
            "Precio": pedido['Precio']
        })

        confirmacion = st.checkbox("Confirmo que deseo eliminar este pedido permanentemente", key="confirm_delete")
        if confirmacion:
            if st.button("Eliminar Definitivamente", type="primary", key="confirm_delete_button"):
                try:
                    df_pedidos = df_pedidos[df_pedidos['ID'] != del_id]
                    doc_id = pedido['id_documento_firestore']
                    if delete_document_firestore('pedidos', doc_id):
                        if 'data' not in st.session_state:
                            st.session_state['data'] = {}
                        st.session_state.data['df_pedidos'] = df_pedidos
                        if save_dataframe_firestore(df_pedidos, 'pedidos'):
                            st.success(f"Pedido {del_id} eliminado correctamente!")
                            st.session_state.pedido_a_eliminar = None
                            st.rerun()
                        else:
                            st.error("Error al guardar los cambios en Firestore")
                    else:
                        st.error("Error al eliminar el pedido de Firestore")
                except Exception as e:
                    st.error(f"Error al eliminar el pedido: {str(e)}")
