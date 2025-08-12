import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils.firestore_utils import get_next_id, save_dataframe_firestore, delete_document_firestore

def show_pedidos_page(df_pedidos, df_listas):
    tab1, tab2, tab3, tab4 = st.tabs(["Crear Pedido", "Consultar Pedidos", "Modificar Pedido", "Eliminar Pedido"])

    # ==============================================
    # Pestaña 1: Crear Pedido
    # ==============================================
    with tab1:
        st.subheader("Crear Nuevo Pedido")
        
        with st.form("nuevo_pedido_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                producto = st.selectbox("Producto*", [""] + df_listas['Producto'].dropna().unique().tolist(), key="new_producto")
                cliente = st.text_input("Cliente*", key="new_cliente")
                telefono = st.text_input("Teléfono*", key="new_telefono")
                club = st.text_input("Club", key="new_club")
                talla = st.selectbox("Talla", [""] + df_listas['Talla'].dropna().unique().tolist(), key="new_talla")
                tela = st.selectbox("Tela", [""] + df_listas['Tela'].dropna().unique().tolist(), key="new_tela")
                descripcion = st.text_area("Descripción", key="new_descripcion")
            
            with col2:
                fecha_entrada_valor = st.date_input("Fecha entrada*", value=datetime.now().date(), key="new_fecha_entrada")
                fecha_salida_valor = st.date_input("Fecha salida", value=None, key="new_fecha_salida")
                precio = st.number_input("Precio*", min_value=0.0, value=0.0, key="new_precio")
                precio_factura = st.number_input("Precio factura", min_value=0.0, value=0.0, key="new_precio_factura")
                tipo_pago = st.selectbox("Tipo de pago", [""] + df_listas['Tipo de pago'].dropna().unique().tolist(), key="new_tipo_pago")
                adelanto = st.number_input("Adelanto", min_value=0.0, value=0.0, key="new_adelanto")
                observaciones = st.text_area("Observaciones", key="new_observaciones")
            
            st.write("**Estado del pedido:**")
            estado_cols = st.columns(5)
            with estado_cols[0]:
                empezado = st.checkbox("Empezado", value=False, key="new_empezado")
            with estado_cols[1]:
                terminado = st.checkbox("Terminado", value=False, key="new_terminado")
            with estado_cols[2]:
                cobrado = st.checkbox("Cobrado", value=False, key="new_cobrado")
            with estado_cols[3]:
                retirado = st.checkbox("Retirado", value=False, key="new_retirado")
            with estado_cols[4]:
                pendiente = st.checkbox("Pendiente", value=True, key="new_pendiente")
            
            if st.form_submit_button("Guardar Nuevo Pedido"):
                if not cliente or not telefono or not producto or precio <= 0:
                    st.error("Por favor complete los campos obligatorios (*).")
                else:
                    try:
                        new_id = get_next_id(df_pedidos, 'ID')
                        new_pedido = {
                            'ID': new_id,
                            'Producto': producto if producto else None,
                            'Cliente': cliente,
                            'Telefono': telefono,
                            'Club': club if club else None,
                            'Talla': talla if talla else None,
                            'Tela': tela if tela else None,
                            'Breve Descripción': descripcion if descripcion else None,
                            'Fecha entrada': fecha_entrada_valor,
                            'Fecha Salida': fecha_salida_valor,
                            'Precio': precio,
                            'Precio Factura': precio_factura,
                            'Tipo de pago': tipo_pago if tipo_pago else None,
                            'Adelanto': adelanto,
                            'Observaciones': observaciones if observaciones else None,
                            'Inicio Trabajo': empezado,
                            'Trabajo Terminado': terminado,
                            'Cobrado': cobrado,
                            'Retirado': retirado,
                            'Pendiente': pendiente,
                            'id_documento_firestore': None
                        }
                        
                        df_pedidos_updated = pd.concat([df_pedidos, pd.DataFrame([new_pedido])], ignore_index=True)
                        
                        if save_dataframe_firestore(df_pedidos_updated, 'pedidos'):
                            st.success(f"Pedido {new_id} creado correctamente! ✅")
                            st.session_state.data['df_pedidos'] = df_pedidos_updated
                            st.rerun()
                        else:
                            st.error("Error al crear el pedido. ❌")
                    except Exception as e:
                        st.error(f"Error inesperado al procesar el pedido: {e} ⚠️")
                        st.exception(e)
    
    # ==============================================
    # Pestaña 2: Consultar Pedidos
    # ==============================================
    with tab2:
        st.subheader("Consultar Pedidos")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtro_cliente = st.text_input("Filtrar por cliente")
        with col_f2:
            filtro_producto = st.selectbox(
                "Filtrar por producto",
                [""] + df_listas['Producto'].dropna().unique().tolist() if 'Producto' in df_listas.columns else [""]
            )
        with col_f3:
            filtro_estado = st.selectbox(
                "Filtrar por estado",
                ["", "Pendiente", "Empezado", "Terminado", "Cobrado", "Retirado"]
            )
        
        df_filtrado = df_pedidos.copy()
        if filtro_cliente:
            df_filtrado = df_filtrado[df_filtrado['Cliente'].str.contains(filtro_cliente, case=False, na=False)]
        if filtro_producto:
            df_filtrado = df_filtrado[df_filtrado['Producto'] == filtro_producto]
        if filtro_estado:
            if filtro_estado == "Pendiente":
                df_filtrado = df_filtrado[df_filtrado['Pendiente'] == True]
            elif filtro_estado == "Empezado":
                df_filtrado = df_filtrado[df_filtrado['Inicio Trabajo'] == True]
            elif filtro_estado == "Terminado":
                df_filtrado = df_filtrado[df_filtrado['Trabajo Terminado'] == True]
            elif filtro_estado == "Cobrado":
                df_filtrado = df_filtrado[df_filtrado['Cobrado'] == True]
            elif filtro_estado == "Retirado":
                df_filtrado = df_filtrado[df_filtrado['Retirado'] == True]
        
        if not df_filtrado.empty:
            st.dataframe(
                df_filtrado[[
                    'ID', 'Producto', 'Cliente', 'Club', 'Telefono', 
                    'Fecha entrada', 'Fecha Salida', 'Precio', 'Pendiente',
                    'Inicio Trabajo', 'Trabajo Terminado', 'Cobrado', 'Retirado'
                ]].sort_values('ID', ascending=False),
                height=500, use_container_width=True
            )
        else:
            st.info("No hay pedidos para mostrar con los filtros aplicados.")
    
    # ==============================================
    # Pestaña 3: Modificar Pedido
    # ==============================================
    with tab3:
        st.subheader("Modificar Pedido Existente")
        
        mod_id_input = st.number_input("ID del pedido a modificar:", min_value=1, step=1, key="modify_id_input")
        
        if st.button("Cargar Pedido", key="load_pedido_button"):
            if 'ID' in df_pedidos.columns:
                df_pedidos['ID'] = pd.to_numeric(df_pedidos['ID'], errors='coerce')
                pedido = df_pedidos[df_pedidos['ID'] == mod_id_input]
                if not pedido.empty:
                    st.session_state.pedido_a_modificar = pedido.iloc[0].to_dict()
                    st.success(f"Pedido {mod_id_input} cargado para modificación.")
                else:
                    st.warning(f"No existe un pedido con ID {mod_id_input}.")
                    st.session_state.pedido_a_modificar = None
            else:
                st.error("La columna 'ID' no se encuentra en el DataFrame de pedidos.")
                st.session_state.pedido_a_modificar = None
        
        if 'pedido_a_modificar' in st.session_state and st.session_state.pedido_a_modificar is not None:
            pedido = st.session_state.pedido_a_modificar
            
            with st.form("modificar_pedido_form"):
                col1_mod, col2_mod = st.columns(2)
                
                with col1_mod:
                    st.text_input("ID", value=pedido.get('ID', ''), disabled=True, key="mod_display_id")
                    producto = st.selectbox(
                        "Producto*",
                        [""] + df_listas['Producto'].dropna().unique().tolist(),
                        index= (df_listas['Producto'].dropna().unique().tolist().index(pedido.get('Producto')) + 1) if pedido.get('Producto') in df_listas['Producto'].dropna().unique().tolist() else 0,
                        key="mod_producto"
                    )
                    cliente = st.text_input("Cliente*", value=pedido.get('Cliente', ''), key="mod_cliente")
                    telefono = st.text_input("Teléfono*", value=pedido.get('Telefono', ''), key="mod_telefono")
                    club = st.text_input("Club", value=pedido.get('Club', ''), key="mod_club")
                    talla = st.selectbox(
                        "Talla",
                        [""] + df_listas['Talla'].dropna().unique().tolist(),
                        index= (df_listas['Talla'].dropna().unique().tolist().index(pedido.get('Talla')) + 1) if pedido.get('Talla') in df_listas['Talla'].dropna().unique().tolist() else 0,
                        key="mod_talla"
                    )
                    tela = st.selectbox(
                        "Tela",
                        [""] + df_listas['Tela'].dropna().unique().tolist(),
                        index= (df_listas['Tela'].dropna().unique().tolist().index(pedido.get('Tela')) + 1) if pedido.get('Tela') in df_listas['Tela'].dropna().unique().tolist() else 0,
                        key="mod_tela"
                    )
                    descripcion = st.text_area("Descripción", value=pedido.get('Breve Descripción', ''), key="mod_descripcion")
                
                with col2_mod:
                    fecha_entrada_val = pedido.get('Fecha entrada')
                    fecha_entrada = st.date_input(
                        "Fecha entrada*", 
                        value=fecha_entrada_val if isinstance(fecha_entrada_val, (date, datetime)) else datetime.now().date(),
                        key="mod_fecha_entrada"
                    )
                    fecha_salida_val = pedido.get('Fecha Salida')
                    fecha_salida = st.date_input(
                        "Fecha salida", 
                        value=fecha_salida_val if isinstance(fecha_salida_val, (date, datetime)) else None,
                        key="mod_fecha_salida"
                    )
                    precio = st.number_input("Precio*", min_value=0.0, value=float(pedido.get('Precio', 0.0)), key="mod_precio")
                    precio_factura = st.number_input("Precio factura", min_value=0.0, value=float(pedido.get('Precio Factura', 0.0)), key="mod_precio_factura")
                    tipo_pago = st.selectbox("Tipo de pago", [""] + df_listas['Tipo de pago'].dropna().unique().tolist(), index= (df_listas['Tipo de pago'].dropna().unique().tolist().index(pedido.get('Tipo de pago')) + 1) if pedido.get('Tipo de pago') in df_listas['Tipo de pago'].dropna().unique().tolist() else 0, key="mod_tipo_pago")
                    adelanto = st.number_input("Adelanto", min_value=0.0, value=float(pedido.get('Adelanto', 0.0)), key="mod_adelanto")
                    observaciones = st.text_area("Observaciones", value=pedido.get('Observaciones', ''), key="mod_observaciones")
                
                st.write("**Estado del pedido:**")
                estado_cols_mod = st.columns(5)
                with estado_cols_mod[0]:
                    empezado = st.checkbox("Empezado", value=pedido.get('Inicio Trabajo', False), key="mod_empezado")
                with estado_cols_mod[1]:
                    terminado = st.checkbox("Terminado", value=pedido.get('Trabajo Terminado', False), key="mod_terminado")
                with estado_cols_mod[2]:
                    cobrado = st.checkbox("Cobrado", value=pedido.get('Cobrado', False), key="mod_cobrado")
                with estado_cols_mod[3]:
                    retirado = st.checkbox("Retirado", value=pedido.get('Retirado', False), key="mod_retirado")
                with estado_cols_mod[4]:
                    pendiente = st.checkbox("Pendiente", value=pedido.get('Pendiente', False), key="mod_pendiente")
                
                if st.form_submit_button("Guardar Cambios"):
                    if not cliente or not telefono or precio <= 0:
                        st.error("Por favor complete los campos obligatorios (*).")
                    else:
                        try:
                            # Encontrar el índice del DataFrame
                            index_to_edit = df_pedidos[df_pedidos['ID'] == mod_id_input].index
                            
                            if not index_to_edit.empty:
                                index = index_to_edit[0]
                                
                                # Actualizar los valores en el DataFrame
                                df_pedidos.loc[index, 'Producto'] = producto if producto else None
                                df_pedidos.loc[index, 'Cliente'] = cliente
                                df_pedidos.loc[index, 'Telefono'] = telefono
                                df_pedidos.loc[index, 'Club'] = club if club else None
                                df_pedidos.loc[index, 'Talla'] = talla if talla else None
                                df_pedidos.loc[index, 'Tela'] = tela if tela else None
                                df_pedidos.loc[index, 'Breve Descripción'] = descripcion if descripcion else None
                                df_pedidos.loc[index, 'Fecha entrada'] = fecha_entrada
                                df_pedidos.loc[index, 'Fecha Salida'] = fecha_salida
                                df_pedidos.loc[index, 'Precio'] = precio
                                df_pedidos.loc[index, 'Precio Factura'] = precio_factura
                                df_pedidos.loc[index, 'Tipo de pago'] = tipo_pago if tipo_pago else None
                                df_pedidos.loc[index, 'Adelanto'] = adelanto
                                df_pedidos.loc[index, 'Observaciones'] = observaciones if observaciones else None
                                df_pedidos.loc[index, 'Inicio Trabajo'] = empezado
                                df_pedidos.loc[index, 'Trabajo Terminado'] = terminado
                                df_pedidos.loc[index, 'Cobrado'] = cobrado
                                df_pedidos.loc[index, 'Retirado'] = retirado
                                df_pedidos.loc[index, 'Pendiente'] = pendiente
                                
                                if save_dataframe_firestore(df_pedidos, 'pedidos'):
                                    st.success(f"Pedido {pedido['ID']} actualizado correctamente! ✅")
                                    st.session_state.data['df_pedidos'] = df_pedidos
                                    del st.session_state.pedido_a_modificar
                                    st.rerun()
                                else:
                                    st.error("Error al actualizar el pedido en Firestore. ❌")
                            else:
                                st.error("Error: No se encontró el pedido en el DataFrame para actualizar.")
                        except Exception as e:
                            st.error(f"Error inesperado al procesar la modificación del pedido: {e} ⚠️")
                            st.exception(e)
    
    # ==============================================
    # Pestaña 4: Eliminar Pedido
    # ==============================================
    with tab4:
        st.subheader("Eliminar Pedido")
        
        if not df_pedidos.empty:
            pedidos_ids_disponibles = sorted(df_pedidos['ID'].tolist(), reverse=True)
            
            pedido_a_eliminar_id = st.selectbox(
                "Selecciona el ID del pedido a eliminar",
                options=pedidos_ids_disponibles,
                key="delete_pedido_id_select"
            )

            if st.button("Confirmar Eliminación", key="delete_button"):
                doc_id_firestore_to_delete = df_pedidos[df_pedidos['ID'] == pedido_a_eliminar_id]['id_documento_firestore'].iloc[0]
                
                if delete_document_firestore('pedidos', doc_id_firestore_to_delete):
                    df_pedidos_updated = df_pedidos[df_pedidos['ID'] != pedido_a_eliminar_id].reset_index(drop=True)
                    st.session_state.data['df_pedidos'] = df_pedidos_updated
                    st.success(f"Pedido ID {pedido_a_eliminar_id} eliminado exitosamente! 🗑️")
                    st.rerun()
                else:
                    st.error(f"Error al eliminar el pedido ID {pedido_a_eliminar_id} de Firestore. ❌")
        else:
            st.info("No hay pedidos para eliminar.")