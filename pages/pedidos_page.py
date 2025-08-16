# pages/pedidos_page.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from utils import get_next_id, save_dataframe_firestore, delete_document_firestore

def clean_for_firestore(value):
    """Convierte cualquier valor a un tipo compatible con Firestore"""
    if pd.isna(value) or value is None:
        return None
    elif isinstance(value, (int, np.integer)):
        return int(value)
    elif isinstance(value, (float, np.floating)):
        return float(value)
    elif isinstance(value, bool):
        return bool(value)
    elif isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    elif isinstance(value, datetime):
        return value
    elif isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    else:
        return str(value)

def prepare_dataframe(df):
    """Prepara el DataFrame para Firestore y Streamlit"""
    # Convertir tipos de columnas específicas
    date_cols = [col for col in df.columns if 'Fecha' in col]
    bool_cols = ['Inicio Trabajo', 'Trabajo Terminado', 'Cobrado', 'Retirado', 'Pendiente']
    num_cols = ['Precio', 'Precio Factura', 'Adelanto']
    
    df = df.copy()
    
    for col in df.columns:
        if col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
        elif col in bool_cols:
            df[col] = df[col].astype(bool)
        elif col in num_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        else:
            df[col] = df[col].astype(str).replace('nan', '').replace('None', '')
    
    return df

