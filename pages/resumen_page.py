# pages/resumen_page.py
import streamlit as st
import pandas as pd

def highlight_pedidos_rows(row):
    """Función para resaltar filas según su estado"""
    styles = [''] * len(row)
    
    empezado = row.get('Inicio Trabajo', False)
    terminado = row.get('Trabajo Terminado', False)
    cobrado = row.get('Cobrado', False)
    retirado = row.get('Retirado', False)
    pendiente = row.get('Pendiente', False)

    # Lógica de colores mejorada
    if pendiente:
        styles = ['background-color: #FF00FF'] * len(row)  # Morado para pendientes
    elif empezado and not pendiente:
        styles = ['background-color: #0070C0'] * len(row)  # Azul para empezados no pendientes
    elif terminado and not pendiente:
        styles = ['background-color: #FFC000'] * len(row)  # Amarillo para terminados
    elif cobrado and retirado:
        styles = ['background-color: #00B050'] * len(row)  # Verde para completados

    return styles

def show_resumen_page(df_pedidos, current_view):
    """Muestra la página de resumen con filtros mejorados"""
    st.header("Resumen de Pedidos")
    
    # Filtrado mejorado
    if current_view == "Todos los Pedidos":
        filtered_df = df_pedidos.copy()
        st.subheader("Todos los Pedidos")
    elif current_view == "Trabajos Empezados":
        filtered_df = df_pedidos[
            (df_pedidos['Inicio Trabajo'] == True) & 
            (df_pedidos['Pendiente'] == False)
        ]
        st.subheader("Trabajos Empezados (no pendientes)")
    elif current_view == "Trabajos Terminados":
        filtered_df = df_pedidos[
            (df_pedidos['Trabajo Terminado'] == True) & 
            (df_pedidos['Pendiente'] == False)
        ]
        st.subheader("Trabajos Terminados (no pendientes)")
    elif current_view == "Pedidos Pendientes":
        filtered_df = df_pedidos[df_pedidos['Pendiente'] == True]
        st.subheader("Pedidos Pendientes")
    elif current_view == "Pedidos sin estado específico":
        filtered_df = df_pedidos[
            (df_pedidos['Inicio Trabajo'] == False) & 
            (df_pedidos['Trabajo Terminado'] == False) & 
            (df_pedidos['Pendiente'] == False)
        ]
        st.subheader("Pedidos sin Estado Específico")
    else:
        filtered_df = pd.DataFrame()
        st.warning("Vista no reconocida")

    # Mostrar resultados
    if not filtered_df.empty:
        # Columnas a mostrar (en orden específico)
        base_cols = [
            'ID', 'Producto', 'Cliente', 'Club', 'Telefono',
            'Fecha entrada', 'Fecha Salida', 'Precio'
        ]
        
        # Columnas de estado (si existen)
        estado_cols = [
            'Inicio Trabajo', 'Trabajo Terminado', 
            'Cobrado', 'Retirado', 'Pendiente'
        ]
        
        # Asegurar que las columnas existan
        cols_to_show = [col for col in base_cols if col in filtered_df.columns]
        cols_to_show += [col for col in estado_cols if col in filtered_df.columns]
        
        # Ordenar y mostrar
        filtered_df = filtered_df.sort_values('ID', ascending=False)
        st.dataframe(
            filtered_df[cols_to_show].style.apply(
                highlight_pedidos_rows,
                axis=1
            ),
            height=600
        )
    else:
        st.info(f"No hay pedidos en la categoría: {current_view}")