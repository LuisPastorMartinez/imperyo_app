        # ------------------------------
        # BOTÓN PROGRESIVO ELIMINAR
        # ------------------------------
        if "delete_step" not in st.session_state:
            st.session_state.delete_step = 0

        # CSS para botones de colores
        st.markdown("""
        <style>
        .stButton>button { width: 100%; font-weight: bold; }
        button[data-baseweb="button"].green {
            background-color: #28a745 !important; /* Verde */
            color: white !important;
        }
        button[data-baseweb="button"].yellow {
            background-color: #ffc107 !important; /* Amarillo */
            color: black !important;
        }
        button[data-baseweb="button"].red {
            background-color: #dc3545 !important; /* Rojo */
            color: white !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # Paso 1 - Verde
        if st.session_state.delete_step == 0:
            if st.button("Eliminar Pedido", key="btn_eliminar"):
                st.session_state.delete_step = 1
            st.markdown(
                "<script>var el = window.parent.document.querySelector('button[kind=secondary]'); "
                "if (el) el.classList.add('green');</script>",
                unsafe_allow_html=True
            )

        # Paso 2 - Amarillo
        elif st.session_state.delete_step == 1:
            if st.button(f"¿Seguro eliminar pedido N° {pedido['ID']}?", key="btn_confirmar"):
                st.session_state.delete_step = 2
            st.markdown(
                "<script>var el = window.parent.document.querySelector('button[kind=secondary]'); "
                "if (el) el.classList.add('yellow');</script>",
                unsafe_allow_html=True
            )

        # Paso 3 - Rojo y eliminar
        elif st.session_state.delete_step == 2:
            if st.button(f"Pedido a eliminar N° {pedido['ID']}", key="btn_borrar"):
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

                        # Reset automático al paso 0 (verde)
                        st.session_state.delete_step = 0
                        if 'pedido_a_eliminar' in st.session_state:
                            del st.session_state['pedido_a_eliminar']
                        st.session_state.data['df_pedidos'] = df_pedidos
                    else:
                        st.error("❌ Error al eliminar el pedido en Firestore.")
                except Exception as e:
                    st.error(f"Error al eliminar el pedido: {str(e)}")
            st.markdown(
                "<script>var el = window.parent.document.querySelector('button[kind=secondary]'); "
                "if (el) el.classList.add('red');</script>",
                unsafe_allow_html=True
            )
