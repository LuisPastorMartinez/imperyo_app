import streamlit as st
import pandas as pd
from datetime import datetime

def show_analisis_productos_page(df_pedidos):
    """
    Muestra análisis de productos con selector de año y ambas columnas de precio.
    """
    st.header("📊 Análisis de Productos")
    st.write("---")

    if df_pedidos.empty:
        st.info("📭 No hay pedidos registrados aún.")
        return

    # Validar columna obligatoria
    if 'Producto' not in df_pedidos.columns:
        st.error("❌ Falta la columna 'Producto'.")
        return

    # --- Asegurar columna 'Año' ---
    if 'Año' not in df_pedidos.columns:
        st.warning("⚠️ Columna 'Año' no encontrada. Usando año actual para todos los pedidos.")
        df_pedidos['Año'] = datetime.now().year
    else:
        # Convertir a entero y limpiar
        df_pedidos['Año'] = pd.to_numeric(df_pedidos['Año'], errors='coerce').fillna(datetime.now().year).astype('int64')

    # --- Selector de año ---
    años_disponibles = sorted(df_pedidos['Año'].dropna().unique(), reverse=True)
    if not años_disponibles:
        años_disponibles = [datetime.now().year]
    
    año_seleccionado = st.selectbox(
        "📅 Selecciona el año para analizar:",
        options=años_disponibles,
        index=0,
        key="analisis_año_selector"
    )

    # --- Filtrar por año seleccionado ---
    df_filtrado = df_pedidos[df_pedidos['Año'] == año_seleccionado].copy()

    # --- Verificar qué columnas de precio existen ---
    tiene_precio = 'Precio' in df_filtrado.columns
    tiene_precio_factura = 'Precio Factura' in df_filtrado.columns

    if not tiene_precio and not tiene_precio_factura:
        st.error("❌ No se encontraron columnas de precio ('Precio' o 'Precio Factura').")
        return

    # --- Filtrar pedidos completados (opcional, pero recomendado) ---
    if {'Trabajo Terminado', 'Cobrado', 'Retirado'}.issubset(df_filtrado.columns):
        df_completados = df_filtrado[
            (df_filtrado['Trabajo Terminado'] == True) &
            (df_filtrado['Cobrado'] == True) &
            (df_filtrado['Retirado'] == True)
        ].copy()
        if df_completados.empty:
            st.warning(f"⚠️ No hay pedidos completados en {año_seleccionado}. Mostrando todos los pedidos del año.")
            df_completados = df_filtrado.copy()
    else:
        st.info(f"ℹ️ Mostrando todos los pedidos de {año_seleccionado} (no se pueden filtrar completados).")
        df_completados = df_filtrado.copy()

    # --- Asegurar que las columnas de precio sean numéricas ---
    if tiene_precio:
        df_completados['Precio'] = pd.to_numeric(df_completados['Precio'], errors='coerce').fillna(0)
    else:
        df_completados['Precio'] = 0

    if tiene_precio_factura:
        df_completados['Precio Factura'] = pd.to_numeric(df_completados['Precio Factura'], errors='coerce').fillna(0)
    else:
        df_completados['Precio Factura'] = 0

    # --- Calcular total ---
    df_completados['Total'] = df_completados['Precio'] + df_completados['Precio Factura']

    # --- Agrupar por producto ---
    if df_completados.empty:
        st.info(f"📭 No hay datos para analizar en {año_seleccionado}.")
        return

    analisis = df_completados.groupby('Producto').agg(
        Unidades=('Producto', 'count'),
        Suma_Precio=('Precio', 'sum'),
        Suma_Precio_Factura=('Precio Factura', 'sum'),
        Suma_Total=('Total', 'sum')
    ).reset_index()

    if analisis.empty:
        st.info(f"📭 No hay datos suficientes para el análisis en {año_seleccionado}.")
        return

    analisis = analisis.sort_values('Suma_Total', ascending=False).reset_index(drop=True)

    # --- Métricas ---
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

    # --- Tabla detallada ---
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