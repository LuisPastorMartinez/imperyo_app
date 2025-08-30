# pages/pedidos_page.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils import get_next_id, save_dataframe_firestore, delete_document_firestore, convert_to_firestore_types

def show_pedidos_page(df_pedidos, df_listas):
    # Definir las 4 pestañas
    tab1, tab2, tab3, tab4 = st.tabs(["Crear Pedido", "Consultar Pedidos", "Modificar Pedido", "Eliminar Pedido"])
    
    # ==============================================
    # Pestaña 1: Crear Pedido
    # ==============================================
    with tab1:
        st.subheader("Crear Nuevo Pedido")
        
        with st.form("nuevo_pedido_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                producto = st.selectbox(
                    "Producto*",
                    [""] + df_listas['Producto'].dropna().unique().tolist(),
                    key="new_producto"
                )
                cliente = st.text_input("Cliente*", key="new_cliente")
                telefono = st.text_input("Teléfono*", key="new_telefono", max_chars=15)
                club = st.text_input("Club*", key="new_club")
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
                    value=datetime.now().date(),
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
                observaciones = st.text_area("Observaciones", key="new_observaciones")
            
            # Estado del pedido
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
                pendiente = st.checkbox("Pendiente", value=False, key="new_pendiente")
            
            if st.form_submit_button("Guardar Nuevo Pedido"):
                if not cliente or not telefono or not producto or not club:
                    st.error("Por favor complete los campos obligatorios (*)")
                else:
                    new_id = get_next_id(df_pedidos, 'ID')
                    new_pedido = {
                        'ID': new_id,
                        'Producto': producto,
                        'Cliente': cliente,
                        'Telefono': telefono,
                        'Club': club,
                        'Talla': talla,
                        'Tela': tela,
                        'Breve Descripción': descripcion,
                        'Fecha entrada': fecha_entrada,
                        'Fecha Salida': fecha_salida,
                        'Precio': precio,
                        'Precio Factura': precio_factura,
                        'Tipo de pago': tipo_pago,
                        'Adelanto': adelanto,
                        'Observaciones': observaciones,
                        'Inicio Trabajo': empezado,
                        'Trabajo Terminado': terminado,
                        'Cobrado': cobrado,
                        'Retirado': retirado,
                        'Pendiente': pendiente,
                        'id_documento_firestore': None
                    }
                    
                    new_pedido_df = pd.DataFrame([new_pedido])
                    df_pedidos_updated = pd.concat([df_pedidos, new_pedido_df], ignore_index=True)
                    
                    if save_dataframe_firestore(df_pedidos_updated, 'pedidos'):
                        st.success(f"Pedido {new_id} creado correctamente!")
                        st.session_state.data['df_pedidos'] = df_pedidos_updated
                        st.rerun()
                    else:
                        st.error("Error al crear el pedido")

    # ==============================================
    # Pestaña 2: Consultar Pedidos
    # ==============================================
    with tab2:
        st.subheader("Consultar Pedidos")
        
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        with col_f1:
            filtro_cliente = st.text_input("Filtrar por cliente")
        with col_f2:
            filtro_club = st.text_input("Filtrar por club")
        with col_f3:
            filtro_telefono = st.text_input("Filtrar por teléfono")
        with col_f4:
            filtro_estado = st.selectbox(
                "Filtrar por estado",
                options=["", "Pendiente", "Empezado", "Terminado", "Retirado"],
                key="filtro_estado_consulta"
            )
        
        df_filtrado = df_pedidos.copy()
        
        if filtro_cliente:
            df_filtrado = df_filtrado[
                df_filtrado['Cliente'].str.contains(filtro_cliente, case=False, na=False)
            ]
        
        if filtro_club:
            df_filtrado = df_filtrado[
                df_filtrado['Club'].str.contains(filtro_club, case=False, na=False)
            ]
        
        if filtro_telefono:
            df_filtrado = df_filtrado[
                df_filtrado['Telefono'].astype(str).str.contains(filtro_telefono, na=False)
            ]
        
        if filtro_estado:
            if filtro_estado == "Pendiente":
                df_filtrado = df_filtrado[df_filtrado['Pendiente'] == True]
            elif filtro_estado == "Empezado":
                df_filtrado = df_filtrado[df_filtrado['Inicio Trabajo'] == True]
            elif filtro_estado == "Terminado":
                df_filtrado = df_filtrado[df_filtrado['Trabajo Terminado'] == True]
            elif filtro_estado == "Retirado":
                df_filtrado = df_filtrado[df_filtrado['Retirado'] == True]
        
        if not df_filtrado.empty:
            df_display = df_filtrado.copy()
            date_cols = ['Fecha entrada', 'Fecha Salida']
            for col in date_cols:
                if col in df_display.columns:
                    df_display[col] = df_display[col].dt.strftime('%Y-%m-%d')
            
            columnas_mostrar = [
                'ID', 'Producto', 'Cliente', 'Club', 'Telefono',
                'Fecha entrada', 'Fecha Salida', 'Precio',
                'Pendiente', 'Inicio Trabajo', 'Trabajo Terminado', 'Retirado'
            ]
            
            columnas_disponibles = [col for col in columnas_mostrar if col in df_display.columns]
            
            st.dataframe(
                df_display[columnas_disponibles].sort_values('ID', ascending=False),
                height=600,
                use_container_width=True
            )
            
            st.caption(f"Mostrando {len(df_filtrado)} de {len(df_pedidos)} pedidos")
        else:
            st.info("No se encontraron pedidos con los filtros aplicados")

    # ==============================================
    # Pestaña 3: Modificar Pedido
    # ==============================================
    with tab3:
        st.subheader("Modificar Pedido Existente")
        
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
                
                # Opciones para selectbox
                opciones_producto = [""] + df_listas['Producto'].dropna().unique().tolist()
                opciones_talla = [""] + df_listas['Talla'].dropna().unique().tolist()
                opciones_tela = [""] + df_listas['Tela'].dropna().unique().tolist()
                opciones_pago = [""] + df_listas['Tipo de pago'].dropna().unique().tolist()
                
                # Índices predeterminados
                idx_producto = opciones_producto.index(pedido['Producto']) if pedido['Producto'] in opciones_producto else 0
                idx_talla = opciones_talla.index(pedido['Talla']) if pedido['Talla'] in opciones_talla else 0
                idx_tela = opciones_tela.index(pedido['Tela']) if pedido['Tela'] in opciones_tela else 0
                idx_pago = opciones_pago.index(pedido['Tipo de pago']) if pedido['Tipo de pago'] in opciones_pago else 0
                
                with col1:
                    st.text_input("ID", value=pedido['ID'], disabled=True, key="mod_id")
                    producto = st.selectbox(
                        "Producto*",
                        options=opciones_producto,
                        index=idx_producto,
                        key="mod_producto"
                    )
                    cliente = st.text_input("Cliente*", value=pedido['Cliente'], key="mod_cliente")
                    telefono = st.text_input("Teléfono*", value=pedido['Telefono'], key="mod_telefono")
                    club = st.text_input("Club*", value=pedido['Club'], key="mod_club")
                    talla = st.selectbox(
                        "Talla",
                        options=opciones_talla,
                        index=idx_talla,
                        key="mod_talla"
                    )
                    tela = st.selectbox(
                        "Tela",
                        options=opciones_tela,
                        index=idx_tela,
                        key="mod_tela"
                    )
                    descripcion = st.text_area("Descripción", value=pedido['Breve Descripción'], key="mod_descripcion")
                
                with col2:
                    fecha_entrada_value = pedido['Fecha entrada'].date() if isinstance(pedido['Fecha entrada'], datetime) else datetime.now().date()
                    fecha_entrada = st.date_input(
                        "Fecha entrada*", 
                        value=fecha_entrada_value,
                        key="mod_fecha_entrada"
                    )
                    
                    fecha_salida_value = pedido['Fecha Salida'].date() if isinstance(pedido['Fecha Salida'], datetime) else None
                    fecha_salida = st.date_input(
                        "Fecha salida", 
                        value=fecha_salida_value,
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
                        options=opciones_pago,
                        index=idx_pago,
                        key="mod_tipo_pago"
                    )
                    adelanto = st.number_input(
                        "Adelanto", 
                        min_value=0.0, 
                        value=float(pedido['Adelanto']) if not pd.isna(pedido['Adelanto']) else 0.0,
                        key="mod_adelanto"
                    )
                    observaciones = st.text_area("Observaciones", value=pedido['Observaciones'], key="mod_observaciones")
                
                st.write("**Estado del pedido:**")
                estado_cols = st.columns(5)
                with estado_cols[0]:
                    empezado = st.checkbox("Empezado", value=bool(pedido['Inicio Trabajo']), key="mod_empezado")
                with estado_cols[1]:
                    terminado = st.checkbox("Terminado", value=bool(pedido['Trabajo Terminado']), key="mod_terminado")
                with estado_cols[2]:
                    cobrado = st.checkbox("Cobrado", value=bool(pedido['Cobrado']), key="mod_cobrado")
                with estado_cols[3]:
                    retirado = st.checkbox("Retirado", value=bool(pedido['Retirado']), key="mod_retirado")
                with estado_cols[4]:
                    pendiente = st.checkbox("Pendiente", value=bool(pedido['Pendiente']), key="mod_pendiente")
                
                if st.form_submit_button("Guardar Cambios"):
                    if not cliente or not telefono or not producto or not club:
                        st.error("Por favor complete los campos obligatorios (*)")
                    else:
                        updated_pedido = {
                            'ID': mod_id,
                            'Producto': producto,
                            'Cliente': cliente,
                            'Telefono': telefono,
                            'Club': club,
                            'Talla': talla,
                            'Tela': tela,
                            'Breve Descripción': descripcion,
                            'Fecha entrada': fecha_entrada,
                            'Fecha Salida': fecha_salida,
                            'Precio': precio,
                            'Precio Factura': precio_factura,
                            'Tipo de pago': tipo_pago,
                            'Adelanto': adelanto,
                            'Observaciones': observaciones,
                            'Inicio Trabajo': empezado,
                            'Trabajo Terminado': terminado,
                            'Cobrado': cobrado,
                            'Retirado': retirado,
                            'Pendiente': pendiente,
                            'id_documento_firestore': pedido['id_documento_firestore']
                        }
                        
                        idx = df_pedidos[df_pedidos['ID'] == mod_id].index[0]
                        df_pedidos.loc[idx] = updated_pedido
                        
                        if save_dataframe_firestore(df_pedidos, 'pedidos'):
                            st.success(f"Pedido {mod_id} actualizado correctamente!")
                            st.session_state.pedido_a_modificar = None
                            st.session_state.data['df_pedidos'] = df_pedidos
                            st.rerun()
                        else:
                            st.error("Error al actualizar el pedido")

    # ==============================================
    # Pestaña 4: Eliminar Pedido
    # ==============================================
    with tab4:
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
                        doc_id = pedido['id_documento_firestore']
                        if delete_document_firestore('pedidos', doc_id):
                            st.session_state.data['df_pedidos'] = st.session_state.data['df_pedidos'][st.session_state.data['df_pedidos']['ID'] != del_id].copy()
                            st.success(f"Pedido {del_id} eliminado correctamente!")
                            st.session_state.pedido_a_eliminar = None
                            st.rerun()
                        else:
                            st.error("Error al eliminar el pedido de Firestore")
                    except Exception as e:
                        st.error(f"Error al eliminar el pedido: {str(e)}")