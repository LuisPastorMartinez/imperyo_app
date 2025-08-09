# pages/pedidos_page.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils import get_next_id, save_dataframe_firestore, delete_document_firestore

def show_pedidos_page(df_pedidos, df_listas):
    # Definir las pestañas
    tab1, tab2, tab3 = st.tabs(["Crear Pedido", "Consultar/Eliminar Pedidos", "Modificar Pedido"])
    
    # Pestaña 1: Crear Pedido (se mantiene igual)
    with tab1:
        st.subheader("Crear Nuevo Pedido")
        # ... (código existente para crear pedidos)
    
    # Pestaña 2: Consultar y Eliminar Pedidos (actualizada)
    with tab2:
        st.subheader("Consultar y Eliminar Pedidos")
        
        # Filtros de búsqueda
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtro_cliente = st.text_input("Filtrar por cliente")
        with col_f2:
            filtro_producto = st.selectbox(
                "Filtrar por producto",
                [""] + df_listas['Producto'].dropna().unique().tolist()
            )
        with col_f3:
            filtro_estado = st.selectbox(
                "Filtrar por estado",
                ["", "Pendiente", "Empezado", "Terminado", "Cobrado", "Retirado"]
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
        
        # Mostrar resultados con opción de eliminación
        st.write("**Resultados:**")
        
        # Selección de pedido para eliminar
        selected_ids = st.multiselect(
            "Seleccione pedidos para eliminar",
            options=df_filtrado['ID'].unique(),
            format_func=lambda x: f"Pedido ID: {x}"
        )
        
        # Mostrar tabla con checkbox de selección
        st.dataframe(
            df_filtrado[[
                'ID', 'Producto', 'Cliente', 'Club', 'Telefono', 
                'Fecha entrada', 'Fecha Salida', 'Precio', 'Pendiente',
                'Inicio Trabajo', 'Trabajo Terminado', 'Cobrado', 'Retirado'
            ]].sort_values('ID', ascending=False),
            height=400
        )
        
        # Botón para eliminar pedidos seleccionados
        if selected_ids:
            st.warning(f"Pedidos seleccionados para eliminar: {', '.join(map(str, selected_ids))}")
            
            col_confirm1, col_confirm2 = st.columns(2)
            with col_confirm1:
                if st.button("Confirmar Eliminación", type="primary"):
                    try:
                        # Eliminar de DataFrame
                        df_to_keep = df_pedidos[~df_pedidos['ID'].isin(selected_ids)]
                        
                        # Eliminar de Firestore
                        success = True
                        for pid in selected_ids:
                            pedido = df_pedidos[df_pedidos['ID'] == pid].iloc[0]
                            doc_id = pedido.get('id_documento_firestore')
                            if doc_id and not delete_document_firestore('pedidos', doc_id):
                                success = False
                                break
                        
                        if success:
                            st.session_state.data['df_pedidos'] = df_to_keep
                            if save_dataframe_firestore(df_to_keep, 'pedidos'):
                                st.success(f"Pedidos {', '.join(map(str, selected_ids))} eliminados correctamente!")
                                st.rerun()
                            else:
                                st.error("Error al guardar los cambios en Firestore")
                        else:
                            st.error("Error al eliminar algunos pedidos de Firestore")
                    except Exception as e:
                        st.error(f"Error al eliminar pedidos: {str(e)}")
            
            with col_confirm2:
                if st.button("Cancelar Eliminación"):
                    st.rerun()
    
    # Pestaña 3: Modificar Pedido (se mantiene igual)
    with tab3:
        st.subheader("Modificar Pedido Existente")
        # ... (código existente para modificar pedidos)