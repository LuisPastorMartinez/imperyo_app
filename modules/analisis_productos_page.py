# Ver datos, analisis_productos_page.py
import streamlit as st
import pandas as pd
from datetime import datetime
import json

def explotar_productos_json(df_pedidos):
    """
    Convierte la columna 'Productos' (JSON) en filas individuales con Producto + Tela.
    Retorna un DataFrame con: Producto, Tela, Cantidad, Precio_Unitario, y metadatos del pedido.
    """
    filas_expandidas = []
    
    for idx, row in df_pedidos.iterrows():
        productos_json = row.get('Productos')
        if pd.isna(productos_json) or productos_json == "" or productos_json is None:
            continue
            
        try:
            if isinstance(productos_json, str):
                productos = json.loads(productos_json)
            elif isinstance(productos_json, list):
                productos = productos_json
            else:
                continue
                
            if not isinstance(productos, list):
                continue
                
            for item in productos:
                if not isinstance(item, dict):
                    continue
                    
                producto = item.get('Producto', 'Sin producto')
                tela = item.get('Tela', 'Sin tela')
                cantidad = item.get('Cantidad', 1)
                precio_unit = item.get('PrecioUnitario', 0.0)
                
                # Asegurar tipos
                try:
                    cantidad = int(cantidad)
                    precio_unit = float(precio_unit)
                except (ValueError, TypeError):
                    continue
                
                filas_expandidas.append({
                    'Producto': producto,
                    'Tela': tela,
                    'Cantidad': cantidad,
                    'Precio_Unitario': precio_unit,
                    'Subtotal': cantidad * precio_unit,
                    'ID_Pedido': row.get('ID', idx),
                    'Año': row.get('Año', datetime.now().year),
                    'Precio_Factura_Pedido': row.get('Precio Factura', 0.0),
                    'Precio_Pedido': row.get('Precio', 0.0)
                })
                
        except (json.JSONDecodeError, TypeError, KeyError, ValueError):
            continue
    
    if not filas_expandidas:
        return pd.DataFrame()
    
    return pd.DataFrame(filas_expandidas)

def show_analisis_productos_page(df_pedidos):
    """
    Análisis avanzado que explota el JSON de productos para mostrar combinaciones Producto + Tela.
    """
    st.header("📊 Análisis Detallado de Productos")
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

    # --- Explotar productos ---
    with st.spinner("🔍 Procesando productos..."):
        df_expandido = explotar_productos_json(df_filtrado)

    if df_expandido.empty:
        st.info(f"📭 No se encontraron productos válidos en {año_seleccionado}.")
        return

    # --- Crear columna combinada Producto + Tela ---
    df_expandido['Producto_Tela'] = df_expandido['Producto'] + " + " + df_expandido['Tela']

    # --- Agrupar por Producto + Tela ---
    analisis = df_expandido.groupby('Producto_Tela').agg(
        Unidades_Totales=('Cantidad', 'sum'),
        Pedidos_Distintos=('ID_Pedido', 'nunique'),
        Subtotal_Total=('Subtotal', 'sum')
    ).reset_index()

    # Extraer Producto y Tela separados para la tabla
    analisis[['Producto', 'Tela']] = analisis['Producto_Tela'].str.split(' \+ ', expand=True)

    # Ordenar por subtotal total
    analisis = analisis.sort_values('Subtotal_Total', ascending=False).reset_index(drop=True)

    # --- Métricas generales ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👕 Combinaciones", len(analisis))
    with col2:
        st.metric("🔢 Total Unidades", int(analisis['Unidades_Totales'].sum()))
    with col3:
        st.metric("💰 Ingresos por Productos", f"{analisis['Subtotal_Total'].sum():,.2f} €")

    st.write("---")

    # --- Producto + Tela más vendido y rentable ---
    if not analisis.empty:
        mas_vendido = analisis.loc[analisis['Unidades_Totales'].idxmax()]
        mas_rentable = analisis.iloc[0]
        
        col4, col5 = st.columns(2)
        with col4:
            st.success(f"🔝 **Más Vendido**\n\n**{mas_vendido['Producto']}**\n**Tela:** {mas_vendido['Tela']}\n{int(mas_vendido['Unidades_Totales'])} unidades")
        with col5:
            st.success(f"💎 **Más Rentable**\n\n**{mas_rentable['Producto']}**\n**Tela:** {mas_rentable['Tela']}\n{mas_rentable['Subtotal_Total']:,.2f} €")

    st.write("---")

    # --- Tabla detallada ---
    st.subheader(f"📋 Desglose por Producto + Tela ({año_seleccionado})")
    analisis_display = analisis.copy()
    analisis_display['Subtotal_Total_Formateado'] = analisis_display['Subtotal_Total'].apply(lambda x: f"{x:,.2f} €")
    
    st.dataframe(
        analisis_display[['Producto', 'Tela', 'Unidades_Totales', 'Pedidos_Distintos', 'Subtotal_Total_Formateado']].rename(columns={
            'Producto': 'Producto',
            'Tela': 'Tela',
            'Unidades_Totales': 'Unidades Totales',
            'Pedidos_Distintos': 'Pedidos',
            'Subtotal_Total_Formateado': 'Ingresos'
        }),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Unidades Totales": st.column_config.NumberColumn("👕 Unidades", format="%d"),
            "Pedidos": st.column_config.NumberColumn("📦 Pedidos", format="%d"),
            "Ingresos": st.column_config.TextColumn("💰 Ingresos", width="medium")
        }
    )

    # --- Análisis adicional: Top telas ---
    st.write("---")
    st.subheader("🧵 Análisis por Tela")
    analisis_telas = df_expandido.groupby('Tela').agg(
        Unidades=('Cantidad', 'sum'),
        Combinaciones=('Producto_Tela', 'nunique'),
        Ingresos=('Subtotal', 'sum')
    ).sort_values('Ingresos', ascending=False).reset_index()
    
    if not analisis_telas.empty:
        analisis_telas['Ingresos_Formateado'] = analisis_telas['Ingresos'].apply(lambda x: f"{x:,.2f} €")
        st.dataframe(
            analisis_telas[['Tela', 'Unidades', 'Combinaciones', 'Ingresos_Formateado']].rename(columns={
                'Tela': 'Tela',
                'Unidades': 'Unidades Totales',
                'Combinaciones': 'Productos Distintos',
                'Ingresos_Formateado': 'Ingresos Totales'
            }),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Unidades Totales": st.column_config.NumberColumn("👕 Unidades", format="%d"),
                "Productos Distintos": st.column_config.NumberColumn("👕 Productos", format="%d"),
                "Ingresos Totales": st.column_config.TextColumn("💰 Ingresos", width="medium")
            }
        )

    # --- Exportar ---
    st.write("---")
    if st.button("📥 Exportar análisis detallado", type="primary"):
        # Preparar DataFrame para exportar
        export_df = analisis[['Producto', 'Tela', 'Unidades_Totales', 'Pedidos_Distintos', 'Subtotal_Total']].copy()
        export_df.columns = ['Producto', 'Tela', 'Unidades Totales', 'Pedidos Distintos', 'Ingresos Totales']
        
        csv = export_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "⬇️ Descargar CSV",
            csv,
            f"analisis_detallado_{año_seleccionado}.csv",
            "text/csv",
            key='download-detailed-csv'
        )