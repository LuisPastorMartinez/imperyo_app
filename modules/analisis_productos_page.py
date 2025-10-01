import streamlit as st
import pandas as pd
from datetime import datetime
import json

def extraer_primer_producto(productos_json):
    """Extrae el nombre del primer producto desde JSON o devuelve el valor original."""
    if pd.isna(productos_json) or productos_json == "" or productos_json is None:
        return "Sin producto"
    
    try:
        # Si es string JSON
        if isinstance(productos_json, str):
            productos = json.loads(productos_json)
        # Si ya es lista (raro, pero posible)
        elif isinstance(productos_json, list):
            productos = productos_json
        else:
            return str(productos_json)
        
        if isinstance(productos, list) and len(productos) > 0:
            primer_producto = productos[0]
            if isinstance(primer_producto, dict):
                return primer_producto.get("Producto", "Sin producto")
            else:
                return str(primer_producto)
        else:
            return "Sin producto"
    except (json.JSONDecodeError, TypeError, KeyError, IndexError):
        return str(productos_json) if not pd.isna(productos_json) else "Sin producto"

def show_analisis_productos_page(df_pedidos):
    """
    Muestra análisis de productos compatible con pedidos antiguos (columna 'Producto') 
    y nuevos (columna 'Productos' en JSON).
    """
    st.header("📊 Análisis de Productos")
    st.write("---")

    if df_pedidos.empty:
        st.info("📭 No hay pedidos registrados aún.")
        return

    # --- Asegurar columna 'Año' ---
    if 'Año' not in df_pedidos.columns:
        st.warning("⚠️ Columna 'Año' no encontrada. Usando año actual.")
        df_pedidos['Año'] = datetime.now().year
    else:
        df_pedidos['Año'] = pd.to_numeric(df_pedidos['Año'], errors='coerce').fillna(datetime.now().year).astype('int64')

    # --- Selector de año ---
    años_disponibles = sorted(df_pedidos['Año'].dropna().unique(), reverse=True)
    año_seleccionado = st.selectbox(
        "📅 Selecciona el año para analizar:",
        options=años_disponibles if años_disponibles else [datetime.now().year],
        index=0,
        key="analisis_año_selector"
    )

    df_filtrado = df_pedidos[df_pedidos['Año'] == año_seleccionado].copy()

    # --- Crear columna 'Producto_Unificado' ---
    if 'Producto' in df_filtrado.columns and 'Productos' in df_filtrado.columns:
        # Usar 'Producto' si está disponible, si no, extraer de 'Productos'
        df_filtrado['Producto_Unificado'] = df_filtrado.apply(
            lambda row: row['Producto'] if pd.notna(row['Producto']) and row['Producto'] != "" else extraer_primer_producto(row['Productos']),
            axis=1
        )
    elif 'Producto' in df_filtrado.columns:
        df_filtrado['Producto_Unificado'] = df_filtrado['Producto'].fillna("Sin producto")
    elif 'Productos' in df_filtrado.columns:
        df_filtrado['Producto_Unificado'] = df_filtrado['Productos'].apply(extraer_primer_producto)
    else:
        st.error("❌ No se encontraron columnas de producto ('Producto' o 'Productos').")
        return

    # --- Verificar columnas de precio ---
    tiene_precio = 'Precio' in df_filtrado.columns
    tiene_precio_factura = 'Precio Factura' in df_filtrado.columns

    if not tiene_precio and not tiene_precio_factura:
        st.error("❌ No se encontraron columnas de precio.")
        return

    # --- Filtrar pedidos completados ---
    if {'Trabajo Terminado', 'Cobrado', 'Retirado'}.issubset(df_filtrado.columns):
        df_completados = df_filtrado[
            (df_filtrado['Trabajo Terminado'] == True) &
            (df_filtrado['Cobrado'] == True) &
            (df_filtrado['Retirado'] == True)
        ].copy()
        if df_completados.empty:
            st.warning(f"⚠️ No hay pedidos completados en {año_seleccionado}. Mostrando todos.")
            df_completados = df_filtrado.copy()
    else:
        df_completados = df_filtrado.copy()

    # --- Preparar precios ---
    for col in ['Precio', 'Precio Factura']:
        if col in df_completados.columns:
            df_completados[col] = pd.to_numeric(df_completados[col], errors='coerce').fillna(0)
        else:
            df_completados[col] = 0

    df_completados['Total'] = df_completados['Precio'] + df_completados['Precio Factura']

    # --- Agrupar por producto unificado ---
    if df_completados.empty:
        st.info(f"📭 No hay datos en {año_seleccionado}.")
        return

    analisis = df_completados.groupby('Producto_Unificado').agg(
        Unidades=('Producto_Unificado', 'count'),
        Suma_Precio=('Precio', 'sum'),
        Suma_Precio_Factura=('Precio Factura', 'sum'),
        Suma_Total=('Total', 'sum')
    ).reset_index()

    if analisis.empty or analisis['Suma_Total'].sum() == 0:
        st.info(f"📭 No hay datos suficientes en {año_seleccionado}.")
        return

    analisis = analisis.sort_values('Suma_Total', ascending=False).reset_index(drop=True)
    analisis.rename(columns={'Producto_Unificado': 'Producto'}, inplace=True)

    # --- Mostrar resultados ---
    col1, col2 = st.columns(2)
    with col1:
        st.metric("👕 Productos", len(analisis))
        st.metric("🔢 Unidades", int(analisis['Unidades'].sum()))
    with col2:
        if tiene_precio:
            st.metric("💶 Precio Base", f"{analisis['Suma_Precio'].sum():,.2f} €")
        if tiene_precio_factura:
            st.metric("🧾 Precio Factura", f"{analisis['Suma_Precio_Factura'].sum():,.2f} €")

    st.metric("💰 **INGRESOS TOTALES**", f"{analisis['Suma_Total'].sum():,.2f} €")

    # --- Producto más vendido y rentable ---
    if not analisis.empty:
        mas_vendido = analisis.loc[analisis['Unidades'].idxmax()]
        mas_rentable = analisis.iloc[0]
        
        col3, col4 = st.columns(2)
        with col3:
            st.success(f"🔝 **Más Vendido**\n\n**{mas_vendido['Producto']}**\n{int(mas_vendido['Unidades'])} unidades")
        with col4:
            st.success(f"💎 **Más Rentable**\n\n**{mas_rentable['Producto']}**\n{mas_rentable['Suma_Total']:,.2f} €")

    # --- Tabla ---
    st.subheader(f"📋 Desglose por Producto ({año_seleccionado})")
    cols_mostrar = ['Producto', 'Unidades']
    if tiene_precio:
        cols_mostrar.append('Suma_Precio')
    if tiene_precio_factura:
        cols_mostrar.append('Suma_Precio_Factura')
    cols_mostrar.append('Suma_Total')

    analisis_display = analisis[cols_mostrar].copy()
    for col in ['Suma_Precio', 'Suma_Precio_Factura', 'Suma_Total']:
        if col in analisis_display.columns:
            analisis_display[col] = analisis_display[col].apply(lambda x: f"{x:,.2f} €")

    st.dataframe(
        analisis_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Producto": "Producto",
            "Unidades": st.column_config.NumberColumn("👕 Unidades", format="%d"),
            "Suma_Precio": "💶 Precio Base",
            "Suma_Precio_Factura": "🧾 Precio Factura",
            "Suma_Total": "💰 Total"
        }
    )

    # --- Exportar ---
    st.write("---")
    csv = analisis.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Descargar análisis",
        csv,
        f"analisis_productos_{año_seleccionado}.csv",
        "text/csv"
    )