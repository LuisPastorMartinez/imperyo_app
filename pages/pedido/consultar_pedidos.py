# pages/pedido/consultar_pedidos.py
import streamlit as st
import pandas as pd
import json
from utils.data_utils import limpiar_telefono

def formatear_primer_producto(productos_json):
    """Muestra solo el primer producto en formato resumido."""
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
            resumen += f" +{len(productos)-1}"

        return resumen

    except Exception:
        return "Error"

def mostrar_detalle_productos(productos_json, key_suffix):
    """Muestra todos los productos en un expander."""
    try:
        if isinstance(productos_json, str):
            productos = json.loads(productos_json)
        elif isinstance(productos_json, list):
            productos = productos_json
        else:
            st.write("Sin productos")
            return

        if not productos:
            st.write("Sin productos")
            return

        total_general = 0.0
        for i, p in enumerate(productos):
            nombre = p.get("Producto", "")
            tela = p.get("Tela", "")
            precio_unit = float(p.get("PrecioUnitario", 0.0))
            cantidad = int(p.get("Cantidad", 1))
            total = precio_unit * cantidad
            total_general += total

            st.markdown(f"**{i+1}. {nombre}** {f'({tela})' if tela else ''} — x{cantidad} → **{total:.2f}€**")

        st.markdown(f"**TOTAL: {total_general:.2f}€**")

    except Exception as e:
        st.error(f"Error al cargar productos: {e}")

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

        # ✅ Formatear columna Productos (solo primer producto)
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

        # ✅ Columnas a mostrar
        columnas_mostrar = [
            'ID', 'Productos', 'Cliente', 'Club', 'Telefono',
            'Fecha entrada', 'Fecha Salida', 'Precio',
            'Pendiente', 'Inicio Trabajo', 'Trabajo Terminado', 'Retirado', 'Cobrado'
        ]
        columnas_disponibles = [col for col in columnas_mostrar if col in df_display.columns]

        # Ordenar por ID descendente
        df_display = df_display.sort_values('ID', ascending=False)

        # Mostrar tabla
        st.dataframe(df_display[columnas_disponibles], height=600, use_container_width=True)

        # ✅ NUEVO: Sección de "Ver Detalle de Productos"
        st.markdown("### 🔍 Detalle de Productos por Pedido")
        for idx, row in df_filtrado.iterrows():
            if 'Productos' in row and row['Productos']:
                with st.expander(f"Pedido {row['ID']} - {row['Cliente']} ({len(json.loads(row['Productos']) if isinstance(row['Productos'], str) else row['Productos'])} productos)"):
                    mostrar_detalle_productos(row['Productos'], key_suffix=str(row['ID']))

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