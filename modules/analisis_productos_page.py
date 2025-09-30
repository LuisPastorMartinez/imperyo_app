import streamlit as st
import pandas as pd

def show_analisis_productos_page(df_pedidos):
    """
    Muestra un análisis detallado de productos: unidades, ingresos, más vendido y más rentable.
    """
    st.header("📊 Análisis de Productos")
    st.write("---")

    if df_pedidos.empty:
        st.info("📭 No hay pedidos registrados aún.")
        return

    # Validar columnas necesarias
    if 'Producto' not in df_pedidos.columns:
        st.error("❌ La columna 'Producto' no existe en los pedidos.")
        return
    if 'Precio' not in df_pedidos.columns:
        st.error("❌ La columna 'Precio' no existe en los pedidos.")
        return

    # --- Filtrar pedidos completados (Terminado + Cobrado + Retirado) ---
    df_completados = df_pedidos[
        (df_pedidos['Trabajo Terminado'] == True) &
        (df_pedidos['Cobrado'] == True) &
        (df_pedidos['Retirado'] == True)
    ].copy()

    if df_completados.empty:
        st.warning("⚠️ No hay pedidos completados. Mostrando todos los pedidos para el análisis.")
        df_completados = df_pedidos.copy()

    # --- Agrupar por producto ---
    analisis = df_completados.groupby('Producto').agg(
        Unidades=('Producto', 'count'),
        Ingresos=('Precio', 'sum')
    ).reset_index()

    if analisis.empty:
        st.info("📭 No hay datos suficientes para el análisis.")
        return

    # Ordenar por ingresos (más rentable primero)
    analisis = analisis.sort_values('Ingresos', ascending=False).reset_index(drop=True)

    # --- Métricas generales ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👕 Productos Únicos", len(analisis))
    with col2:
        st.metric("🔢 Total Unidades", int(analisis['Unidades'].sum()))
    with col3:
        st.metric("💰 Ingresos Totales", f"{analisis['Ingresos'].sum():,.2f} €")

    st.write("---")

    # --- Producto más vendido y más rentable ---
    mas_vendido = analisis.loc[analisis['Unidades'].idxmax()]
    mas_rentable = analisis.iloc[0]  # Ya está ordenado por ingresos

    col4, col5 = st.columns(2)
    with col4:
        st.success(f"🔝 **Más Vendido**\n\n**{mas_vendido['Producto']}**\n{int(mas_vendido['Unidades'])} unidades")
    with col5:
        st.success(f"💎 **Más Rentable**\n\n**{mas_rentable['Producto']}**\n{mas_rentable['Ingresos']:,.2f} €")

    st.write("---")

    # --- Tabla detallada ---
    st.subheader("📋 Desglose por Producto")
    analisis_display = analisis.copy()
    analisis_display['Ingresos Formateado'] = analisis_display['Ingresos'].apply(lambda x: f"{x:,.2f} €")
    
    st.dataframe(
        analisis_display[['Producto', 'Unidades', 'Ingresos Formateado']].rename(columns={
            'Producto': 'Producto',
            'Unidades': 'Unidades Vendidas',
            'Ingresos Formateado': 'Ingresos Totales'
        }),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Unidades Vendidas": st.column_config.NumberColumn("👕 Unidades", format="%d"),
            "Ingresos Totales": st.column_config.TextColumn("💰 Ingresos", width="medium")
        }
    )

    # --- Botón de exportación (opcional) ---
    st.write("---")
    csv = analisis.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Descargar análisis como CSV",
        csv,
        "analisis_productos.csv",
        "text/csv",
        key='download-csv'
    )