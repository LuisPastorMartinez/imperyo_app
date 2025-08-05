def view_pedidos():
    st.header("📋 Gestión de Pedidos")
    tab1, tab2, tab3 = st.tabs(["Nuevo Pedido", "Editar", "Buscar"])
    
    with tab1:
        with st.form("nuevo_pedido", clear_on_submit=True):
            st.subheader("Nuevo Pedido")
            
            # Generar ID automático
            next_id = get_next_id(st.session_state.data['df_pedidos'], 'ID')
            
            # --- PRIMERA FILA (4 campos principales) ---
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.text_input("ID", value=next_id, disabled=True, key="nuevo_id")
            with col2:
                cliente = st.text_input("Cliente*", key="nuevo_cliente")
            with col3:
                telefono = st.text_input("Teléfono", key="nuevo_telefono")
            with col4:
                producto = st.selectbox(
                    "Producto*", 
                    options=st.session_state.data['df_listas']['Producto'].dropna().unique(),
                    key="nuevo_producto"
                )
            
            # --- SEGUNDA FILA (4 campos) ---
            col5, col6, col7, col8 = st.columns(4)
            with col5:
                club = st.text_input("Club", key="nuevo_club")
            with col6:
                talla = st.selectbox(
                    "Talla", 
                    options=st.session_state.data['df_listas']['Talla'].dropna().unique(),
                    key="nuevo_talla"
                )
            with col7:
                tela = st.selectbox(
                    "Tela", 
                    options=st.session_state.data['df_listas']['Tela'].dropna().unique(),
                    key="nuevo_tela"
                )
            with col8:
                breve_desc = st.text_input("Breve Descripción", key="nuevo_desc")
            
            # --- TERCERA FILA (Fechas y precios) ---
            col9, col10, col11, col12 = st.columns(4)
            with col9:
                fecha_entrada = st.date_input("Fecha Entrada*", key="nuevo_fecha_entrada")
            with col10:
                fecha_salida = st.date_input("Fecha Salida", key="nuevo_fecha_salida")
            with col11:
                precio = st.number_input("Precio*", min_value=0.0, format="%.2f", key="nuevo_precio")
            with col12:
                precio_factura = st.number_input("Precio Factura", min_value=0.0, format="%.2f", key="nuevo_precio_factura")
            
            # --- CUARTA FILA (Pago y observaciones) ---
            col13, col14 = st.columns([1, 3])
            with col13:
                tipo_pago = st.selectbox(
                    "Tipo de Pago", 
                    options=st.session_state.data['df_listas']['Tipo de pago'].dropna().unique(),
                    key="nuevo_tipo_pago"
                )
                adelanto = st.number_input("Adelanto", min_value=0.0, format="%.2f", key="nuevo_adelanto")
            with col14:
                observaciones = st.text_area("Observaciones", height=100, key="nuevo_observaciones")
            
            # --- QUINTA FILA (Estado del pedido) ---
            st.write("**Estado del Pedido:**")
            estado_cols = st.columns(5)
            with estado_cols[0]:
                empezado = st.checkbox("Empezado", key="nuevo_empezado")
            with estado_cols[1]:
                terminado = st.checkbox("Terminado", key="nuevo_terminado")
            with estado_cols[2]:
                cobrado = st.checkbox("Cobrado", key="nuevo_cobrado")
            with estado_cols[3]:
                retirado = st.checkbox("Retirado", key="nuevo_retirado")
            with estado_cols[4]:
                pendiente = st.checkbox("Pendiente", key="nuevo_pendiente")
            
            # Botón de envío
            if st.form_submit_button("💾 Guardar Pedido"):
                if not cliente or not producto or not precio:
                    st.error("Los campos marcados con * son obligatorios")
                else:
                    nuevo_pedido = {
                        'ID': next_id,
                        'Cliente': cliente,
                        'Teléfono': telefono,
                        'Producto': producto,
                        'Club': club,
                        'Talla': talla,
                        'Tela': tela,
                        'Breve Descripción': breve_desc,
                        'Fecha Entrada': fecha_entrada,
                        'Fecha Salida': fecha_salida if fecha_salida else None,
                        'Precio': precio,
                        'Precio Factura': precio_factura if precio_factura else None,
                        'Tipo de pago': tipo_pago,
                        'Adelanto': adelanto if adelanto else None,
                        'Observaciones': observaciones,
                        'Inicio Trabajo': empezado,
                        'Trabajo Terminado': terminado,
                        'Cobrado': cobrado,
                        'Retirado': retirado,
                        'Pendiente': pendiente
                    }
                    
                    if save_dataframe_firestore(pd.DataFrame([nuevo_pedido]), 'pedidos'):
                        st.success("✅ Pedido guardado correctamente!")
                        st.session_state.data['df_pedidos'] = load_dataframes_firestore()['df_pedidos']
                    else:
                        st.error("❌ Error al guardar el pedido")