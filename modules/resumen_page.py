# modules/resumen_page.py
import streamlit as st
import pandas as pd
import json
from datetime import datetime

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

def formatear_primer_producto(productos_json):
    """Muestra solo el primer producto en formato resumido + '+P' si hay más."""
    try:
        if isinstance(productos_json, str):
            productos = json.loads(productos_json)
        elif isinstance(productos_json, list):
            productos = productos_json
        else:
            return "Sin productos"

        if not productos:
            return "Sin productos"

        p = productos[0]
        nombre = p.get("Producto", "")
        tela = p.get("Tela", "")
        cantidad = int(p.get("Cantidad", 1))
        precio_total = float(p.get("PrecioUnitario", 0.0)) * cantidad

        resumen = nombre
        if tela:
            resumen += f" ({tela})"
        resumen += f" x{cantidad} → {precio_total:.2f}€"

        if len(productos) > 1:
            resumen += " +P"

        return resumen

    except Exception:
        return "Error"

def show_resumen_page(df_pedidos, current_view):
    """Muestra la página de resumen con estilo de 'Consultar Pedidos'"""
    st.header("Resumen de Pedidos")
    
    # ✅ Convertir columna 'Año' a entero
    if not df_pedidos.empty and 'Año' in df_pedidos.columns:
        df_pedidos['Año'] = pd.to_numeric(df_pedidos['Año'], errors='coerce').fillna(2025).astype('int64')

    # ✅ Selector de año
    año_actual = datetime.now().year

    if not df_pedidos.empty:
        años_disponibles = sorted(df_pedidos[df_pedidos['Año'] <= año_actual]['Año'].dropna().unique(), reverse=True)
    else:
        años_disponibles = [año_actual]

    año_seleccionado = st.sidebar.selectbox("📅 Año", años_disponibles, key="resumen_año_select")

    # ✅ Filtrar por año primero
    df_pedidos_filtrado = df_pedidos[df_pedidos['Año'] == año_seleccionado].copy() if df_pedidos is not None else None

    if df_pedidos_filtrado is None or df_pedidos_filtrado.empty:
        st.info(f"No hay pedidos en el año {año_seleccionado}")
        return

    # --- FILTROS POR VISTA ---
    if current_view == "Todos los Pedidos":
        filtered_df = df_pedidos_filtrado.copy()
        st.subheader(f"Todos los Pedidos ({año_seleccionado})")
    elif current_view == "Trabajos Empezados":
        filtered_df = df_pedidos_filtrado[
            (df_pedidos_filtrado['Inicio Trabajo'] == True) & 
            (df_pedidos_filtrado['Pendiente'] == False)
        ]
        st.subheader(f"Trabajos Empezados (no pendientes) - {año_seleccionado}")  
    elif current_view == "Trabajos Terminados":
        filtered_df = df_pedidos_filtrado[
            (df_pedidos_filtrado['Trabajo Terminado'] == True) & 
            (df_pedidos_filtrado['Pendiente'] == False)
        ]
        st.subheader(f"Trabajos Terminados (no pendientes) - {año_seleccionado}")
    elif current_view == "Pedidos Pendientes":
        filtered_df = df_pedidos_filtrado[df_pedidos_filtrado['Pendiente'] == True]
        st.subheader(f"Pedidos Pendientes (morado siempre) - {año_seleccionado}")
    elif current_view == "Pedidos sin estado específico":
        filtered_df = df_pedidos_filtrado[
            (df_pedidos_filtrado['Inicio Trabajo'] == False) & 
            (df_pedidos_filtrado['Trabajo Terminado'] == False) & 
            (df_pedidos_filtrado['Pendiente'] == False)
        ]
        st.subheader(f"Pedidos sin Estado Específico - {año_seleccionado}")
    else:
        filtered_df = pd.DataFrame()
        st.warning("Vista no reconocida")

    # --- MOSTRAR RESULTADOS ---
    if not filtered_df.empty:
        df_display = filtered_df.copy()

        # ✅ Formatear columna Productos
        if 'Productos' in df_display.columns:
            df_display['Productos'] = df_display['Productos'].apply(formatear_primer_producto)

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

        # ✅ Generar columna "Estado" con iconos + ✔️ COMPLETADO"
        def estado_a_icono(row):
            iconos = []
            if row.get('Pendiente', False):
                iconos.append("📌")
            if row.get('Inicio Trabajo', False):
                iconos.append("🔵")
            if row.get('Trabajo Terminado', False):
                iconos.append("✅")
            if row.get('Retirado', False):
                iconos.append("📦")
            if row.get('Cobrado', False):
                iconos.append("💰")
            
            # ✅ Si está Terminado + Cobrado + Retirado → añadir "✔️ COMPLETADO"
            if (row.get('Trabajo Terminado', False) and
                row.get('Cobrado', False) and
                row.get('Retirado', False)):
                iconos.append("✔️ COMPLETADO")

            return " ".join(iconos)

        df_display['Estado'] = df_display.apply(estado_a_icono, axis=1)

        # ✅ Columnas a mostrar
        columnas_mostrar = [
            'ID', 'Productos', 'Cliente', 'Club', 'Telefono',
            'Fecha entrada', 'Fecha Salida', 'Precio', 'Estado'
        ]
        columnas_disponibles = [col for col in columnas_mostrar if col in df_display.columns]

        # Ordenar por ID descendente
        df_display = df_display.sort_values('ID', ascending=False)

        # ✅ Mostrar tabla con estilo de "Consultar Pedidos"
        st.dataframe(
            df_display[columnas_disponibles].style.apply(highlight_pedidos_rows, axis=1),
            column_config={
                "Productos": st.column_config.TextColumn(
                    "Productos",
                    help="Primer producto del pedido. '+P' indica que hay más productos.",
                    width="medium"
                ),
                "Precio": st.column_config.NumberColumn(
                    "Precio (€)",
                    format="%.2f €",
                    width="small"
                ),
                "Estado": st.column_config.TextColumn(
                    "Estado",
                    help="📌 Pendiente | 🔵 Empezado | ✅ Terminado | 📦 Retirado | 💰 Cobrado | ✔️ COMPLETADO",
                    width="medium"
                ),
            },
            height=600,
            use_container_width=True,
            hide_index=True
        )

        st.caption(f"Mostrando {len(filtered_df)} de {len(df_pedidos_filtrado)} pedidos del año {año_seleccionado}")

        # ✅ Mostrar contador de pedidos COMPLETADOS
        completados = filtered_df[
            (filtered_df['Trabajo Terminado'] == True) &
            (filtered_df['Cobrado'] == True) &
            (filtered_df['Retirado'] == True)
        ]
        st.info(f"✅ Pedidos COMPLETADOS en esta vista: **{len(completados)}**")

    else:
        st.info(f"No hay pedidos en la categoría: {current_view} para el año {año_seleccionado}")