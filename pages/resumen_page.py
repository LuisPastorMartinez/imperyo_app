# pages/resumen_page.py
import streamlit as st
import pandas as pd

def highlight_pedidos_rows(row):
    """Función para resaltar filas en la tabla de pedidos"""
    styles = [''] * len(row)
    trabajo_terminado = row.get('Trabajo Terminado', False)
    cobrado = row.get('Cobrado', False)
    retirado = row.get('Retirado', False)
    pendiente = row.get('Pendiente', False)
    empezado = row.get('Inicio Trabajo', False)

    if trabajo_terminado and cobrado and retirado and not pendiente:
        styles = ['background-color: #00B050'] * len(row)
    elif empezado and not pendiente:
        styles = ['background-color: #0070C0'] * len(row)
    elif trabajo_terminado and not pendiente:
        styles = ['background-color: #FFC000'] * len(row)
    elif pendiente:
        styles = ['background-color: #FF00FF'] * len(row)

    return styles

def show_resumen_page(df_pedidos, current_view):
    """Muestra la página de resumen de pedidos"""
    st.header("Resumen de Pedidos")
    filtered_df = pd.DataFrame()

    # Filtramos los datos según la vista seleccionada
    if current_view == "Todos los Pedidos":
        filtered_df = df_pedidos
        st.subheader("Todos los Pedidos")
    elif current_view == "Trabajos Empezados":
        filtered_df = df_pedidos[df_pedidos['Inicio Trabajo'] == True and ['Pendiente'] == false]
        st.subheader("Pedidos con 'Inicio Trabajo'")
    elif current_view == "Trabajos Terminados":
        filtered_df = df_pedidos[df_pedidos['Trabajo Terminado'] == True]
        st.subheader("Pedidos con 'Trabajo Terminado'")
    elif current_view == "Pedidos Pendientes":
        filtered_df = df_pedidos[df_pedidos['Pendiente'] == True]
        st.subheader("Pedidos con 'Pendiente'")
    elif current_view == "Pedidos sin estado específico":
        filtered_df = df_pedidos[
            (df_pedidos['Inicio Trabajo'] == False) &
            (df_pedidos['Trabajo Terminado'] == False) &
            (df_pedidos['Pendiente'] == False)
        ]
        st.subheader("Pedidos sin Estado Específico")

    # Mostramos los datos filtrados
    if not filtered_df.empty:
        filtered_df_sorted = filtered_df.sort_values(by='ID', ascending=False)
        column_order = [
            'ID', 'Producto', 'Cliente', 'Club', 'Telefono', 'Breve Descripción',
            'Fecha entrada', 'Fecha Salida', 'Precio', 'Precio Factura',
            'Tipo de pago', 'Adelanto', 'Observaciones'
        ]
        remaining_cols = [col for col in filtered_df_sorted.columns if col not in column_order]
        final_order = column_order + remaining_cols
        df_to_show = filtered_df_sorted[final_order]
        
        st.dataframe(df_to_show.style.apply(highlight_pedidos_rows, axis=1))
    else:
        st.info(f"No hay pedidos en la categoría: {current_view}")