# pages/resumen_page.py (o modules/resumen_page.py si renombraste)
import streamlit as st
import pandas as pd

def highlight_pedidos_rows(row):
    """Función para resaltar filas según su estado"""
    styles = [''] * len(row)
    
    pendiente = row.get('Pendiente', False)
    terminado = row.get('Trabajo Terminado', False)
    retirado = row.get('Retirado', False)
    cobrado = row.get('Cobrado', False)
    
    # ✅ Nueva lógica: si está Terminado + Cobrado + Retirado → verde
    if terminado and cobrado and retirado:
        styles = ['background-color: #00B050'] * len(row)  # Verde para completado
    elif pendiente:
        styles = ['background-color: #FF00FF'] * len(row)  # Morado para pendientes
    elif terminado and retirado:
        styles = ['background-color: #00B050'] * len(row)  # Verde para terminados+retirados
    elif terminado:
        styles = ['background-color: #FFC000'] * len(row)  # Amarillo para solo terminados
    elif row.get('Inicio Trabajo', False):
        styles = ['background-color: #0070C0'] * len(row)  # Azul para empezados no pendientes

    return styles

def show_resumen_page(df_pedidos, current_view):
    """Muestra la página de resumen con filtros mejorados"""
    st.header("Resumen de Pedidos")
    
    # Filtrado mejorado con prioridad a pendientes
    if current_view == "Todos los Pedidos":
        filtered_df = df_pedidos.copy()
        st.subheader("Todos los Pedidos")
    elif current_view == "Trabajos Empezados":
        filtered_df = df_pedidos[
            (df_pedidos['Inicio Trabajo'] == True) & 
            (df_pedidos['Pendiente'] == False)  # Excluye pendientes
        ]
        st.subheader("Trabajos Empezados (no pendientes)")  
    elif current_view == "Trabajos Terminados":
        filtered_df = df_pedidos[
            (df_pedidos['Trabajo Terminado'] == True) & 
            (df_pedidos['Pendiente'] == False)  # Excluye pendientes
        ]
        st.subheader("Trabajos Terminados (no pendientes)")
    elif current_view == "Pedidos Pendientes":
        filtered_df = df_pedidos[df_pedidos['Pendiente'] == True]
        st.subheader("Pedidos Pendientes (morado siempre)")
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
        # Columnas base + columnas de estado
        column_order = [
            'ID', 'Producto', 'Cliente', 'Club', 'Telefono',
            'Fecha entrada', 'Fecha Salida', 'Precio',
            'Inicio Trabajo', 'Trabajo Terminado', 'Retirado', 'Pendiente', 'Cobrado'
        ]
        
        # Filtrar columnas existentes
        cols_to_show = [col for col in column_order if col in filtered_df.columns]
        
        # Ordenar por ID descendente y mostrar
        st.dataframe(
            filtered_df[cols_to_show]
            .sort_values('ID', ascending=False)
            .style.apply(highlight_pedidos_rows, axis=1),
            height=600,
            use_container_width=True
        )
        
        # ✅ Mostrar contador de pedidos COMPLETADOS (Terminado + Cobrado + Retirado)
        completados = filtered_df[
            (filtered_df['Trabajo Terminado'] == True) &
            (filtered_df['Cobrado'] == True) &
            (filtered_df['Retirado'] == True)
        ]
        st.info(f"✅ Pedidos COMPLETADOS en esta vista: **{len(completados)}**")
    else:
        st.info(f"No hay pedidos en la categoría: {current_view}")