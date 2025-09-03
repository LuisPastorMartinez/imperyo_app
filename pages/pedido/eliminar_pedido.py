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
    st.subheader("Eliminar Pedido")

    del_id = st.number_input("ID del pedido a eliminar:", min_value=1, key="delete_id_input")
    if st.button("Buscar Pedido", key="search_pedido_button"):
        pedido = df_pedidos[df_pedidos['ID'] == del_id]
        if not pedido.empty:
            st.session_state.pedido_a_eliminar = pedido.iloc[0].to_dict()
            st.success(f"Pedido {del_id} cargado para eliminación")
        else:
            st.warning(f"No existe un pedido con ID {del_id}")
            st.session_state.pedido_a_eliminar = None

    if 'pedido_a_eliminar' in st.session_state and st.session_state.pedido_a_eliminar:
        pedido = st.session_state.pedido_a_eliminar

        st.markdown(f"### ⚠️ Pedido a eliminar: **{pedido['ID']}**")

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

        # ------------------------------
        # BOTÓN PROGRESIVO ELIMINAR
        # ------------------------------
        if "delete_step" not in st.session_state:
            st.session_state.delete_step = 0

        # CSS para colorear botones
        st.markdown("""
        <style>
        .stButton>button { width: 100%; font-weight: bold; }
        .green-button>button {
            background-color: #28a745 !important; /* Verde */
            color: white !important;
        }
        .yellow-button>button {
            background-color: #ffc107 !important; /* Amarillo */
            color: black !important;
        }
        .red-button>button {
            background-color: #dc3545 !important; /* Rojo */
            color: white !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # Paso 1 - Verde
        if st.session_state.delete_step == 0:
            with st.container():
                if st.button("Eliminar Pedido", key="btn_green"):
                    st.session_state.delete_step = 1
            st.markdown('<div class="green-button"></div>', unsafe_allow_html=True)

        # Paso 2 - Amarillo
        elif st.session_state.delete_step == 1:
            with st.container():
                if st.button(f"¿Seguro eliminar pedido N° {pedido['ID']}?", key="btn_yellow"):
                    st.session_state.delete_step = 2
            st.markdown('<div class="yellow-button"></div>', unsafe_allow_html=True)

        # Paso 3 - Rojo y eliminar
        elif st.session_state.delete_step == 2:
            with st.container():
                if st.button(f"Pedido a eliminar N° {pedido['ID']}", key="btn_red"):
                    try:
                        # Eliminar del dataframe
                        df_pedidos = df_pedidos[df_pedidos['ID'] != del_id]
                        df_pedidos = reindex_pedidos(df_pedidos)

                        # Eliminar de Firestore
                        doc_id = pedido['id_documento_firestore']
                        if delete_document_firestore('pedidos', doc_id) and save_dataframe_firestore(df_pedidos, 'pedidos'):
                            msg = st.empty()
                            msg.success(f"✅ Pedido {del_id} eliminado con éxito y IDs reindexados.")
                            time.sleep(5)
                            msg.empty()

                            # Resetear estado automáticamente al verde
                            st.session_state.delete_step = 0
                            if 'pedido_a_eliminar' in st.session_state:
                                del st.session_state['pedido_a_eliminar']
                            st.session_state.data['df_pedidos'] = df_pedidos
                        else:
                            st.error("❌ Error al eliminar el pedido en Firestore.")
                    except Exception as e:
                        st.error(f"Error al eliminar el pedido: {str(e)}")
            st.markdown('<div class="red-button"></div>', unsafe_allow_html=True)
