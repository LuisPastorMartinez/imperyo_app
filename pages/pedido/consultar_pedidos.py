# pages/pedido/consultar_pedidos.py
import streamlit as st
import pandas as pd
from utils.data_utils import limpiar_telefono

def show_consult(df_pedidos, df_listas):
    st.subheader("Consultar Pedidos")

    # --- FILTROS ---
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        filtro_cliente = st.text_input("Filtrar por cliente", key="filtro_cliente_consulta")
    with col_f2:
        filtro_club = st.text_input("Filtrar por club", key="filtro_club_consulta")
    with col_f3:
        filtro_telefono = st.text_input("Filtrar por teléfono", key="filtro_telefono_consulta")
    with col_f4:
        filtro_estado = st.selectbox(
            "Filtrar por estado",
            options=["", "Pendiente", "Empezado", "Terminado", "Retirado", "Cobrado"],
            key="filtro_estado_consulta"
        )

    df_filtrado = df_pedidos.copy()

    # --- APLICAR FILTROS ---
    if filtro_cliente:
        df_filtrado = df_filtrado[df_filtrado['Cliente'].str.contains(filtro_cliente, case=False, na=False)]

    if filtro_club:
        df_filtrado = df_filtrado[df_filtrado['Club'].str.contains(filtro_club, case=False, na=False)]

    if filtro_telefono:
        # ✅ Limpiar y filtrar por teléfono
        filtro_limpio = ''.join(filter(str.isdigit, filtro_telefono))
        if filtro_limpio:
            df_filtrado['Telefono_limpio'] = df_filtrado['Telefono'].astype(str).str.replace(r'\D', '', regex=True)
            df_filtrado = df_filtrado[df_filtrado['Telefono_limpio'].str.contains(filtro_limpio, na=False)]
            df_filtrado = df_filtrado.drop(columns=['Telefono_limpio'])

    if filtro_estado:
        if filtro_estado == "Pendiente":
            df_filtrado = df_filtrado[df_filtrado['Pendiente'] == True]
        elif filtro_estado == "Empezado":
            df_filtrado = df_filtrado[df_filtrado['Inicio Trabajo'] == True]
        elif filtro_estado == "Terminado":
            df_filtrado = df_filtrado[df_filtrado['Trabajo Terminado'] == True]
        elif filtro_estado == "Retirado":
            df_filtrado = df_filtrado[df_filtrado['Retirado'] == True]
        elif filtro_estado == "Cobrado":
            df_filtrado = df_filtrado[df_filtrado['Cobrado'] == True]

    # --- MOSTRAR RESULTADOS ---
    if not df_filtrado.empty:
        df_display = df_filtrado.copy()

        # Formatear fechas
        for col in ['Fecha entrada', 'Fecha Salida']:
            if col in df_display.columns:
                df_display[col] = pd.to_datetime(df_display[col], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')

        # Asegurar tipos numéricos
        if 'ID' in df_display.columns:
            df_display['ID'] = pd.to_numeric(df_display['ID'], errors='coerce').fillna(0).astype('int64')
        if 'Precio' in df_display.columns:
            df_display['Precio'] = pd.to_numeric(df_display['Precio'], errors='coerce').fillna(0.0)

        # Asegurar booleanos
        for col in ['Pendiente', 'Inicio Trabajo', 'Trabajo Terminado', 'Retirado', 'Cobrado']:
            if col in df_display.columns:
                df_display[col] = df_display[col].fillna(False).astype(bool)

        # ✅ Columnas a mostrar — ¡AHORA INCLUYE 'Productos'!
        columnas_mostrar = [
            'ID', 'Productos', 'Cliente', 'Club', 'Telefono',  # ✅ 'Productos' añadido aquí
            'Fecha entrada', 'Fecha Salida', 'Precio',
            'Pendiente', 'Inicio Trabajo', 'Trabajo Terminado', 'Retirado', 'Cobrado'
        ]
        columnas_disponibles = [col for col in columnas_mostrar if col in df_display.columns]

        # Ordenar por ID descendente
        df_display = df_display.sort_values('ID', ascending=False)

        # Mostrar tabla
        st.dataframe(df_display[columnas_disponibles], height=600, use_container_width=True)
        st.caption(f"Mostrando {len(df_filtrado)} de {len(df_pedidos)} pedidos")

        # ✅ Botón para exportar a CSV
        st.download_button(
            "📥 Descargar como CSV",
            df_filtrado.to_csv(index=False).encode('utf-8'),
            "pedidos_filtrados.csv",
            "text/csv",
            key='download-csv-consulta'
        )
    else:
        st.info("No se encontraron pedidos con los filtros aplicados")