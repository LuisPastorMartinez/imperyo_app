import streamlit as st
import pandas as pd
import json

def explotar_productos_json(df):
    registros = []

    for _, row in df.iterrows():
        productos_raw = row.get('Productos')
        if not productos_raw:
            continue

        try:
            productos = json.loads(productos_raw) if isinstance(productos_raw, str) else productos_raw
        except Exception:
            continue

        for p in productos:
            registros.append({
                'Pedido': f"{row.get('ID')} / {row.get('Año')}",  # ✅ ID + AÑO
                'Cliente': row.get('Cliente'),
                'Club': row.get('Club'),
                'Producto': p.get('Producto'),
                'Tela': p.get('Tela'),
                'Cantidad': int(p.get('Cantidad', 1)),
                'Precio Unitario': float(p.get('PrecioUnitario', 0.0)),
                'Total': float(p.get('PrecioUnitario', 0.0)) * int(p.get('Cantidad', 1))
            })

    return pd.DataFrame(registros)

def show_analisis_productos_page(df_pedidos):
    st.header("📈 Análisis de Productos")
    st.write("---")

    if df_pedidos is None or df_pedidos.empty:
        st.info("No hay pedidos.")
        return

    # ✅ AÑOS DISPONIBLES
    años = sorted(df_pedidos['Año'].dropna().unique(), reverse=True)
    año = st.selectbox("📅 Año", años, index=0)

    df = df_pedidos[df_pedidos['Año'] == año].copy()
    if df.empty:
        st.info(f"No hay datos en {año}.")
        return

    df_prod = explotar_productos_json(df)
    if df_prod.empty:
        st.info("No hay productos.")
        return

    # --- KPIs ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("🧵 Productos vendidos", int(df_prod['Cantidad'].sum()))
    with c2:
        st.metric("📦 Pedidos", df_prod['Pedido'].nunique())
    with c3:
        st.metric("💰 Facturación", f"{df_prod['Total'].sum():.2f} €")

    st.write("---")

    # --- AGRUPADOS ---
    resumen = (
        df_prod
        .groupby(['Producto', 'Tela'], dropna=False)
        .agg({
            'Cantidad': 'sum',
            'Total': 'sum'
        })
        .reset_index()
        .sort_values('Cantidad', ascending=False)
    )

    st.subheader("Resumen por producto")
    st.dataframe(resumen, use_container_width=True, hide_index=True)

    st.subheader("Detalle por pedido")
    st.dataframe(df_prod, use_container_width=True, hide_index=True)
