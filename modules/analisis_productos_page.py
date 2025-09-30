import streamlit as st
import pandas as pd

def show_analisis_productos_page(df_pedidos):
    """
    Muestra análisis con ambas columnas de precio: 'Precio' y 'Precio Factura'
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

    # --- Verificar qué columnas de precio existen ---
    tiene_precio = 'Precio' in df_pedidos.columns
    tiene_precio_factura = 'Precio Factura' in df_pedidos.columns

    if not tiene_precio and not tiene_precio_factura:
        st.error("❌ No se encontraron columnas de precio ('Precio' o 'Precio Factura').")
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
    analisis = df_completados.groupby('Producto').agg(
        Unidades=('Producto', 'count'),
        Suma_Precio=('Precio', 'sum'),
        Suma_Precio_Factura=('Precio Factura', 'sum'),
        Suma_Total=('Total', 'sum')
    ).reset_index()

    if analisis.empty:
        st.info("📭 No hay datos para analizar.")
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
    mas_vendido = analisis.loc[analisis['Unidades'].idxmax()]
    mas_rentable = analisis.iloc[0]

    col3, col4 = st.columns(2)
    with col3:
        st.success(f"🔝 **Más Vendido**\n\n**{mas_vendido['Producto']}**\n{int(mas_vendido['Unidades'])} unidades")
    with col4:
        st.success(f"💎 **Más Rentable**\n\n**{mas_rentable['Producto']}**\n{mas_rentable['Suma_Total']:,.2f} €")

    # --- Tabla detallada ---
    st.subheader("📋 Desglose por Producto")
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
        "analisis_productos.csv",
        "text/csv"
    )