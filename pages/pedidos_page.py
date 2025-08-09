with tab3:  # Pestaña Modificar Pedido
    st.subheader("Modificar Pedido Existente")
    
    # Selección del pedido a modificar
    mod_id = st.number_input("ID del pedido a modificar:", min_value=1, key="modify_id_input")
    
    if st.button("Cargar Pedido", key="load_pedido_button"):
        pedido = df_pedidos[df_pedidos['ID'] == mod_id]
        if not pedido.empty:
            st.session_state.pedido_a_modificar = pedido.iloc[0].to_dict()
            st.success(f"Pedido {mod_id} cargado para modificación")
        else:
            st.warning(f"No existe un pedido con ID {mod_id}")
            st.session_state.pedido_a_modificar = None
    
    if 'pedido_a_modificar' in st.session_state and st.session_state.pedido_a_modificar:
        pedido = st.session_state.pedido_a_modificar
        
        with st.form("modificar_pedido_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input("ID", value=pedido['ID'], disabled=True, key="mod_id")
                producto = st.selectbox(
                    "Producto",
                    [""] + df_listas['Producto'].dropna().unique().tolist(),
                    index=0 if pd.isna(pedido['Producto']) else df_listas['Producto'].tolist().index(pedido['Producto']),
                    key="mod_producto"
                )
                cliente = st.text_input("Cliente*", value=pedido['Cliente'], key="mod_cliente")
                telefono = st.text_input("Teléfono*", value=pedido['Telefono'], key="mod_telefono")
                club = st.text_input("Club", value=pedido['Club'], key="mod_club")
                talla = st.selectbox(
                    "Talla",
                    [""] + df_listas['Talla'].dropna().unique().tolist(),
                    index=0 if pd.isna(pedido['Talla']) else df_listas['Talla'].tolist().index(pedido['Talla']),
                    key="mod_talla"
                )
                tela = st.selectbox(
                    "Tela",
                    [""] + df_listas['Tela'].dropna().unique().tolist(),
                    index=0 if pd.isna(pedido['Tela']) else df_listas['Tela'].tolist().index(pedido['Tela']),
                    key="mod_tela"
                )
                descripcion = st.text_area("Descripción", value=pedido['Breve Descripción'], key="mod_descripcion")
            
            with col2:
                fecha_entrada = st.date_input(
                    "Fecha entrada*", 
                    value=pedido['Fecha entrada'] if not pd.isna(pedido['Fecha entrada']) else datetime.now(),
                    key="mod_fecha_entrada"
                )
                fecha_salida = st.date_input(
                    "Fecha salida", 
                    value=pedido['Fecha Salida'] if not pd.isna(pedido['Fecha Salida']) else None,
                    key="mod_fecha_salida"
                )
                precio = st.number_input("Precio*", min_value=0.0, value=float(pedido['Precio']), key="mod_precio")
                precio_factura = st.number_input(
                    "Precio factura", 
                    min_value=0.0, 
                    value=float(pedido['Precio Factura']) if not pd.isna(pedido['Precio Factura']) else 0.0,
                    key="mod_precio_factura"
                )
                tipo_pago = st.selectbox(
                    "Tipo de pago",
                    [""] + df_listas['Tipo de pago'].dropna().unique().tolist(),
                    index=0 if pd.isna(pedido['Tipo de pago']) else df_listas['Tipo de pago'].tolist().index(pedido['Tipo de pago']),
                    key="mod_tipo_pago"
                )
                adelanto = st.number_input(
                    "Adelanto", 
                    min_value=0.0, 
                    value=float(pedido['Adelanto']) if not pd.isna(pedido['Adelanto']) else 0.0,
                    key="mod_adelanto"
                )
                observaciones = st.text_area("Observaciones", value=pedido['Observaciones'], key="mod_observaciones")
            
            # Estado del pedido
            st.write("**Estado del pedido:**")
            estado_cols = st.columns(5)
            with estado_cols[0]:
                empezado = st.checkbox("Empezado", value=pedido['Inicio Trabajo'], key="mod_empezado")
            with estado_cols[1]:
                terminado = st.checkbox("Terminado", value=pedido['Trabajo Terminado'], key="mod_terminado")
            with estado_cols[2]:
                cobrado = st.checkbox("Cobrado", value=pedido['Cobrado'], key="mod_cobrado")
            with estado_cols[3]:
                retirado = st.checkbox("Retirado", value=pedido['Retirado'], key="mod_retirado")
            with estado_cols[4]:
                pendiente = st.checkbox("Pendiente", value=pedido['Pendiente'], key="mod_pendiente")
            
            if st.form_submit_button("Guardar Cambios"):
                # Actualizar los datos del pedido
                updated_pedido = {
                    'ID': mod_id,
                    'Producto': producto or None,
                    'Cliente': cliente,
                    'Telefono': telefono,
                    'Club': club,
                    'Talla': talla or None,
                    'Tela': tela or None,
                    'Breve Descripción': descripcion,
                    'Fecha entrada': fecha_entrada,
                    'Fecha Salida': fecha_salida if fecha_salida else None,
                    'Precio': float(precio),
                    'Precio Factura': float(precio_factura) if precio_factura else None,
                    'Tipo de pago': tipo_pago or None,
                    'Adelanto': float(adelanto) if adelanto else None,
                    'Observaciones': observaciones,
                    'Inicio Trabajo': empezado,
                    'Trabajo Terminado': terminado,
                    'Cobrado': cobrado,
                    'Retirado': retirado,
                    'Pendiente': pendiente,
                    'id_documento_firestore': pedido['id_documento_firestore']
                }
                
                # Actualizar el DataFrame
                idx = df_pedidos[df_pedidos['ID'] == mod_id].index[0]
                df_pedidos.loc[idx] = updated_pedido
                
                # Guardar en Firestore
                if save_dataframe_firestore(df_pedidos, 'pedidos'):
                    st.success(f"Pedido {mod_id} actualizado correctamente!")
                    st.session_state.pedido_a_modificar = None
                    st.rerun()
                else:
                    st.error("Error al actualizar el pedido")