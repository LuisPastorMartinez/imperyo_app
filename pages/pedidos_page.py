import streamlit as st
import pandas as pd
from datetime import datetime

# Asume que estos imports están en la carpeta utils
from utils.firestore_utils import save_dataframe_firestore, delete_document_firestore, get_next_id

def show_pedidos_page(df_pedidos, df_listas):
    st.header("Gestión de Pedidos")

    # --- TABS ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Ver Pedidos", "➕ Añadir Pedido", "✏️ Editar Pedido", "🗑️ Eliminar Pedido"])

    # --- TAB 1: VER PEDIDOS ---
    with tab1:
        st.subheader("Lista de Pedidos")
        
        # Opciones de filtrado
        estado_filtro = st.radio(
            "Filtrar por estado:",
            ["Todos", "Pendientes", "Trabajo Terminado", "Retirados"],
            key="filtro_pedidos_ver"
        )

        df_filtrado = df_pedidos.copy()
        if estado_filtro == "Pendientes":
            df_filtrado = df_filtrado[
                (df_filtrado['Inicio Trabajo'] == False) |
                (df_filtrado['Trabajo Terminado'] == False)
            ]
        elif estado_filtro == "Trabajo Terminado":
            df_filtrado = df_filtrado[df_filtrado['Trabajo Terminado'] == True]
        elif estado_filtro == "Retirados":
            df_filtrado = df_filtrado[df_filtrado['Retirado'] == True]

        if not df_filtrado.empty:
            df_filtrado_sorted = df_filtrado.sort_values(by='ID', ascending=False)
            st.dataframe(df_filtrado_sorted, use_container_width=True)
        else:
            st.info("No hay pedidos para mostrar con este filtro.")

    # --- TAB 2: AÑADIR PEDIDO ---
    with tab2:
        st.subheader("Añadir un Nuevo Pedido")
        with st.form("form_add_pedido"):
            # Usar st.columns para un diseño más limpio
            col1, col2 = st.columns(2)
            with col1:
                cliente = st.text_input("Cliente", key="add_cliente")
                producto = st.text_input("Producto", key="add_producto")
                club = st.text_input("Club", key="add_club")
                telefono = st.text_input("Teléfono", key="add_telefono")
            with col2:
                # Opciones de listas
                opciones_talla = [''] + df_listas['Talla'].dropna().unique().tolist() if not df_listas.empty and 'Talla' in df_listas.columns else ['']
                talla = st.selectbox("Talla", opciones_talla, key="add_talla")
                opciones_tela = [''] + df_listas['Tela'].dropna().unique().tolist() if not df_listas.empty and 'Tela' in df_listas.columns else ['']
                tela = st.selectbox("Tela", opciones_tela, key="add_tela")
                descripcion = st.text_area("Breve Descripción", key="add_descripcion")

            col3, col4, col5 = st.columns(3)
            with col3:
                precio = st.number_input("Precio", min_value=0.0, step=0.01, key="add_precio")
                precio_factura = st.number_input("Precio Factura", min_value=0.0, step=0.01, key="add_precio_factura")
            with col4:
                opciones_pago = [''] + df_listas['Tipo de pago'].dropna().unique().tolist() if not df_listas.empty and 'Tipo de pago' in df_listas.columns else ['']
                tipo_pago = st.selectbox("Tipo de pago", opciones_pago, key="add_tipo_pago")
                adelanto = st.number_input("Adelanto", min_value=0.0, step=0.01, key="add_adelanto")
            with col5:
                fecha_entrada = st.date_input("Fecha entrada", value=datetime.now(), key="add_fecha_entrada")
                observaciones = st.text_area("Observaciones", key="add_observaciones")

            # Checkboxes de estado
            st.markdown("---")
            st.write("Estado del pedido:")
            col_check1, col_check2, col_check3, col_check4, col_check5 = st.columns(5)
            with col_check1:
                inicio_trabajo = st.checkbox("Inicio Trabajo", key="add_inicio_trabajo")
            with col_check2:
                trabajo_terminado = st.checkbox("Trabajo Terminado", key="add_trabajo_terminado")
            with col_check3:
                cobrado = st.checkbox("Cobrado", key="add_cobrado")
            with col_check4:
                retirado = st.checkbox("Retirado", key="add_retirado")
            with col_check5:
                pendiente = st.checkbox("Pendiente", key="add_pendiente")
                
            submitted = st.form_submit_button("Guardar Pedido")
            
            if submitted:
                # *** CORRECCIÓN CLAVE AQUÍ ***
                # La columna en el DataFrame es 'Fecha entrada', no 'Fecha Entrada'
                # Además, el campo 'Breve Descripción' estaba mal escrito en el nuevo dict.
                new_id = get_next_id(df_pedidos, 'ID')
                new_pedido = {
                    'ID': new_id,
                    'Cliente': cliente,
                    'Producto': producto,
                    'Club': club,
                    'Telefono': telefono,
                    'Talla': talla,
                    'Tela': tela,
                    'Breve Descripción': descripcion,
                    'Fecha entrada': fecha_entrada, # <-- Corregido
                    'Fecha Salida': None, # Opcional, puedes poner un campo para esto
                    'Precio': precio,
                    'Precio Factura': precio_factura,
                    'Tipo de pago': tipo_pago,
                    'Adelanto': adelanto,
                    'Observaciones': observaciones,
                    'Inicio Trabajo': inicio_trabajo,
                    'Trabajo Terminado': trabajo_terminado,
                    'Cobrado': cobrado,
                    'Retirado': retirado,
                    'Pendiente': pendiente
                }
                
                # Crear un nuevo DataFrame de una fila
                new_df = pd.DataFrame([new_pedido])
                
                # Usar pd.concat para añadir la nueva fila al DataFrame existente
                # Se usa ignore_index=True para que se reajuste el índice
                df_pedidos_updated = pd.concat([df_pedidos, new_df], ignore_index=True)
                
                if save_dataframe_firestore(df_pedidos_updated, 'pedidos'):
                    st.success("Pedido añadido exitosamente!")
                    st.session_state['data']['df_pedidos'] = df_pedidos_updated
                    st.rerun() # Recarga la página para mostrar los datos actualizados
                else:
                    st.error("Error al guardar el pedido en Firestore.")

    # --- TAB 3: EDITAR PEDIDO ---
    with tab3:
        st.subheader("Editar un Pedido Existente")
        if not df_pedidos.empty:
            pedidos_para_editar = df_pedidos.sort_values(by='ID', ascending=False)
            pedido_a_editar_id = st.selectbox(
                "Selecciona el ID del pedido a editar",
                options=pedidos_para_editar['ID'].tolist(),
                key="edit_pedido_id"
            )
            
            if pedido_a_editar_id:
                pedido_actual = df_pedidos[df_pedidos['ID'] == pedido_a_editar_id].iloc[0].to_dict()
                
                with st.form("form_edit_pedido"):
                    col1_edit, col2_edit = st.columns(2)
                    with col1_edit:
                        st.text_input("Cliente", value=pedido_actual.get('Cliente', ''), key="edit_cliente")
                        st.text_input("Producto", value=pedido_actual.get('Producto', ''), key="edit_producto")
                        st.text_input("Club", value=pedido_actual.get('Club', ''), key="edit_club")
                        st.text_input("Teléfono", value=pedido_actual.get('Telefono', ''), key="edit_telefono")
                    with col2_edit:
                        opciones_talla = [''] + df_listas['Talla'].dropna().unique().tolist() if not df_listas.empty and 'Talla' in df_listas.columns else ['']
                        st.selectbox("Talla", opciones_talla, index=opciones_talla.index(pedido_actual.get('Talla', '')) if pedido_actual.get('Talla', '') in opciones_talla else 0, key="edit_talla")
                        opciones_tela = [''] + df_listas['Tela'].dropna().unique().tolist() if not df_listas.empty and 'Tela' in df_listas.columns else ['']
                        st.selectbox("Tela", opciones_tela, index=opciones_tela.index(pedido_actual.get('Tela', '')) if pedido_actual.get('Tela', '') in opciones_tela else 0, key="edit_tela")
                        st.text_area("Breve Descripción", value=pedido_actual.get('Breve Descripción', ''), key="edit_descripcion")

                    col3_edit, col4_edit, col5_edit = st.columns(3)
                    with col3_edit:
                        st.number_input("Precio", min_value=0.0, step=0.01, value=float(pedido_actual.get('Precio', 0.0)), key="edit_precio")
                        st.number_input("Precio Factura", min_value=0.0, step=0.01, value=float(pedido_actual.get('Precio Factura', 0.0)), key="edit_precio_factura")
                    with col4_edit:
                        opciones_pago = [''] + df_listas['Tipo de pago'].dropna().unique().tolist() if not df_listas.empty and 'Tipo de pago' in df_listas.columns else ['']
                        st.selectbox("Tipo de pago", opciones_pago, index=opciones_pago.index(pedido_actual.get('Tipo de pago', '')) if pedido_actual.get('Tipo de pago', '') in opciones_pago else 0, key="edit_tipo_pago")
                        st.number_input("Adelanto", min_value=0.0, step=0.01, value=float(pedido_actual.get('Adelanto', 0.0)), key="edit_adelanto")
                    with col5_edit:
                        fecha_entrada_val = pedido_actual.get('Fecha entrada', datetime.now().date())
                        st.date_input("Fecha entrada", value=fecha_entrada_val, key="edit_fecha_entrada")
                        observaciones_val = pedido_actual.get('Observaciones', '')
                        st.text_area("Observaciones", value=observaciones_val, key="edit_observaciones")

                    st.markdown("---")
                    st.write("Estado del pedido:")
                    col_check1_edit, col_check2_edit, col_check3_edit, col_check4_edit, col_check5_edit = st.columns(5)
                    with col_check1_edit:
                        st.checkbox("Inicio Trabajo", value=pedido_actual.get('Inicio Trabajo', False), key="edit_inicio_trabajo")
                    with col_check2_edit:
                        st.checkbox("Trabajo Terminado", value=pedido_actual.get('Trabajo Terminado', False), key="edit_trabajo_terminado")
                    with col_check3_edit:
                        st.checkbox("Cobrado", value=pedido_actual.get('Cobrado', False), key="edit_cobrado")
                    with col_check4_edit:
                        st.checkbox("Retirado", value=pedido_actual.get('Retirado', False), key="edit_retirado")
                    with col_check5_edit:
                        st.checkbox("Pendiente", value=pedido_actual.get('Pendiente', False), key="edit_pendiente")
                        
                    edit_submitted = st.form_submit_button("Guardar Cambios")
                    
                    if edit_submitted:
                        # Buscar el índice del pedido en el DataFrame original
                        index_to_edit = df_pedidos[df_pedidos['ID'] == pedido_a_editar_id].index[0]
                        
                        # Actualizar los valores en el DataFrame
                        df_pedidos.loc[index_to_edit, 'Cliente'] = st.session_state['edit_cliente']
                        df_pedidos.loc[index_to_edit, 'Producto'] = st.session_state['edit_producto']
                        df_pedidos.loc[index_to_edit, 'Club'] = st.session_state['edit_club']
                        df_pedidos.loc[index_to_edit, 'Telefono'] = st.session_state['edit_telefono']
                        df_pedidos.loc[index_to_edit, 'Talla'] = st.session_state['edit_talla']
                        df_pedidos.loc[index_to_edit, 'Tela'] = st.session_state['edit_tela']
                        df_pedidos.loc[index_to_edit, 'Breve Descripción'] = st.session_state['edit_descripcion']
                        df_pedidos.loc[index_to_edit, 'Fecha entrada'] = st.session_state['edit_fecha_entrada']
                        df_pedidos.loc[index_to_edit, 'Precio'] = st.session_state['edit_precio']
                        df_pedidos.loc[index_to_edit, 'Precio Factura'] = st.session_state['edit_precio_factura']
                        df_pedidos.loc[index_to_edit, 'Tipo de pago'] = st.session_state['edit_tipo_pago']
                        df_pedidos.loc[index_to_edit, 'Adelanto'] = st.session_state['edit_adelanto']
                        df_pedidos.loc[index_to_edit, 'Observaciones'] = st.session_state['edit_observaciones']
                        df_pedidos.loc[index_to_edit, 'Inicio Trabajo'] = st.session_state['edit_inicio_trabajo']
                        df_pedidos.loc[index_to_edit, 'Trabajo Terminado'] = st.session_state['edit_trabajo_terminado']
                        df_pedidos.loc[index_to_edit, 'Cobrado'] = st.session_state['edit_cobrado']
                        df_pedidos.loc[index_to_edit, 'Retirado'] = st.session_state['edit_retirado']
                        df_pedidos.loc[index_to_edit, 'Pendiente'] = st.session_state['edit_pendiente']
                        
                        if save_dataframe_firestore(df_pedidos, 'pedidos'):
                            st.success(f"Pedido ID {pedido_a_editar_id} actualizado exitosamente!")
                            st.rerun()
                        else:
                            st.error(f"Error al actualizar el pedido ID {pedido_a_editar_id}.")
        else:
            st.info("No hay pedidos para editar.")

    # --- TAB 4: ELIMINAR PEDIDO ---
    with tab4:
        st.subheader("Eliminar un Pedido")
        if not df_pedidos.empty:
            pedido_a_eliminar_id = st.selectbox(
                "Selecciona el ID del pedido a eliminar",
                options=df_pedidos['ID'].tolist(),
                key="delete_pedido_id"
            )

            if st.button("Confirmar Eliminación", key="delete_button"):
                doc_id_firestore = df_pedidos[df_pedidos['ID'] == pedido_a_eliminar_id]['id_documento_firestore'].iloc[0]
                if delete_document_firestore('pedidos', doc_id_firestore):
                    # Eliminar la fila del DataFrame local
                    df_pedidos_updated = df_pedidos[df_pedidos['ID'] != pedido_a_eliminar_id]
                    st.session_state['data']['df_pedidos'] = df_pedidos_updated
                    st.success(f"Pedido ID {pedido_a_eliminar_id} eliminado exitosamente!")
                    st.rerun()
                else:
                    st.error(f"Error al eliminar el pedido ID {pedido_a_eliminar_id} de Firestore.")
        else:
            st.info("No hay pedidos para eliminar.")