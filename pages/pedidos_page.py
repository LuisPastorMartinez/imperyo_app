import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils import get_next_id, save_dataframe_firestore, delete_document_firestore

def show_pedidos_page(df_pedidos, df_listas):
    tab1, tab2, tab3, tab4 = st.tabs(["Crear Pedido", "Consultar Pedidos", "Modificar Pedido", "Eliminar Pedido"])
    
    def convert_to_firestore_type(value):
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
    
    # Pestaña 1: Crear Pedido (sin cambios)
    with tab1:
        # ... (mantener todo el código existente sin cambios)
    
    # Pestaña 2: Consultar Pedidos (CORRECCIÓN PARA ArrowTypeError)
    with tab2:
        st.subheader("Consultar Pedidos")
        
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
        
        df_filtrado = df_pedidos.copy()
        
        # Aplicar filtros (sin cambios)
        if filtro_cliente:
            df_filtrado = df_filtrado[df_filtrado['Cliente'].str.contains(filtro_cliente, case=False, na=False)]
        if filtro_producto:
            df_filtrado = df_filtrado[df_filtrado['Producto'] == filtro_producto]
        if filtro_estado:
            # ... (mantener lógica de filtrado existente)
        
        # PREPARACIÓN DEL DATAFRAME PARA VISUALIZACIÓN (CORRECCIÓN)
        df_mostrar = df_filtrado[[
            'ID', 'Producto', 'Cliente', 'Club', 'Telefono', 
            'Fecha entrada', 'Fecha Salida', 'Precio', 'Pendiente',
            'Inicio Trabajo', 'Trabajo Terminado', 'Cobrado', 'Retirado'
        ]].sort_values('ID', ascending=False).copy()
        
        # Convertir tipos problemáticos
        for col in ['Fecha entrada', 'Fecha Salida']:
            if col in df_mostrar.columns:
                df_mostrar[col] = pd.to_datetime(df_mostrar[col]).dt.date
                
        for col in ['Inicio Trabajo', 'Trabajo Terminado', 'Cobrado', 'Retirado', 'Pendiente']:
            if col in df_mostrar.columns:
                df_mostrar[col] = df_mostrar[col].fillna(False).astype(bool)
        
        st.dataframe(df_mostrar, height=500)

    # Pestañas 3 y 4 (sin cambios)
    with tab3:
        # ... (mantener código existente)
    
    with tab4:
        # ... (mantener código existente)