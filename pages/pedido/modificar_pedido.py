# pages/pedido/modificar_pedido.py
import streamlit as st
import pandas as pd
import time
from datetime import datetime
from utils import save_dataframe_firestore


def show_modify(df_pedidos, df_listas):
    st.subheader("✏️ Modificar Pedido")

    # Si ya viene cargado desde consultar
    mod_id = st.session_state.get("modify_id_input", None)

    if mod_id is None:
        mod_id = st.number_input("ID del pedido a modificar:", min_value=1, key="modify_id_input")

    if st.button("Buscar Pedido", key="load_pedido_button") or "pedido_a_modificar" not in st.session_state:
        pedido = df_pedidos[df_pedidos['ID'] == mod_id]
        if not pedido.empty:
            st.session_state.pedido_a_modificar = pedido.iloc[0].to_dict()
            st.success(f"Pedido {mod_id} cargado para modificar")
        else:
            st.warning(f"No existe un pedido con ID {mod_id}")
            st.session_state.pedido_a_modificar = None

    if 'pedido_a_modificar' in st.session_state and st.session_state.pedido_a_modificar:
        pedido = st.session_state.pedido_a_modificar

        st.markdown(f"### ✏️ Modificando pedido **{pedido['ID']}**")

        with st.form("modificar_pedido_form"):
            col1, col2 = st.columns(2)

            with col1:
                cliente = st.text_input("Cliente", value=str(pedido.get('Cliente', '')))
                telefono = st.text_input("Teléfono", value=str(pedido.get('Telefono', '')))
                club = st.text_input("Club", value=str(pedido.get('Club', '')))
                producto = st.text_input("Producto", value=str(pedido.get('Producto', '')))
                talla = st.text_input("Talla", value=str(pedido.get('Talla', '')))
                tela = st.text_input("Tela", value=str(pedido.get('Tela', '')))
                descripcion = st.text_area("Descripción", value=str(pedido.get('Breve Descripción', '')))

            with col2:
                fecha_entrada = st.date_input("Fecha entrada", value=pd.to_datetime(pedido.get('Fecha entrada', datetime.now())).date())
                fecha_salida = st.date_input("Fecha salida", value=pd.to_datetime(pedido.get('Fecha Salida', datetime.now())).date())
                precio = st.number_input("Precio", value=float(pedido.get('Precio', 0.0)))
                precio_factura = st.number_input("Precio factura", value=float(pedido.get('Precio Factura', 0.0)))
                tipo_pago = st.text_input("Tipo de pago", value=str(pedido.get('Tipo de pago', '')))
                adelanto = st.number_input("Adelanto", value=float(pedido.get('Adelanto', 0.0)))
                observaciones = st.text_area("Observaciones", value=str(pedido.get('Observaciones', '')))

            st.write("**Estado del pedido:**")
            estado_cols = st.columns(5)
            with estado_cols[0]:
                empezado = st.checkbox("Empezado", value=bool(pedido.get('Inicio Trabajo', False)))
            with estado_cols[1]:
                terminado = st.checkbox("Terminado", value=bool(pedido.get('Trabajo Terminado', False)))
            with estado_cols[2]:
                cobrado = st.checkbox("Cobrado", value=bool(pedido.get('Cobrado', False)))
            with estado_cols[3]:
                retirado = st.checkbox("Retirado", value=bool(pedido.get('Retirado', False)))
            with estado_cols[4]:
                pendiente = st.checkbox("Pendiente", value=bool(pedido.get('Pendiente', False)))

            guardar = st.form_submit_button("💾 Guardar Cambios", type="primary")

            if guardar:
                if "modify_confirm_step" not in st.session_state:
                    st.session_state.modify_confirm_step = True
                    st.warning("⚠️ Pulsa de nuevo 'Guardar Cambios' para confirmar.")
                else:
                    try:
                        idx = df_pedidos.index[df_pedidos['ID'] == pedido['ID']].tolist()[0]
                        df_pedidos.at[idx, 'Cliente'] = cliente
                        df_pedidos.at[idx, 'Telefono'] = telefono
                        df_pedidos.at[idx, 'Club'] = club
                        df_pedidos.at[idx, 'Producto'] = producto
                        df_pedidos.at[idx, 'Talla'] = talla
                        df_pedidos.at[idx, 'Tela'] = tela
                        df_pedidos.at[idx, 'Breve Descripción'] = descripcion
                        df_pedidos.at[idx, 'Fecha entrada'] = fecha_entrada
                        df_pedidos.at[idx, 'Fecha Salida'] = fecha_salida
                        df_pedidos.at[idx, 'Precio'] = precio
                        df_pedidos.at[idx, 'Precio Factura'] = precio_factura
                        df_pedidos.at[idx, 'Tipo de pago'] = tipo_pago
                        df_pedidos.at[idx, 'Adelanto'] = adelanto
                        df_pedidos.at[idx, 'Observaciones'] = observaciones
                        df_pedidos.at[idx, 'Inicio Trabajo'] = empezado
                        df_pedidos.at[idx, 'Trabajo Terminado'] = terminado
                        df_pedidos.at[idx, 'Cobrado'] = cobrado
                        df_pedidos.at[idx, 'Retirado'] = retirado
                        df_pedidos.at[idx, 'Pendiente'] = pendiente

                        if save_dataframe_firestore(df_pedidos, 'pedidos'):
                            success_placeholder = st.empty()
                            success_placeholder.success(f"Pedido {pedido['ID']} modificado correctamente!")
                            time.sleep(5)
                            success_placeholder.empty()

                            # Limpiar estado
                            keys_to_delete = [k for k in list(st.session_state.keys()) if k.startswith("mod_") or k.startswith("modify_")]
                            for k in keys_to_delete:
                                del st.session_state[k]
                            if 'pedido_a_modificar' in st.session_state:
                                del st.session_state['pedido_a_modificar']
                            if "modify_confirm_step" in st.session_state:
                                del st.session_state["modify_confirm_step"]

                            st.session_state.data['df_pedidos'] = df_pedidos
                            st.session_state.active_pedido_tab = "Consultar Pedidos"
                            st.rerun()

                        else:
                            st.error("Error al guardar los cambios en Firestore")

                    except Exception as e:
                        st.error(f"Error al modificar el pedido: {str(e)}")
