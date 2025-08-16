# pages/pedidos_page.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils import get_next_id, save_dataframe_firestore, delete_document_firestore

def show_pedidos_page(df_pedidos, df_listas):
    # Definir las 4 pestañas
    tab1, tab2, tab3, tab4 = st.tabs(["Crear Pedido", "Consultar Pedidos", "Modificar Pedido", "Eliminar Pedido"])
    
    # Función mejorada para conversión de tipos
    def prepare_for_firestore(value):
        """Convierte valores a tipos compatibles con Firestore"""
        if value is None or pd.isna(value) or value == "":
            return None
        elif isinstance(value, (int, float, str, bool)):
            return value
        elif isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        elif isinstance(value, datetime):
            return value
        elif isinstance(value, pd.Timestamp):
            return value.to_pydatetime()
        try:
            return float(value) if str(value).replace('.','',1).isdigit() else str(value)
        except:
            return str(value)

    # ==============================================
    # Pestaña 1: Crear Pedido (Versión Corregida)
    # ==============================================
    with tab1:
        st.subheader("Crear Nuevo Pedido")
        
        with st.form("nuevo_pedido_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                producto = st.selectbox(
                    "Producto*",
                    options=[""] + df_listas['Producto'].dropna().unique().tolist(),
                    key="new_producto"
                )
                cliente = st.text_input("Cliente*", key="new_cliente")
                telefono = st.text_input("Teléfono*", key="new_telefono")
                club = st.text_input("Club*", key="new_club")
                talla = st.selectbox(
                    "Talla",
                    options=[""] + df_listas['Talla'].dropna().unique().tolist(),
                    key="new_talla"
                )
                tela = st.selectbox(
                    "Tela",
                    options=[""] + df_listas['Tela'].dropna().unique().tolist(),
                    key="new_tela"
                )
                descripcion = st.text_area("Descripción", key="new_descripcion")
            
            with col2:
                fecha_entrada = st.date_input(
                    "Fecha entrada*", 
                    value=datetime.now(),
                    key="new_fecha_entrada"
                )
                fecha_salida = st.date_input(
                    "Fecha salida", 
                    value=None,
                    key="new_fecha_salida"
                )
                precio = st.number_input("Precio*", min_value=0.0, value=0.0, step=0.01, key="new_precio")
                precio_factura = st.number_input(
                    "Precio factura", 
                    min_value=0.0, 
                    value=0.0,
                    step=0.01,
                    key="new_precio_factura"
                )
                tipo_pago = st.selectbox(
                    "Tipo de pago",
                    options=[""] + df_listas['Tipo de pago'].dropna().unique().tolist(),
                    key="new_tipo_pago"
                )
                adelanto = st.number_input(
                    "Adelanto", 
                    min_value=0.0, 
                    value=0.0,
                    step=0.01,
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
            
            submitted = st.form_submit_button("Guardar Nuevo Pedido")
            
            if submitted:
                if not all([cliente, telefono, producto, club, precio > 0]):
                    st.error("Por favor complete los campos obligatorios (*)")
                else:
                    try:
                        new_id = get_next_id(df_pedidos, 'ID')
                        
                        # Construcción del diccionario con conversión explícita
                        new_pedido = {
                            'ID': int(new_id),
                            'Producto': str(producto),
                            'Cliente': str(cliente),
                            'Telefono': str(telefono),
                            'Club': str(club),
                            'Talla': str(talla) if talla else None,
                            'Tela': str(tela) if tela else None,
                            'Breve Descripción': str(descripcion) if descripcion else None,
                            'Fecha entrada': datetime.combine(fecha_entrada, datetime.min.time()),
                            'Fecha Salida': datetime.combine(fecha_salida, datetime.min.time()) if fecha_salida else None,
                            'Precio': float(precio),
                            'Precio Factura': float(precio_factura) if precio_factura else None,
                            'Tipo de pago': str(tipo_pago) if tipo_pago else None,
                            'Adelanto': float(adelanto) if adelanto else 0.0,
                            'Observaciones': str(observaciones) if observaciones else None,
                            'Inicio Trabajo': bool(empezado),
                            'Trabajo Terminado': bool(terminado),
                            'Cobrado': bool(cobrado),
                            'Retirado': bool(retirado),
                            'Pendiente': bool(pendiente),
                            'id_documento_firestore': None
                        }

                        # Convertir todos los valores para Firestore
                        for key, value in new_pedido.items():
                            new_pedido[key] = prepare_for_firestore(value)

                        # Añadir al DataFrame
                        new_pedido_df = pd.DataFrame([new_pedido])
                        df_pedidos = pd.concat([df_pedidos, new_pedido_df], ignore_index=True)
                        
                        # Guardar en Firestore
                        if save_dataframe_firestore(df_pedidos, 'pedidos'):
                            st.success(f"✅ Pedido {new_id} creado correctamente!")
                            st.session_state.data['df_pedidos'] = df_pedidos
                            st.rerun()
                        else:
                            st.error("❌ Error al guardar en Firestore")
                    except Exception as e:
                        st.error(f"❌ Error crítico: {str(e)}")
                        st.stop()

    # ==============================================
    # Pestaña 2: Consultar Pedidos
    # ==============================================
    with tab2:
        st.subheader("Consultar Pedidos")
        
        # Filtros de búsqueda
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtro_cliente = st.text_input("Filtrar por cliente")
        with col_f2:
            filtro_producto = st.selectbox(
                "Filtrar por producto",
                options=[""] + df_listas['Producto'].dropna().unique().tolist()
            )
        with col_f3:
            filtro_estado = st.selectbox(
                "Filtrar por estado",
                options=["", "Pendiente", "Empezado", "Terminado", "Cobrado", "Retirado"]
            )
        
        # Aplicar filtros
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
        
        # Mostrar resultados
        if not df_filtrado.empty:
            st.dataframe(
                df_filtrado[[
                    'ID', 'Producto', 'Cliente', 'Club', 'Telefono', 
                    'Fecha entrada', 'Fecha Salida', 'Precio', 'Pendiente',
                    'Inicio Trabajo', 'Trabajo Terminado', 'Cobrado', 'Retirado'
                ]].sort_values('ID', ascending=False),
                height=500
            )
        else:
            st.info("No se encontraron pedidos con los filtros aplicados")

    # ==============================================
    # Pestaña 3: Modificar Pedido
    # ==============================================
    with tab3:
        st.subheader("Modificar Pedido Existente")
        
        # Selección del pedido a modificar
        mod_id = st.number_input("ID del pedido a modificar:", 
                                min_value=1, 
                                step=1,
                                key="modify_id_input")
        
        if st.button("Cargar Pedido", key="load_pedido_button"):
            if mod_id in df_pedidos['ID'].values:
                pedido = df_pedidos[df_pedidos['ID'] == mod_id].iloc[0].to_dict()
                st.session_state.pedido_a_modificar = pedido
                st.success(f"Pedido {mod_id} cargado para modificación")
            else:
                st.warning(f"No existe un pedido con ID {mod_id}")
                st.session_state.pedido_a_modificar = None
        
        if 'pedido_a_modificar' in st.session_state and st.session_state.pedido_a_modificar:
            pedido = st.session_state.pedido_a_modificar
            
            with st.form("modificar_pedido_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.text_input("ID", value=pedido['ID'], disabled=True)
                    producto = st.selectbox(
                        "Producto*",
                        options=[""] + df_listas['Producto'].dropna().unique().tolist(),
                        index=0 if pd.isna(pedido.get('Producto')) else 
                        (df_listas['Producto'].dropna().unique().tolist().index(pedido['Producto']) + 1 
                         if pedido['Producto'] in df_listas['Producto'].values else 0),
                        key="mod_producto"
                    )
                    cliente = st.text_input("Cliente*", value=pedido.get('Cliente', ''))
                    telefono = st.text_input("Teléfono*", value=pedido.get('Telefono', ''))
                    club = st.text_input("Club*", value=pedido.get('Club', ''))
                    talla = st.selectbox(
                        "Talla",
                        options=[""] + df_listas['Talla'].dropna().unique().tolist(),
                        index=0 if pd.isna(pedido.get('Talla')) else 
                        (df_listas['Talla'].dropna().unique().tolist().index(pedido['Talla']) + 1 
                         if pedido['Talla'] in df_listas['Talla'].values else 0),
                        key="mod_talla"
                    )
                    tela = st.selectbox(
                        "Tela",
                        options=[""] + df_listas['Tela'].dropna().unique().tolist(),
                        index=0 if pd.isna(pedido.get('Tela')) else 
                        (df_listas['Tela'].dropna().unique().tolist().index(pedido['Tela']) + 1 
                         if pedido['Tela'] in df_listas['Tela'].values else 0),
                        key="mod_tela"
                    )
                    descripcion = st.text_area("Descripción", value=pedido.get('Breve Descripción', ''))
                
                with col2:
                    fecha_entrada = st.date_input(
                        "Fecha entrada*", 
                        value=pedido.get('Fecha entrada', datetime.now())
                    )
                    fecha_salida = st.date_input(
                        "Fecha salida", 
                        value=pedido.get('Fecha Salida', None)
                    )
                    precio = st.number_input(
                        "Precio*", 
                        min_value=0.0, 
                        value=float(pedido.get('Precio', 0.0)),
                        step=0.01
                    )
                    precio_factura = st.number_input(
                        "Precio factura", 
                        min_value=0.0, 
                        value=float(pedido.get('Precio Factura', 0.0)),
                        step=0.01
                    )
                    tipo_pago = st.selectbox(
                        "Tipo de pago",
                        options=[""] + df_listas['Tipo de pago'].dropna().unique().tolist(),
                        index=0 if pd.isna(pedido.get('Tipo de pago')) else 
                        (df_listas['Tipo de pago'].dropna().unique().tolist().index(pedido['Tipo de pago']) + 1 
                         if pedido['Tipo de pago'] in df_listas['Tipo de pago'].values else 0),
                        key="mod_tipo_pago"
                    )
                    adelanto = st.number_input(
                        "Adelanto", 
                        min_value=0.0, 
                        value=float(pedido.get('Adelanto', 0.0)),
                        step=0.01
                    )
                    observaciones = st.text_area("Observaciones", value=pedido.get('Observaciones', ''))
                
                # Estado del pedido
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
                
                if st.form_submit_button("Guardar Cambios"):
                    if not all([cliente, telefono, producto, club, precio > 0]):
                        st.error("Por favor complete los campos obligatorios (*)")
                    else:
                        try:
                            # Actualizar el pedido
                            updated_pedido = {
                                'ID': int(mod_id),
                                'Producto': str(producto),
                                'Cliente': str(cliente),
                                'Telefono': str(telefono),
                                'Club': str(club),
                                'Talla': str(talla) if talla else None,
                                'Tela': str(tela) if tela else None,
                                'Breve Descripción': str(descripcion) if descripcion else None,
                                'Fecha entrada': datetime.combine(fecha_entrada, datetime.min.time()),
                                'Fecha Salida': datetime.combine(fecha_salida, datetime.min.time()) if fecha_salida else None,
                                'Precio': float(precio),
                                'Precio Factura': float(precio_factura) if precio_factura else None,
                                'Tipo de pago': str(tipo_pago) if tipo_pago else None,
                                'Adelanto': float(adelanto) if adelanto else 0.0,
                                'Observaciones': str(observaciones) if observaciones else None,
                                'Inicio Trabajo': bool(empezado),
                                'Trabajo Terminado': bool(terminado),
                                'Cobrado': bool(cobrado),
                                'Retirado': bool(retirado),
                                'Pendiente': bool(pendiente),
                                'id_documento_firestore': pedido.get('id_documento_firestore')
                            }

                            # Actualizar el DataFrame
                            idx = df_pedidos[df_pedidos['ID'] == mod_id].index[0]
                            for key, value in updated_pedido.items():
                                df_pedidos.at[idx, key] = prepare_for_firestore(value)

                            # Guardar en Firestore
                            if save_dataframe_firestore(df_pedidos, 'pedidos'):
                                st.success(f"✅ Pedido {mod_id} actualizado correctamente!")
                                st.session_state.pedido_a_modificar = None
                                st.session_state.data['df_pedidos'] = df_pedidos
                                st.rerun()
                            else:
                                st.error("❌ Error al guardar los cambios")
                        except Exception as e:
                            st.error(f"❌ Error al actualizar el pedido: {str(e)}")

    # ==============================================
    # Pestaña 4: Eliminar Pedido
    # ==============================================
    with tab4:
        st.subheader("Eliminar Pedido")
        
        # Selección del pedido a eliminar
        del_id = st.number_input("ID del pedido a eliminar:", 
                               min_value=1, 
                               step=1,
                               key="delete_id_input")
        
        if st.button("Buscar Pedido", key="search_pedido_button"):
            if del_id in df_pedidos['ID'].values:
                st.session_state.pedido_a_eliminar = df_pedidos[df_pedidos['ID'] == del_id].iloc[0].to_dict()
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
                "Fecha entrada": str(pedido.get('Fecha entrada', '')),
                "Precio": pedido.get('Precio', 0)
            })
            
            confirmacion = st.checkbox("Confirmo que deseo eliminar este pedido permanentemente", 
                                     key="confirm_delete")
            
            if confirmacion:
                if st.button("Eliminar Definitivamente", type="primary", key="confirm_delete_button"):
                    try:
                        # Eliminar de DataFrame
                        df_pedidos = df_pedidos[df_pedidos['ID'] != del_id]
                        
                        # Eliminar de Firestore
                        doc_id = pedido.get('id_documento_firestore')
                        if delete_document_firestore('pedidos', doc_id):
                            st.session_state.data['df_pedidos'] = df_pedidos
                            if save_dataframe_firestore(df_pedidos, 'pedidos'):
                                st.success(f"✅ Pedido {del_id} eliminado correctamente!")
                                st.session_state.pedido_a_eliminar = None
                                st.rerun()
                            else:
                                st.error("❌ Error al guardar los cambios en Firestore")
                        else:
                            st.error("❌ Error al eliminar el pedido de Firestore")
                    except Exception as e:
                        st.error(f"❌ Error al eliminar el pedido: {str(e)}")