def show_pedidos_page(df_pedidos, df_listas):
    # Preparar el DataFrame inicial
    df_pedidos = prepare_dataframe(df_pedidos)
    
    # Definir pestañas
    tab1, tab2, tab3, tab4 = st.tabs(["Crear Pedido", "Consultar Pedidos", "Modificar Pedido", "Eliminar Pedido"])

    # ========== PESTAÑA 1: CREAR PEDIDO ==========
    with tab1:
        st.subheader("Crear Nuevo Pedido")
        
        with st.form("nuevo_pedido_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                producto = st.selectbox("Producto*", [""] + df_listas['Producto'].dropna().unique().tolist())
                cliente = st.text_input("Cliente*")
                telefono = st.text_input("Teléfono*")
                club = st.text_input("Club*")
                talla = st.selectbox("Talla", [""] + df_listas['Talla'].dropna().unique().tolist())
                tela = st.selectbox("Tela", [""] + df_listas['Tela'].dropna().unique().tolist())
                descripcion = st.text_area("Descripción")
            
            with col2:
                fecha_entrada = st.date_input("Fecha entrada*", datetime.now())
                fecha_salida = st.date_input("Fecha salida", None)
                precio = st.number_input("Precio*", min_value=0.0, value=0.0, step=0.01)
                precio_factura = st.number_input("Precio factura", min_value=0.0, value=0.0, step=0.01)
                tipo_pago = st.selectbox("Tipo de pago", [""] + df_listas['Tipo de pago'].dropna().unique().tolist())
                adelanto = st.number_input("Adelanto", min_value=0.0, value=0.0, step=0.01)
                observaciones = st.text_area("Observaciones")
            
            # Estado del pedido
            st.write("**Estado del pedido:**")
            col_estado = st.columns(5)
            with col_estado[0]: empezado = st.checkbox("Empezado")
            with col_estado[1]: terminado = st.checkbox("Terminado")
            with col_estado[2]: cobrado = st.checkbox("Cobrado")
            with col_estado[3]: retirado = st.checkbox("Retirado")
            with col_estado[4]: pendiente = st.checkbox("Pendiente")
            
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
                            'Talla': talla if talla else None,
                            'Tela': tela if tela else None,
                            'Breve Descripción': descripcion if descripcion else None,
                            'Fecha entrada': fecha_entrada,
                            'Fecha Salida': fecha_salida if fecha_salida else None,
                            'Precio': precio,
                            'Precio Factura': precio_factura if precio_factura else None,
                            'Tipo de pago': tipo_pago if tipo_pago else None,
                            'Adelanto': adelanto if adelanto else 0.0,
                            'Observaciones': observaciones if observaciones else None,
                            'Inicio Trabajo': empezado,
                            'Trabajo Terminado': terminado,
                            'Cobrado': cobrado,
                            'Retirado': retirado,
                            'Pendiente': pendiente
                        }
                        
                        # Limpiar datos para Firestore
                        new_pedido = {k: clean_for_firestore(v) for k, v in new_pedido.items()}
                        
                        # Añadir al DataFrame
                        new_df = pd.DataFrame([new_pedido])
                        df_pedidos = pd.concat([df_pedidos, prepare_dataframe(new_df)], ignore_index=True)
                        
                        # Guardar en Firestore
                        if save_dataframe_firestore(df_pedidos, 'pedidos'):
                            st.success(f"✅ Pedido {new_id} creado!")
                            st.session_state.data['df_pedidos'] = df_pedidos
                            st.rerun()
                        else:
                            st.error("❌ Error al guardar")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

    # ========== PESTAÑA 2: CONSULTAR PEDIDOS ==========
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
            estado_map = {
                "Pendiente": "Pendiente",
                "Empezado": "Inicio Trabajo",
                "Terminado": "Trabajo Terminado",
                "Cobrado": "Cobrado",
                "Retirado": "Retirado"
            }
            df_filtrado = df_filtrado[df_filtrado[estado_map[filtro_estado]] == True]
        
        # Mostrar resultados
        cols_mostrar = ['ID', 'Producto', 'Cliente', 'Club', 'Telefono', 
                       'Fecha entrada', 'Fecha Salida', 'Precio', 'Pendiente',
                       'Inicio Trabajo', 'Trabajo Terminado', 'Cobrado', 'Retirado']
        
        st.dataframe(
            df_filtrado[cols_mostrar].sort_values('ID', ascending=False),
            height=500
        )

    # ========== PESTAÑA 3: MODIFICAR PEDIDO ==========
    with tab3:
        st.subheader("Modificar Pedido")
        
        mod_id = st.number_input("ID del pedido a modificar:", min_value=1, step=1)
        
        if st.button("Cargar Pedido"):
            if mod_id in df_pedidos['ID'].values:
                st.session_state.pedido_edit = df_pedidos[df_pedidos['ID'] == mod_id].iloc[0].to_dict()
                st.success(f"Pedido {mod_id} cargado")
            else:
                st.warning(f"No existe pedido con ID {mod_id}")
                st.session_state.pedido_edit = None
        
        if 'pedido_edit' in st.session_state and st.session_state.pedido_edit:
            pedido = st.session_state.pedido_edit
            
            with st.form("form_editar_pedido"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.text_input("ID", value=pedido['ID'], disabled=True)
                    producto = st.selectbox("Producto*", 
                                          [""] + df_listas['Producto'].dropna().unique().tolist(),
                                          index=([""] + df_listas['Producto'].dropna().unique().tolist()).index(pedido['Producto']) 
                                          if pd.notna(pedido['Producto']) else 0)
                    cliente = st.text_input("Cliente*", value=pedido['Cliente'])
                    telefono = st.text_input("Teléfono*", value=pedido['Telefono'])
                    club = st.text_input("Club*", value=pedido['Club'])
                    talla = st.selectbox("Talla", 
                                       [""] + df_listas['Talla'].dropna().unique().tolist(),
                                       index=([""] + df_listas['Talla'].dropna().unique().tolist()).index(pedido['Talla']) 
                                       if pd.notna(pedido['Talla']) else 0)
                    tela = st.selectbox("Tela", 
                                      [""] + df_listas['Tela'].dropna().unique().tolist(),
                                      index=([""] + df_listas['Tela'].dropna().unique().tolist()).index(pedido['Tela']) 
                                      if pd.notna(pedido['Tela']) else 0)
                    descripcion = st.text_area("Descripción", value=pedido['Breve Descripción'])
                
                with col2:
                    fecha_entrada = st.date_input("Fecha entrada*", 
                                                 value=pedido['Fecha entrada'].to_pydatetime().date() 
                                                 if pd.notna(pedido['Fecha entrada']) else datetime.now())
                    fecha_salida = st.date_input("Fecha salida", 
                                                value=pedido['Fecha Salida'].to_pydatetime().date() 
                                                if pd.notna(pedido['Fecha Salida']) else None)
                    precio = st.number_input("Precio*", min_value=0.0, 
                                           value=float(pedido['Precio']), step=0.01)
                    precio_factura = st.number_input("Precio factura", min_value=0.0, 
                                                    value=float(pedido['Precio Factura']) if pd.notna(pedido['Precio Factura']) else 0.0, 
                                                    step=0.01)
                    tipo_pago = st.selectbox("Tipo de pago", 
                                           [""] + df_listas['Tipo de pago'].dropna().unique().tolist(),
                                           index=([""] + df_listas['Tipo de pago'].dropna().unique().tolist()).index(pedido['Tipo de pago']) 
                                           if pd.notna(pedido['Tipo de pago']) else 0)
                    adelanto = st.number_input("Adelanto", min_value=0.0, 
                                             value=float(pedido['Adelanto']), step=0.01)
                    observaciones = st.text_area("Observaciones", value=pedido['Observaciones'])
                
                # Estado del pedido
                st.write("**Estado del pedido:**")
                col_estado = st.columns(5)
                with col_estado[0]: empezado = st.checkbox("Empezado", value=bool(pedido['Inicio Trabajo']))
                with col_estado[1]: terminado = st.checkbox("Terminado", value=bool(pedido['Trabajo Terminado']))
                with col_estado[2]: cobrado = st.checkbox("Cobrado", value=bool(pedido['Cobrado']))
                with col_estado[3]: retirado = st.checkbox("Retirado", value=bool(pedido['Retirado']))
                with col_estado[4]: pendiente = st.checkbox("Pendiente", value=bool(pedido['Pendiente']))
                
                if st.form_submit_button("Guardar Cambios"):
                    if not all([cliente, telefono, producto, club, precio > 0]):
                        st.error("Complete los campos obligatorios (*)")
                    else:
                        try:
                            # Actualizar datos
                            update_data = {
                                'Producto': producto,
                                'Cliente': cliente,
                                'Telefono': telefono,
                                'Club': club,
                                'Talla': talla if talla else None,
                                'Tela': tela if tela else None,
                                'Breve Descripción': descripcion if descripcion else None,
                                'Fecha entrada': fecha_entrada,
                                'Fecha Salida': fecha_salida if fecha_salida else None,
                                'Precio': precio,
                                'Precio Factura': precio_factura if precio_factura else None,
                                'Tipo de pago': tipo_pago if tipo_pago else None,
                                'Adelanto': adelanto if adelanto else 0.0,
                                'Observaciones': observaciones if observaciones else None,
                                'Inicio Trabajo': empezado,
                                'Trabajo Terminado': terminado,
                                'Cobrado': cobrado,
                                'Retirado': retirado,
                                'Pendiente': pendiente
                            }
                            
                            # Aplicar actualización
                            idx = df_pedidos[df_pedidos['ID'] == mod_id].index[0]
                            for k, v in update_data.items():
                                df_pedidos.at[idx, k] = clean_for_firestore(v)
                            
                            # Guardar cambios
                            if save_dataframe_firestore(df_pedidos, 'pedidos'):
                                st.success(f"✅ Pedido {mod_id} actualizado!")
                                st.session_state.pedido_edit = None
                                st.session_state.data['df_pedidos'] = df_pedidos
                                st.rerun()
                            else:
                                st.error("❌ Error al guardar cambios")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

    # ========== PESTAÑA 4: ELIMINAR PEDIDO ==========
    with tab4:
        st.subheader("Eliminar Pedido")
        
        del_id = st.number_input("ID del pedido a eliminar:", min_value=1, step=1)
        
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
                "Fecha": str(pedido['Fecha entrada']),
                "Precio": pedido['Precio']
            })
            
            if st.checkbox("Confirmar eliminación"):
                if st.button("Eliminar Definitivamente", type="primary"):
                    try:
                        # Eliminar de DataFrame
                        df_pedidos = df_pedidos[df_pedidos['ID'] != del_id]
                        
                        # Guardar cambios
                        if save_dataframe_firestore(df_pedidos, 'pedidos'):
                            st.success(f"✅ Pedido {del_id} eliminado!")
                            st.session_state.pedido_del = None
                            st.session_state.data['df_pedidos'] = df_pedidos
                            st.rerun()
                        else:
                            st.error("❌ Error al eliminar")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

    return df_pedidos