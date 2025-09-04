# pages/pedido/consultar_pedidos.py
import streamlit as st
import pandas as pd
from .helpers import convert_to_firestore_type

def show_consult(df_pedidos, df_listas):
    st.subheader("Consultar Pedidos")

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        filtro_cliente = st.text_input("Filtrar por cliente")
    with col_f2:
        filtro_club = st.text_input("Filtrar por club")
    with col_f3:
        filtro_telefono = st.text_input("Filtrar por teléfono")
    with col_f4:
        filtro_estado = st.selectbox("Filtrar por estado", options=["", "Pendiente", "Empezado", "Terminado", "Retirado"], key="filtro_estado_consulta")

    df_filtrado = df_pedidos.copy()

    if filtro_cliente:
        df_filtrado = df_filtrado[df_filtrado['Cliente'].str.contains(filtro_cliente, case=False, na=False)]
    if filtro_club:
        df_filtrado = df_filtrado[df_filtrado['Club'].str.contains(filtro_club, case=False, na=False)]
    if filtro_telefono:
        df_filtrado = df_filtrado[df_filtrado['Telefono'].astype(str).str.contains(filtro_telefono, na=False)]
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
        for col in ['Fecha entrada', 'Fecha Salida']:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(lambda x: str(x)[:10] if pd.notna(x) and str(x) != 'NaT' else '')
        if 'ID' in df_display.columns:
            df_display['ID'] = pd.to_numeric(df_display['ID'], errors='coerce').fillna(0).astype('int64')
        if 'Precio' in df_display.columns:
            df_display['Precio'] = pd.to_numeric(df_display['Precio'], errors='coerce').fillna(0.0)
        for col in ['Pendiente', 'Inicio Trabajo', 'Trabajo Terminado', 'Retirado']:
            if col in df_display.columns:
                df_display[col] = df_display[col].fillna(False).astype(bool)

        columnas_mostrar = ['ID', 'Producto', 'Cliente', 'Club', 'Telefono', 'Fecha entrada', 'Fecha Salida', 'Precio', 'Pendiente', 'Inicio Trabajo', 'Trabajo Terminado', 'Retirado']
        columnas_disponibles = [col for col in columnas_mostrar if col in df_display.columns]

        st.dataframe(df_display[columnas_disponibles].sort_values('ID', ascending=False), height=600, use_container_width=True)
        st.caption(f"Mostrando {len(df_filtrado)} de {len(df_pedidos)} pedidos")
    else:
        st.info("No se encontraron pedidos con los filtros aplicados")
