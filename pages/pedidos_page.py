# pages/pedidos_page.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils import get_next_id, save_dataframe_firestore, delete_document_firestore

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

def clean_dataframe(df):
    """Limpia el DataFrame para Firestore"""
    df = df.copy()
    
    # Columnas específicas con sus tipos
    date_cols = [col for col in df.columns if 'Fecha' in col]
    bool_cols = ['Inicio Trabajo', 'Trabajo Terminado', 'Cobrado', 'Retirado', 'Pendiente']
    num_cols = ['Precio', 'Precio Factura', 'Adelanto']
    str_cols = ['Producto', 'Cliente', 'Telefono', 'Club', 'Talla', 'Tela', 
               'Breve Descripción', 'Tipo de pago', 'Observaciones']
    
    for col in df.columns:
        if col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
        elif col in bool_cols:
            df[col] = df[col].astype(bool)
        elif col in num_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        elif col in str_cols:
            df[col] = df[col].astype(str).replace('nan', '').replace('None', '')
    
    return df

def show_pedidos_page(df_pedidos, df_listas):
    # Preparar datos iniciales
    df_pedidos = clean_dataframe(df_pedidos)
    
    # Pestañas principales
    tab1, tab2, tab3, tab4 = st.tabs([
        "Crear Pedido", 
        "Consultar Pedidos", 
        "Modificar Pedido", 
        "Eliminar Pedido"
    ])

    # ========== CREAR PEDIDO ==========
    with tab1:
        st.subheader("Crear Nuevo Pedido")
        
        with st.form("nuevo_pedido_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                producto = st.selectbox(
                    "Producto*", 
                    options=[""] + df_listas['Producto'].dropna().unique().tolist()
                )
                cliente = st.text_input("Cliente*")
                telefono = st.text_input("Teléfono*")
                club = st.text_input("Club*")
                talla = st.selectbox(
                    "Talla", 
                    options=[""] + df_listas['Talla'].dropna().unique().tolist()
                )
                tela = st.selectbox(
                    "Tela", 
                    options=[""] + df_listas['Tela'].dropna().unique().tolist()
                )
                descripcion = st.text_area("Descripción")
            
            with col2:
                fecha_entrada = st.date_input(
                    "Fecha entrada*", 
                    value=datetime.now()
                )
                fecha_salida = st.date_input("Fecha salida")
                precio = st.number_input(
                    "Precio*", 
                    min_value=0.0, 
                    value=0.0, 
                    step=0.01
                )
                precio_factura = st.number_input(
                    "Precio factura", 
                    min_value=0.0, 
                    value=0.0, 
                    step=0.01
                )
                tipo_pago = st.selectbox(
                    "Tipo de pago", 
                    options=[""] + df_listas['Tipo de pago'].dropna().unique().tolist()
                )
                adelanto = st.number_input(
                    "Adelanto", 
                    min_value=0.0, 
                    value=0.0, 
                    step=0.01
                )
                observaciones = st.text_area("Observaciones")
            
            # Estado del pedido
            st.write("**Estado del pedido:**")
            cols_estado = st.columns(5)
            with cols_estado[0]: 
                empezado = st.checkbox("Empezado")
            with cols_estado[1]: 
                terminado = st.checkbox("Terminado")
            with cols_estado[2]: 
                cobrado = st.checkbox("Cobrado")
            with cols_estado[3]: 
                retirado = st.checkbox("Retirado")
            with cols_estado[4]: 
                pendiente = st.checkbox("Pendiente")
            
            if st.form_submit_button("Guardar Pedido"):
                if not all([cliente, telefono, producto, club, precio > 0]):
                    st.error("Complete los campos obligatorios (*)")
                else:
                    try:
                        new_id = get_next_id(df_pedidos, 'ID')
                        new_pedido = {
                            'ID': new_id,
                            'Producto': producto,
                            'Cliente': cliente,
                            'Telefono': telefono,
                            'Club': club,
                            'Talla': talla if talla else '',
                            'Tela': tela if tela else '',
                            'Breve Descripción': descripcion if descripcion else '',
                            'Fecha entrada': fecha_entrada,
                            'Fecha Salida': fecha_salida if fecha_salida else None,
                            'Precio': float(precio),
                            'Precio Factura': float(precio_factura) if precio_factura else None,
                            'Tipo de pago': tipo_pago if tipo_pago else '',
                            'Adelanto': float(adelanto) if adelanto else 0.0,
                            'Observaciones': observaciones if observaciones else '',
                            'Inicio Trabajo': bool(empezado),
                            'Trabajo Terminado': bool(terminado),
                            'Cobrado': bool(cobrado),
                            'Retirado': bool(retirado),
                            'Pendiente': bool(pendiente),
                            'id_documento_firestore': None
                        }
                        
                        # Limpiar y agregar el nuevo pedido
                        new_df = pd.DataFrame([new_pedido])
                        new_df = clean_dataframe(new_df)
                        df_pedidos = pd.concat([df_pedidos, new_df], ignore_index=True)
                        
                        # Guardar en Firestore
                        if save_dataframe_firestore(df_pedidos, 'pedidos'):
                            st.success(f"✅ Pedido {new_id} creado!")
                            st.session_state.data['df_pedidos'] = df_pedidos
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

    # [Resto del código de las otras pestañas...]
    # ... (las otras pestañas permanecen igual)

    
    # ========== CONSULTAR PEDIDOS ==========
    with tab2:
        st.subheader("Consultar Pedidos")
        
        # Filtros
        col_filtros = st.columns(3)
        with col_filtros[0]:
            filtro_cliente = st.text_input("Filtrar por cliente")
        with col_filtros[1]:
            filtro_producto = st.selectbox("Filtrar por producto", [""] + df_listas['Producto'].dropna().unique().tolist())
        with col_filtros[2]:
            filtro_estado = st.selectbox("Filtrar por estado", ["", "Pendiente", "Empezado", "Terminado", "Cobrado", "Retirado"])
        
        # Aplicar filtros
        df_filtrado = df_pedidos.copy()
        if filtro_cliente:
            df_filtrado = df_filtrado[df_filtrado['Cliente'].str.contains(filtro_cliente, case=False, na=False)]
        if filtro_producto:
            df_filtrado = df_filtrado[df_filtrado['Producto'] == filtro_producto]
        if filtro_estado:
            estado_col = {
                "Pendiente": "Pendiente",
                "Empezado": "Inicio Trabajo",
                "Terminado": "Trabajo Terminado",
                "Cobrado": "Cobrado",
                "Retirado": "Retirado"
            }[filtro_estado]
            df_filtrado = df_filtrado[df_filtrado[estado_col] == True]
        
        # Mostrar resultados
        cols_mostrar = [
            'ID', 'Producto', 'Cliente', 'Club', 'Telefono',
            'Fecha entrada', 'Fecha Salida', 'Precio',
            'Inicio Trabajo', 'Trabajo Terminado', 'Cobrado', 'Retirado', 'Pendiente'
        ]
        
        st.dataframe(
            df_filtrado[cols_mostrar].sort_values('ID', ascending=False),
            height=500
        )

    # ========== MODIFICAR PEDIDO ==========
    with tab3:
        st.subheader("Modificar Pedido")
        
        mod_id = st.number_input("ID del pedido:", min_value=1, step=1)
        
        if st.button("Cargar Pedido"):
            if mod_id in df_pedidos['ID'].values:
                st.session_state.pedido_edit = df_pedidos[df_pedidos['ID'] == mod_id].iloc[0].to_dict()
                st.success(f"Pedido {mod_id} cargado")
            else:
                st.warning(f"No existe pedido con ID {mod_id}")
        
        if 'pedido_edit' in st.session_state and st.session_state.pedido_edit:
            pedido = st.session_state.pedido_edit
            
            with st.form("form_editar_pedido"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.text_input("ID", value=pedido['ID'], disabled=True)
                    producto = st.selectbox(
                        "Producto*", 
                        options=[""] + df_listas['Producto'].dropna().unique().tolist(),
                        index=(["", *df_listas['Producto'].dropna().unique()].index(pedido['Producto']) 
                        if pd.notna(pedido.get('Producto')) else 0
                    )
                    cliente = st.text_input("Cliente*", value=pedido.get('Cliente', ''))
                    telefono = st.text_input("Teléfono*", value=pedido.get('Telefono', ''))
                    club = st.text_input("Club*", value=pedido.get('Club', ''))
                    talla = st.selectbox(
                        "Talla", 
                        options=[""] + df_listas['Talla'].dropna().unique().tolist(),
                        index=(["", *df_listas['Talla'].dropna().unique()].index(pedido['Talla'])) 
                        if pd.notna(pedido.get('Talla')) else 0
                    )
                    tela = st.selectbox(
                        "Tela", 
                        options=[""] + df_listas['Tela'].dropna().unique().tolist(),
                        index=(["", *df_listas['Tela'].dropna().unique()].index(pedido['Talla'])) 
                        if pd.notna(pedido.get('Talla')) else 0
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
                        index=(["", *df_listas['Tipo de pago'].dropna().unique()].index(pedido['Tipo de pago'])) 
                        if pd.notna(pedido.get('Tipo de pago')) else 0
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
                cols_estado = st.columns(5)
                with cols_estado[0]: empezado = st.checkbox("Empezado", value=bool(pedido.get('Inicio Trabajo', False)))
                with cols_estado[1]: terminado = st.checkbox("Terminado", value=bool(pedido.get('Trabajo Terminado', False)))
                with cols_estado[2]: cobrado = st.checkbox("Cobrado", value=bool(pedido.get('Cobrado', False)))
                with cols_estado[3]: retirado = st.checkbox("Retirado", value=bool(pedido.get('Retirado', False)))
                with cols_estado[4]: pendiente = st.checkbox("Pendiente", value=bool(pedido.get('Pendiente', False)))
                
                if st.form_submit_button("Guardar Cambios"):
                    if not all([cliente, telefono, producto, club, precio > 0]):
                        st.error("Complete los campos obligatorios (*)")
                    else:
                        try:
                            # Actualizar datos
                            idx = df_pedidos[df_pedidos['ID'] == mod_id].index[0]
                            
                            updates = {
                                'Producto': producto,
                                'Cliente': cliente,
                                'Telefono': telefono,
                                'Club': club,
                                'Talla': talla if talla else '',
                                'Tela': tela if tela else '',
                                'Breve Descripción': descripcion if descripcion else '',
                                'Fecha entrada': fecha_entrada,
                                'Fecha Salida': fecha_salida if fecha_salida else None,
                                'Precio': float(precio),
                                'Precio Factura': float(precio_factura) if precio_factura else None,
                                'Tipo de pago': tipo_pago if tipo_pago else '',
                                'Adelanto': float(adelanto) if adelanto else 0.0,
                                'Observaciones': observaciones if observaciones else '',
                                'Inicio Trabajo': bool(empezado),
                                'Trabajo Terminado': bool(terminado),
                                'Cobrado': bool(cobrado),
                                'Retirado': bool(retirado),
                                'Pendiente': bool(pendiente)
                            }
                            
                            for key, value in updates.items():
                                df_pedidos.at[idx, key] = prepare_for_firestore(value)
                            
                            if save_dataframe_firestore(df_pedidos, 'pedidos'):
                                st.success(f"✅ Pedido {mod_id} actualizado!")
                                st.session_state.pedido_edit = None
                                st.rerun()
                            else:
                                st.error("❌ Error al guardar cambios")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

    # ========== ELIMINAR PEDIDO ==========
    with tab4:
        st.subheader("Eliminar Pedido")
        
        del_id = st.number_input("ID del pedido:", min_value=1, step=1)
        
        if st.button("Buscar Pedido"):
            if del_id in df_pedidos['ID'].values:
                st.session_state.pedido_del = df_pedidos[df_pedidos['ID'] == del_id].iloc[0].to_dict()
                st.success(f"Pedido {del_id} encontrado")
            else:
                st.warning(f"No existe pedido con ID {del_id}")
                st.session_state.pedido_del = None
        
        if 'pedido_del' in st.session_state and st.session_state.pedido_del:
            pedido = st.session_state.pedido_del
            
            st.warning("⚠️ **Pedido a eliminar:**")
            st.json({
                "ID": pedido['ID'],
                "Cliente": pedido['Cliente'],
                "Producto": pedido['Producto'],
                "Fecha entrada": str(pedido.get('Fecha entrada', '')),
                "Precio": pedido.get('Precio', 0)
            })
            
            confirmar = st.checkbox("Confirmar eliminación")
            
            if confirmar and st.button("Eliminar Definitivamente", type="primary"):
                try:
                    # Eliminar de DataFrame
                    df_pedidos = df_pedidos[df_pedidos['ID'] != del_id]
                    
                    # Eliminar de Firestore
                    doc_id = pedido.get('id_documento_firestore')
                    if delete_document_firestore('pedidos', doc_id):
                        st.session_state.data['df_pedidos'] = df_pedidos
                        if save_dataframe_firestore(df_pedidos, 'pedidos'):
                            st.success(f"✅ Pedido {del_id} eliminado!")
                            st.session_state.pedido_del = None
                            st.rerun()
                        else:
                            st.error("❌ Error al actualizar datos")
                    else:
                        st.error("❌ Error al eliminar de Firestore")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    return df_pedidos