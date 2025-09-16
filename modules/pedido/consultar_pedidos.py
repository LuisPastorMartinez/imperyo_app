import streamlit as st
import pandas as pd
import json
from datetime import datetime
from utils.data_utils import limpiar_telefono

def cargar_productos_seguro(productos_json):
    """Carga productos desde JSON de forma segura. Devuelve lista vacía si falla."""
    try:
        if isinstance(productos_json, str):
            if not productos_json.strip():
                return []
            return json.loads(productos_json)
        elif isinstance(productos_json, list):
            return productos_json
        else:
            return []
    except (json.JSONDecodeError, TypeError, ValueError):
        return []

def formatear_primer_producto(productos_json):
    """Muestra solo el primer producto en formato resumido + '+P' si hay más."""
    try:
        productos = cargar_productos_seguro(productos_json)
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

        # ✅ Si hay más de un producto, agregar "+P"
        if len(productos) > 1:
            resumen += " +P"

        return resumen

    except Exception:
        return "Error"

def show_consult(df_pedidos, df_listas):
    st.subheader("Consultar Pedidos")

    año_actual = datetime.now().year

    # ✅ Selector de año (solo años <= actual)
    if df_pedidos is not None and not df_pedidos.empty:
        años_disponibles = sorted(df_pedidos[df_pedidos['Año'] <= año_actual]['Año'].dropna().unique(), reverse=True)
    else:
        años_disponibles = [año_actual]

    año_seleccionado = st.selectbox("📅 Año", años_disponibles, key="consulta_año_select")

    # ✅ Filtrar pedidos por año
    df_pedidos_filtrado = df_pedidos[df_pedidos['Año'] == año_seleccionado].copy() if df_pedidos is not None else None

    if df_pedidos_filtrado is None or df_pedidos_filtrado.empty:
        st.info(f"No hay pedidos en el año {año_seleccionado}")
        return

    # --- FILTROS ---
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        filtro_cliente = st.text_input("Cliente", key="filtro_cliente_consulta")
    with col_f2:
        filtro_club = st.text_input("Club", key="filtro_club_consulta")
    with col_f3:
        filtro_telefono = st.text_input("Teléfono", key="filtro_telefono_consulta")
    with col_f4:
        filtro_estado = st.selectbox(
            "Estado",
            options=["", "Pendiente", "Empezado", "Terminado", "Retirado", "Cobrado", "Completado"],
            key="filtro_estado_consulta"
        )

    df_filtrado = df_pedidos_filtrado.copy()

    # --- APLICAR FILTROS ---
    if filtro_cliente:
        df_filtrado = df_filtrado[df_filtrado['Cliente'].str.contains(filtro_cliente, case=False, na=False)]

    if filtro_club:
        df_filtrado = df_filtrado[df_filtrado['Club'].str.contains(filtro_club, case=False, na=False)]

    if filtro_telefono:
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
        elif filtro_estado == "Completado":
            df_filtrado = df_filtrado[
                (df_filtrado['Trabajo Terminado'] == True) &
                (df_filtrado['Cobrado'] == True) &
                (df_filtrado['Retirado'] == True)
            ]

    # --- MOSTRAR RESULTADOS ---
    if not df_filtrado.empty:
        df_display = df_filtrado.copy()

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

        # ✅ Generar columna "Estado" con iconos + "✔️ COMPLETADO"
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

        # ✅ Mostrar tabla
        st.dataframe(
            df_display[columnas_disponibles],
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

        st.caption(f"Mostrando {len(df_filtrado)} de {len(df_pedidos_filtrado)} pedidos del año {año_seleccionado}")

        # ✅ Botón para exportar a CSV
        st.download_button(
            "📥 Descargar como CSV",
            df_filtrado.to_csv(index=False).encode('utf-8'),
            f"pedidos_{año_seleccionado}_filtrados.csv",
            "text/csv",
            key='download-csv-consulta'
        )
    else:
        st.info("No se encontraron pedidos con los filtros aplicados")