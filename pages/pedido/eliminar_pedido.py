# pages/pedido/eliminar_pedido.py
import streamlit as st
import pandas as pd
import time
from utils.firestore_utils import delete_document_firestore, save_dataframe_firestore

def show_delete(df_pedidos, df_listas):
    st.subheader("Eliminar Pedido")

    # ✅ Input para ID
    del_id = st.number_input("ID del pedido a eliminar:", min_value=1, value=1, key="delete_id_input")

    # ✅ Botón para cargar pedido
    if st.button("Buscar Pedido", key="search_pedido_button"):
        pedido = df_pedidos[df_pedidos['ID'] == del_id]
        if not pedido.empty:
            st.session_state.pedido_a_eliminar = pedido.iloc[0].to_dict()
            st.success(f"Pedido {del_id} cargado para eliminación")
        else:
            st.warning(f"No existe un pedido con ID {del_id}")
            if 'pedido_a_eliminar' in st.session_state:
                del st.session_state['pedido_a_eliminar']

    # ✅ Mostrar pedido a eliminar
    if 'pedido_a_eliminar' in st.session_state and st.session_state.pedido_a_eliminar:
        pedido = st.session_state.pedido_a_eliminar

        st.markdown(f"### ⚠️ Pedido a eliminar: **{pedido['ID']}**")
        st.json({
            "Cliente": pedido.get('Cliente', ''),
            "Teléfono": pedido.get('Telefono', ''),
            "Club": pedido.get('Club', ''),
            "Producto": pedido.get('Producto', ''),
            "Precio": pedido.get('Precio', 0),
            "Fecha entrada": str(pedido.get('Fecha entrada', '')),
            "Estado": {
                "Empezado": bool(pedido.get('Inicio Trabajo', False)),
                "Terminado": bool(pedido.get('Trabajo Terminado', False)),
                "Retirado": bool(pedido.get('Retirado', False)),
            }
        })

        # ✅ Confirmación de doble clic
        if st.button("🗑️ Eliminar Definitivamente", type="primary", key="confirm_delete_button"):
            if not st.session_state.get('confirm_delete_step', False):
                st.session_state.confirm_delete_step = True
                st.warning("⚠️ ¿Estás seguro? Pulsa de nuevo 'Eliminar Definitivamente' para confirmar.")
            else:
                try:
                    # ✅ Obtener doc_id
                    doc_id = pedido.get('id_documento_firestore')
                    if not doc_id:
                        st.error("Error: El pedido no tiene ID de documento en Firestore.")
                        return

                    # ✅ Eliminar de Firestore
                    if not delete_document_firestore('pedidos', doc_id):
                        st.error("Error al eliminar el pedido de Firestore.")
                        return

                    # ✅ Eliminar del DataFrame
                    df_pedidos = df_pedidos[df_pedidos['ID'] != del_id].reset_index(drop=True)

                    # ✅ Guardar cambios
                    if not save_dataframe_firestore(df_pedidos, 'pedidos'):
                        st.error("Error al guardar los cambios en Firestore.")
                        return

                    # ✅ Éxito
                    st.success(f"✅ Pedido {del_id} eliminado correctamente!")
                    st.balloons()
                    time.sleep(2)

                    # ✅ Limpiar estado
                    keys_to_delete = [
                        'pedido_a_eliminar',
                        'confirm_delete_step',
                        'delete_id_input'
                    ]
                    for k in keys_to_delete:
                        if k in st.session_state:
                            del st.session_state[k]

                    # ✅ Actualizar sesión
                    if 'data' not in st.session_state:
                        st.session_state['data'] = {}
                    st.session_state.data['df_pedidos'] = df_pedidos

                    # ✅ Recargar
                    st.rerun()

                except Exception as e:
                    st.error(f"Error al eliminar el pedido: {str(e)}")