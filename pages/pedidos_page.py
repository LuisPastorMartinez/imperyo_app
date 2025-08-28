# pages/pedidos_page.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils import get_next_id, save_dataframe_firestore, delete_document_firestore

def show_pedidos_page(df_pedidos, df_listas):
    
    # --- CORRECCIÓN 1: NORMALIZACIÓN DE TIPOS ---
    # Convertir la columna 'Club' a tipo string y reemplazar valores nulos/NaN por una cadena vacía
    df_pedidos['Club'] = df_pedidos['Club'].astype(str).replace('nan', '')

    # Definir las 4 pestañas
    tab1, tab2, tab3, tab4 = st.tabs(["Crear Pedido", "Consultar Pedidos", "Modificar Pedido", "Eliminar Pedido"])

    # Función para conversión segura de tipos
    # Esta función puede estar en un archivo de utilidades si quieres reutilizarla
    def convert_to_firestore_type(value):
        """Convierte los valores a tipos compatibles con Firestore"""
        if pd.isna(value) or value is None or value == "":
            return None
        elif isinstance(value, (int, float, str, bool)):
            return value
        elif isinstance(value, (date, datetime)):
            return datetime.combine(value, datetime.min.time()) if isinstance(value, date) else value
        elif isinstance(value, pd.Timestamp):
            return value.to_pydatetime()
        try:
            return float(value)
        except (ValueError, TypeError):
            return str(value)

    # ==============================================
    # Pestaña 1: Crear Pedido
    # ==============================================
    with tab1:
        st.subheader("Crear Nuevo Pedido")

        with st.form("nuevo_pedido_form"):
            col1, col2 = st.columns(2)
            with col1:
                # Tus campos de entrada
                cliente = st.text_input("Cliente*", key="new_cliente")
                telefono = st.text_input("Teléfono*", key="new_telefono", max_chars=15)
                club = st.text_input("Club*", key="new_club") # Es de tipo texto
                talla = st.selectbox(
                    "Talla",
                    [""] + df_listas['Talla'].dropna().unique().tolist(),
                    key="new_talla"
                )
                tela = st.selectbox(
                    "Tela",
                    [""] + df_listas['Tela'].dropna().unique().tolist(),
                    key="new_tela"
                )
                descripcion = st.text_area("Descripción", key="new_descripcion")

            with col2:
                fecha_entrada = st.date_input(
                    "Fecha entrada",
                    value=datetime.now(),
                    key="new_fecha_entrada"
                )
                fecha_salida = st.date_input(
                    "Fecha salida",
                    value=None,
                    key="new_fecha_salida"
                )
                precio = st.number_input("Precio", min_value=0.0, value=0.0, key="new_precio")
                precio_factura = st.number_input(
                    "Precio factura",
                    min_value=0.0,
                    value=0.0,
                    key="new_precio_factura"
                )
                tipo_pago = st.selectbox(
                    "Tipo de pago",
                    [""] + df_listas['Tipo de pago'].dropna().unique().tolist(),
                    key="new_tipo_pago"
                )
                adelanto = st.number_input(
                    "Adelanto",
                    min_value=0.0,
                    value=0.0,
                    key="new_adelanto"
                )
            
            # Botón de guardar
            submitted = st.form_submit_button("Guardar Pedido")

            if submitted:
                # --- CORRECCIÓN 2: VALIDACIÓN SIMPLE DE CAMPOS ---
                # Si 'club' es un texto, solo necesitamos verificar que no esté vacío
                if not cliente or not telefono or not club:
                    st.warning("Por favor, rellena todos los campos obligatorios (Cliente, Teléfono y Club).")
                else:
                    try:
                        next_id = get_next_id(df_pedidos, 'ID')

                        nueva_fila = pd.DataFrame([{
                            'ID': next_id,
                            'Cliente': cliente,
                            'Telefono': telefono,
                            'Club': club,
                            'Talla': talla,
                            'Tela': tela,
                            'Descripcion': descripcion,
                            'Fecha entrada': fecha_entrada,
                            'Fecha salida': fecha_salida,
                            'Precio': precio,
                            'Precio factura': precio_factura,
                            'Tipo de pago': tipo_pago,
                            'Adelanto': adelanto
                        }])

                        # Añadir la nueva fila al DataFrame
                        df_pedidos = pd.concat([df_pedidos, nueva_fila], ignore_index=True)

                        # Guardar el DataFrame actualizado en Firestore
                        if save_dataframe_firestore(df_pedidos, 'pedidos'):
                            st.success(f"¡Pedido {next_id} creado con éxito!")
                            st.session_state.data['df_pedidos'] = df_pedidos
                            st.rerun()
                        else:
                            st.error("Error al guardar el pedido en Firestore.")
                    except Exception as e:
                        st.error(f"Error al crear el pedido: {str(e)}")


    # ==============================================
    # Pestaña 2: Consultar Pedidos
    # ==============================================
    with tab2:
        st.subheader("Pedidos Registrados")
        
        # --- CORRECCIÓN 3: COMPROBAR SI EL DATAFRAME ESTÁ VACÍO ---
        if not df_pedidos.empty:
            # Reordenar las columnas para una mejor visualización
            columnas_disponibles = [col for col in ['ID', 'Cliente', 'Telefono', 'Club', 'Talla', 'Tela', 'Descripcion', 'Fecha entrada', 'Fecha salida', 'Precio', 'Precio factura', 'Tipo de pago', 'Adelanto'] if col in df_pedidos.columns]
            
            st.dataframe(
                df_pedidos[columnas_disponibles].sort_values('ID', ascending=False),
                height=600,
                use_container_width=True
            )
        else:
            st.info("No hay pedidos registrados. Por favor, crea un nuevo pedido en la pestaña 'Crear Pedido'.")

    # ==============================================
    # Pestaña 3: Modificar Pedido
    # ==============================================
    with tab3:
        st.subheader("Modificar Pedido Existente")
        
        pedidos_disponibles = df_pedidos.sort_values(by='ID', ascending=False)
        pedido_id_to_edit = st.selectbox(
            "Selecciona el ID del pedido a modificar",
            options=[None] + pedidos_disponibles['ID'].tolist(),
            key="edit_pedido_id"
        )

        if pedido_id_to_edit is not None:
            pedido_a_editar = df_pedidos[df_pedidos['ID'] == pedido_id_to_edit].iloc[0].to_dict()
            st.write(f"Modificando Pedido ID: {pedido_id_to_edit}")

            with st.form("modificar_pedido_form"):
                col_edit1, col_edit2 = st.columns(2)
                with col_edit1:
                    new_cliente = st.text_input("Cliente", value=pedido_a_editar.get('Cliente', ''), key="edit_cliente")
                    new_telefono = st.text_input("Teléfono", value=pedido_a_editar.get('Telefono', ''), max_chars=15, key="edit_telefono")
                    new_club = st.text_input("Club", value=pedido_a_editar.get('Club', ''), key="edit_club")
                    
                    opciones_talla = [""] + df_listas['Talla'].dropna().unique().tolist()
                    current_talla_index = opciones_talla.index(pedido_a_editar.get('Talla', '')) if pedido_a_editar.get('Talla', '') in opciones_talla else 0
                    new_talla = st.selectbox("Talla", opciones_talla, index=current_talla_index, key="edit_talla")
                    
                    opciones_tela = [""] + df_listas['Tela'].dropna().unique().tolist()
                    current_tela_index = opciones_tela.index(pedido_a_editar.get('Tela', '')) if pedido_a_editar.get('Tela', '') in opciones_tela else 0
                    new_tela = st.selectbox("Tela", opciones_tela, index=current_tela_index, key="edit_tela")
                    
                    new_descripcion = st.text_area("Descripción", value=pedido_a_editar.get('Descripcion', ''), key="edit_descripcion")

                with col_edit2:
                    current_fecha_entrada = pd.to_datetime(pedido_a_editar.get('Fecha entrada')) if pd.to_datetime(pedido_a_editar.get('Fecha entrada')) is not pd.NaT else None
                    new_fecha_entrada = st.date_input("Fecha entrada", value=current_fecha_entrada, key="edit_fecha_entrada")
                    
                    current_fecha_salida = pd.to_datetime(pedido_a_editar.get('Fecha salida')) if pd.to_datetime(pedido_a_editar.get('Fecha salida')) is not pd.NaT else None
                    new_fecha_salida = st.date_input("Fecha salida", value=current_fecha_salida, key="edit_fecha_salida")

                    new_precio = st.number_input("Precio", min_value=0.0, value=float(pedido_a_editar.get('Precio', 0.0)), key="edit_precio")
                    new_precio_factura = st.number_input("Precio factura", min_value=0.0, value=float(pedido_a_editar.get('Precio factura', 0.0)), key="edit_precio_factura")
                    
                    opciones_pago = [""] + df_listas['Tipo de pago'].dropna().unique().tolist()
                    current_pago_index = opciones_pago.index(pedido_a_editar.get('Tipo de pago', '')) if pedido_a_editar.get('Tipo de pago', '') in opciones_pago else 0
                    new_tipo_pago = st.selectbox("Tipo de pago", opciones_pago, index=current_pago_index, key="edit_tipo_pago")

                    new_adelanto = st.number_input("Adelanto", min_value=0.0, value=float(pedido_a_editar.get('Adelanto', 0.0)), key="edit_adelanto")
                
                # Botón de guardar cambios
                update_submitted = st.form_submit_button("Guardar Cambios")

                if update_submitted:
                    # Validar campos modificados
                    if not new_cliente or not new_telefono or not new_club:
                        st.warning("Por favor, rellena todos los campos obligatorios (Cliente, Teléfono y Club).")
                    else:
                        try:
                            # Encontrar el índice de la fila en el DataFrame para modificarla
                            idx_to_update = df_pedidos[df_pedidos['ID'] == pedido_id_to_edit].index[0]
                            
                            df_pedidos.loc[idx_to_update, 'Cliente'] = new_cliente
                            df_pedidos.loc[idx_to_update, 'Telefono'] = new_telefono
                            df_pedidos.loc[idx_to_update, 'Club'] = new_club
                            df_pedidos.loc[idx_to_update, 'Talla'] = new_talla
                            df_pedidos.loc[idx_to_update, 'Tela'] = new_tela
                            df_pedidos.loc[idx_to_update, 'Descripcion'] = new_descripcion
                            df_pedidos.loc[idx_to_update, 'Fecha entrada'] = new_fecha_entrada
                            df_pedidos.loc[idx_to_update, 'Fecha salida'] = new_fecha_salida
                            df_pedidos.loc[idx_to_update, 'Precio'] = new_precio
                            df_pedidos.loc[idx_to_update, 'Precio factura'] = new_precio_factura
                            df_pedidos.loc[idx_to_update, 'Tipo de pago'] = new_tipo_pago
                            df_pedidos.loc[idx_to_update, 'Adelanto'] = new_adelanto

                            # Guardar el DataFrame actualizado en Firestore
                            if save_dataframe_firestore(df_pedidos, 'pedidos'):
                                st.session_state.data['df_pedidos'] = df_pedidos
                                st.success(f"¡Pedido {pedido_id_to_edit} modificado con éxito!")
                                st.rerun()
                            else:
                                st.error("Error al guardar los cambios en Firestore.")
                        except Exception as e:
                            st.error(f"Error al modificar el pedido: {str(e)}")

    # ==============================================
    # Pestaña 4: Eliminar Pedido
    # ==============================================
    with tab4:
        st.subheader("Eliminar un Pedido")
        
        pedidos_disponibles = df_pedidos.sort_values(by='ID', ascending=False)
        del_id = st.selectbox(
            "Selecciona el ID del pedido a eliminar",
            options=[None] + pedidos_disponibles['ID'].tolist(),
            key="delete_pedido_id"
        )
        
        if del_id is not None:
            pedido_a_eliminar = df_pedidos[df_pedidos['ID'] == del_id]
            st.warning("¡ATENCIÓN! Estás a punto de eliminar el siguiente pedido. Esta acción no se puede deshacer.")
            
            st.dataframe(pd.DataFrame({
                "ID": [pedido_a_eliminar['ID'].iloc[0]],
                "Cliente": [pedido_a_eliminar['Cliente'].iloc[0]],
                "Club": [pedido_a_eliminar['Club'].iloc[0]],
                "Telefono": [pedido_a_eliminar['Telefono'].iloc[0]],
                "Fecha entrada": [str(pedido_a_eliminar['Fecha entrada'].iloc[0])],
                "Precio": [pedido_a_eliminar['Precio'].iloc[0]]
            }))
            
            confirmacion = st.checkbox("Confirmo que deseo eliminar este pedido permanentemente", key="confirm_delete")
            
            if confirmacion:
                if st.button("Eliminar Definitivamente", type="primary", key="confirm_delete_button"):
                    try:
                        # Eliminar de DataFrame
                        df_pedidos = df_pedidos[df_pedidos['ID'] != del_id]
                        
                        # Eliminar de Firestore
                        doc_id = pedido_a_eliminar['id_documento_firestore'].iloc[0]
                        if delete_document_firestore('pedidos', doc_id):
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