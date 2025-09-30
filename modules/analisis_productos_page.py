import streamlit as st
import pandas as pd

def show_analisis_productos_page(df_pedidos):
    """
    Muestra un análisis detallado con columnas separadas para 'Precio', 'Precio Factura' y su suma total.
    """
    st.header("📊 Análisis de Productos")
    st.write("---")

    if df_pedidos.empty:
        st.info("📭 No hay pedidos registrados aún.")
        return

    # Validar columnas obligatorias
    if 'Producto' not in df_pedidos.columns:
        st.error("❌ Falta la columna 'Producto'.")
        return
        
    if 'Precio' not in df_pedidos.columns:
        st.error("❌ Falta la columna 'Precio'.")
        return
        
    if 'Precio Factura' not in df_pedidos.columns:
        st.error("❌ Falta la columna 'Precio Factura'.")
        return

    # --- Filtrar pedidos completados ---
    df_completados = df_pedidos[
        (df_pedidos['Trabajo Terminado'] == True) &
        (df_pedidos['Cobrado'] == True) &
        (df_pedidos['Retirado'] == True)
    ].copy()

    if df_completados.empty:
        st.warning("⚠️ No hay pedidos completados. Mostrando todos los pedidos.")
        df_completados = df_pedidos.copy()

    # --- Asegurar que ambas columnas sean numéricas ---
    for col in ['Precio', 'Precio Factura']:
        df_completados[col] = pd.to_numeric(df_completados[col], errors='coerce').fillna(0)

    # --- Calcular columna total ---
    df_completados['Total'] = df_completados['Precio'] + df_completados['Precio Factura']

    # --- Agrupar por producto ---
    analisis = df_completados.groupby('Producto').agg(
        Unidades=('Producto', 'count'),
        Suma_Precio=('Precio', 'sum'),
        Suma_Precio_Factura=('Precio Factura', 'sum'),
        Suma_Total=('Total', 'sum')
    ).reset_index()

    if analisis.empty:
        st.info("📭 No hay datos para analizar.")
        return

    # Ordenar por suma total (más rentable primero)
    analisis = analisis.sort_values('Suma_Total', ascending=False).reset_index(drop=True)

    # --- Métricas generales ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👕 Productos", len(analisis))
    with col2:
        st.metric("🔢 Unidades", int(analisis['Unidades'].sum()))
    with col3:
        st.metric("💶 Precio Base", f"{analisis['Suma_Precio'].sum():,.2f} €")
    with col4:
        st.metric("🧾 Precio Factura", f"{analisis['Suma_Precio_Factura'].sum():,.2f} €")

    st.write("---")
    st.metric("💰 **INGRESOS TOTALES**", f"{analisis['Suma_Total'].sum():,.2f} €")

    st.write("---")

    # --- Producto más vendido y más rentable ---
    mas_vendido = analisis.loc[analisis['Unidades'].idxmax()]
    mas_rentable = analisis.iloc[0]

    col5, col6 = st.columns(2)
    with col5:
        st.success(f"🔝 **Más Vendido**\n\n**{mas_vendido['Producto']}**\n{int(mas_vendido['Unidades'])} unidades")
    with col6:
        st.success(f"💎 **Más Rentable**\n\n**{mas_rentable['Producto']}**\n{mas_rentable['Suma_Total']:,.2f} €")

    st.write("---")

    # --- Tabla detallada ---
    st.subheader("📋 Desglose por Producto")
    analisis_display = analisis.copy()
    for col in ['Suma_Precio', 'Suma_Precio_Factura', 'Suma_Total']:
        analisis_display[col] = analisis_display[col].apply(lambda x: f"{x:,.2f} €")

    st.dataframe(
        analisis_display[[
            'Producto', 'Unidades', 
            'Suma_Precio', 'Suma_Precio_Factura', 'Suma_Total'
        ]].rename(columns={
            'Producto': 'Producto',
            'Unidades': 'Unidades Vendidas',
            'Suma_Precio': 'Total Precio Base',
            'Suma_Precio_Factura': 'Total Precio Factura',
            'Suma_Total': 'Ingresos Totales'
        }),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Unidades Vendidas": st.column_config.NumberColumn("👕 Unidades", format="%d"),
            "Total Precio Base": st.column_config.TextColumn("💶 Base", width="small"),
            "Total Precio Factura": st.column_config.TextColumn("🧾 Factura", width="small"),
            "Ingresos Totales": st.column_config.TextColumn("💰 Total", width="medium")
        }
    )

    # --- Botón de exportación ---
    st.write("---")
    csv = analisis.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Descargar análisis como CSV",
        csv,
        "analisis_productos_completo.csv",
        "text/csv"
    )