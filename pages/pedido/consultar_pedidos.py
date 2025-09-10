# pages/pedido/consultar_pedidos.py
import streamlit as st
import pandas as pd
import json
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
    """Muestra solo el primer producto en formato resumido."""
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

        if len(productos) > 1:
            resumen += f" +{len(productos)-1}"

        return resumen

    except Exception:
        return "Error"

# ✅ NUEVO: Función de diálogo para mostrar detalle
@st.dialog("Detalle de Productos", width="large")
def mostrar_dialogo_productos(productos_json, pedido_id, cliente):
    st.subheader(f"Pedido {pedido_id} - {cliente}")
    productos = cargar_productos_seguro(productos_json)
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

        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        with col1:
            st.write(f"**{nombre}** {f'({tela})' if tela else ''}")
        with col2:
            st.write(f"x{cantidad}")
        with col3:
            st.write(f"{precio_unit:.2f}€")
        with col4:
            st.write(f"**{total:.2f}€**")

    st.markdown("---")
    st.markdown(f"### **TOTAL: {total_general:.2f}€**")
    st.button("Cerrar", on_click=st.rerun)  # Cierra el diálogo

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

        # ✅ Columnas a mostrar (sin 'Productos' duplicado)
        columnas_mostrar = [
            'ID', 'Cliente', 'Club', 'Telefono',
            'Fecha entrada', 'Fecha Salida', 'Precio',
            'Pendiente', 'Inicio Trabajo', 'Trabajo Terminado', 'Retirado', 'Cobrado'
        ]
        columnas_disponibles = [col for col in columnas_mostrar if col in df_display.columns]

        # Ordenar por ID descendente
        df_display = df_display.sort_values('ID', ascending=False)

        # ✅ Mostrar tabla con botón de acción
        st.markdown("### Resultados")
        for idx, row in df_display.iterrows():
            col_id, col_cliente, col_accion = st.columns([1, 4, 2])
            with col_id:
                st.write(f"**{row['ID']}**")
            with col_cliente:
                st.write(f"{row['Cliente']} - {formatear_primer_producto(df_filtrado.iloc[idx]['Productos'])}")
            with col_accion:
                if st.button("🔍 Ver Detalle", key=f"btn_detalle_{row['ID']}"):
                    mostrar_dialogo_productos(
                        df_filtrado.iloc[idx]['Productos'],
                        row['ID'],
                        row['Cliente']
                    )

            st.markdown("---")

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