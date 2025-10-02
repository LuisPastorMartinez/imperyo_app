#Consultar pedidos
import streamlit as st
import pandas as pd
import json
from datetime import datetime
import io
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
    st.subheader("📋 Consultar y Filtrar Pedidos")
    st.write("---")

    # ✅ Convertir columna 'Año' a entero
    if not df_pedidos.empty and 'Año' in df_pedidos.columns:
        df_pedidos['Año'] = pd.to_numeric(df_pedidos['Año'], errors='coerce').fillna(datetime.now().year).astype('int64')

    # ✅ Selector de año (sincronizado con sesión)
    año_actual = datetime.now().year

    if df_pedidos is not None and not df_pedidos.empty:
        años_disponibles = sorted(df_pedidos['Año'].dropna().unique(), reverse=True)
    else:
        años_disponibles = [año_actual]

    # Usar el año seleccionado en la sesión (sincronizado con otras páginas)
    año_seleccionado = st.selectbox(
        "📅 Filtrar por Año",
        options=años_disponibles,
        index=años_disponibles.index(st.session_state.get('selected_year', año_actual)) 
               if st.session_state.get('selected_year', año_actual) in años_disponibles 
               else 0,
        key="consulta_año_select"
    )

    # Guardar selección en sesión
    st.session_state.selected_year = año_seleccionado

    # ✅ Filtrar pedidos por año
    df_pedidos_filtrado = df_pedidos[df_pedidos['Año'] == año_seleccionado].copy() if df_pedidos is not None else None

    if df_pedidos_filtrado is None or df_pedidos_filtrado.empty:
        st.info(f"📭 No hay pedidos en el año {año_seleccionado}")
        return

    st.write("---")

    # --- BÚSQUEDA GLOBAL ---
    search_term = st.text_input("🔍 Búsqueda global (Cliente, Producto, Teléfono, ID...)", placeholder="Escribe para filtrar todos los campos...")
    
    # --- FILTROS AVANZADOS CON AUTORRELLENADO ---
    with st.expander("⚙️ Filtros Avanzados", expanded=True):
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        # ✅ Cliente: selectbox con valores únicos
        with col_f1:
            clientes_unicos = [""] + sorted(df_pedidos_filtrado['Cliente'].dropna().unique().astype(str).tolist())
            filtro_cliente = st.selectbox("👤 Cliente", options=clientes_unicos, key="filtro_cliente_consulta")
        
        # ✅ Club: selectbox con valores únicos
        with col_f2:
            clubes_unicos = [""] + sorted(df_pedidos_filtrado['Club'].dropna().unique().astype(str).tolist())
            filtro_club = st.selectbox("⚽ Club", options=clubes_unicos, key="filtro_club_consulta")
        
        # ✅ Teléfono: selectbox con valores únicos (solo dígitos)
        with col_f3:
            telefonos_unicos = df_pedidos_filtrado['Telefono'].dropna().astype(str).str.replace(r'\D', '', regex=True)
            telefonos_unicos = telefonos_unicos[telefonos_unicos.str.len() == 9]  # Solo teléfonos válidos
            telefonos_lista = [""] + sorted(telefonos_unicos.unique().tolist())
            filtro_telefono = st.selectbox("📱 Teléfono", options=telefonos_lista, key="filtro_telefono_consulta")
        
        # ✅ Estado: con opción "Todos"
        with col_f4:
            filtro_estado = st.selectbox(
                "🏷️ Estado",
                options=["Todos", "Nuevos Pedidos", "Pendiente", "Empezado", "Terminado", "Retirado", "Cobrado", "Completado"],
                key="filtro_estado_consulta"
            )

    df_filtrado = df_pedidos_filtrado.copy()

    # --- APLICAR FILTRO GLOBAL ---
    if search_term:
        mask = df_filtrado.apply(lambda row: search_term.lower() in str(row).lower(), axis=1)
        df_filtrado = df_filtrado[mask]

    # --- APLICAR FILTROS ESPECÍFICOS ---
    if filtro_cliente:
        df_filtrado = df_filtrado[df_filtrado['Cliente'].astype(str) == filtro_cliente]

    if filtro_club:
        df_filtrado = df_filtrado[df_filtrado['Club'].astype(str) == filtro_club]

    if filtro_telefono:
        df_filtrado['Telefono_limpio'] = df_filtrado['Telefono'].astype(str).str.replace(r'\D', '', regex=True)
        df_filtrado = df_filtrado[df_filtrado['Telefono_limpio'] == filtro_telefono]
        df_filtrado = df_filtrado.drop(columns=['Telefono_limpio'])

    # ✅ Aplicar filtro de estado SOLO si no es "Todos"
    if filtro_estado and filtro_estado != "Todos":
        if filtro_estado == "Nuevos Pedidos":
            df_filtrado = df_filtrado[
                (df_filtrado['Inicio Trabajo'] == False) &
                (df_filtrado['Pendiente'] == False) &
                (df_filtrado['Trabajo Terminado'] == False) &
                (df_filtrado['Cobrado'] == False) &
                (df_filtrado['Retirado'] == False)
            ]
        elif filtro_estado == "Pendiente":
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
        if 'Precio Factura' in df_display.columns:
            df_display['Precio Factura'] = pd.to_numeric(df_display['Precio Factura'], errors='coerce').fillna(0.0)

        # Asegurar booleanos (solo para lógica interna)
        for col in ['Pendiente', 'Inicio Trabajo', 'Trabajo Terminado', 'Retirado', 'Cobrado']:
            if col in df_display.columns:
                df_display[col] = df_display[col].fillna(False).astype(bool)

        # ✅ Generar columna "Estado" con iconos
        def estado_a_icono(row):
            es_nuevo = not (
                row.get('Inicio Trabajo', False) or
                row.get('Pendiente', False) or
                row.get('Trabajo Terminado', False) or
                row.get('Cobrado', False) or
                row.get('Retirado', False)
            )
            if es_nuevo:
                return "🆕 NUEVO"
            
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
            if (row.get('Trabajo Terminado', False) and
                row.get('Cobrado', False) and
                row.get('Retirado', False)):
                iconos.append("✔️ COMPLETADO")

            return " ".join(iconos)

        df_display['Estado'] = df_display.apply(estado_a_icono, axis=1)

        # ✅ Columnas a mostrar
        columnas_mostrar = [
            'ID', 'Productos', 'Cliente', 'Club', 'Telefono',
            'Fecha entrada', 'Fecha Salida', 'Precio', 'Precio Factura', 'Estado'
        ]
        columnas_disponibles = [col for col in columnas_mostrar if col in df_display.columns]

        # Ordenar por ID descendente
        df_display = df_display.sort_values('ID', ascending=False)

        # ✅ Mostrar tabla SIN ESTILOS (usa el tema por defecto)
        st.dataframe(
            df_display[columnas_disponibles],
            column_config={
                "Productos": st.column_config.TextColumn(
                    "🧵 Productos",
                    help="Primer producto del pedido. '+P' indica que hay más productos.",
                    width="medium"
                ),
                "Precio": st.column_config.NumberColumn(
                    "💰 Precio Total (€)",
                    format="%.2f €",
                    width="small"
                ),
                "Precio Factura": st.column_config.NumberColumn(
                    "🧾 Precio Factura (€)",
                    format="%.2f €",
                    width="small"
                ),
                "Estado": st.column_config.TextColumn(
                    "🏷️ Estado",
                    help="📌 Pendiente | 🔵 Empezado | ✅ Terminado | 📦 Retirado | 💰 Cobrado | ✔️ COMPLETADO | 🆕 NUEVO",
                    width="medium"
                ),
            },
            height=600,
            use_container_width=True,
            hide_index=True
        )

        st.caption(f"📊 Mostrando {len(df_filtrado)} de {len(df_pedidos_filtrado)} pedidos del año {año_seleccionado}")

        # ✅ Botón de exportación a Excel
        st.write("---")
        st.markdown("### 📥 Exportar Datos")
        
        df_export = df_filtrado.copy()
        date_columns = ['Fecha entrada', 'Fecha Salida']
        for col in date_columns:
            if col in df_export.columns:
                df_export[col] = pd.to_datetime(df_export[col], errors='coerce')
                df_export[col] = df_export[col].dt.tz_localize(None)
        
        buffer = io.BytesIO()
        try:
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Pedidos')
            
            st.download_button(
                label="📥 Descargar como Excel",
                data=buffer.getvalue(),
                file_name=f"pedidos_{año_seleccionado}_filtrados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        except Exception as e:
            st.error(f"❌ Error al generar el archivo Excel: {e}")