# modules/pedidos_page.py
import streamlit as st
from datetime import datetime
from utils.firestore_utils import load_dataframes_firestore

# Importamos las funciones de pedido
try:
    from modules.pedido import show_create, show_consult, show_modify, show_delete
except ImportError as e:
    st.error(f"❌ Error al importar 'modules.pedido': {e}")
    st.stop()

def show_pedidos_page(df_pedidos=None, df_listas=None):
    """
    Página principal de Pedidos.
    Si no se pasan df_pedidos/df_listas, intenta cargarlos desde sesión o Firestore.
    """
    # Intentar cargar desde parámetros → sesión → Firestore
    if df_pedidos is None or df_listas is None:
        # 1. Intentar desde st.session_state.data
        data = st.session_state.get('data', {})
        if isinstance(data, dict) and 'df_pedidos' in data and 'df_listas' in data:
            df_pedidos = data['df_pedidos']
            df_listas = data['df_listas']
            st.info("✅ Datos cargados desde la sesión.")
        else:
            # 2. Cargar desde Firestore
            try:
                st.info("🔄 Cargando datos desde Firestore...")
                data = load_dataframes_firestore()
                if not data or 'df_pedidos' not in data or 'df_listas' not in data:
                    st.error("❌ No se pudieron cargar df_pedidos o df_listas desde Firestore.")
                    st.write("🔍 Datos recibidos:", list(data.keys()) if data else "Ninguno")
                    return
                df_pedidos = data['df_pedidos']
                df_listas = data['df_listas']
                st.session_state['data'] = data  # Guardar para uso futuro
                st.success("✅ Datos cargados correctamente desde Firestore.")
            except Exception as e:
                st.error(f"❌ Error al cargar datos desde Firestore: {e}")
                return

    # Verificación final
    if df_pedidos is None or df_listas is None:
        st.error("❌ Faltan datos esenciales: df_pedidos o df_listas.")
        return

    # Advertencias si están vacíos
    if df_pedidos.empty:
        st.warning("⚠️ No hay pedidos registrados aún.")
    if df_listas.empty:
        st.warning("⚠️ No se encontraron listas de referencia (productos, clubes, etc.).")

    # ✅ Convertir columna 'Año' a entero
    if not df_pedidos.empty and 'Año' in df_pedidos.columns:
        df_pedidos['Año'] = pd.to_numeric(df_pedidos['Año'], errors='coerce').fillna(2025).astype('int64')

    # ✅ Selector de año en la barra lateral
    año_actual = datetime.now().year

    if not df_pedidos.empty:
        años_disponibles = sorted(df_pedidos[df_pedidos['Año'] <= año_actual]['Año'].dropna().unique(), reverse=True)
    else:
        años_disponibles = [año_actual]

    año_seleccionado = st.sidebar.selectbox("📅 Año", años_disponibles, key="año_selector_principal")

    # ✅ Filtrar DataFrame por año
    df_pedidos_filtrado = df_pedidos[df_pedidos['Año'] == año_seleccionado].copy() if df_pedidos is not None else None

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Crear Pedido",
        "Consultar Pedidos", 
        "Modificar Pedido",
        "Eliminar Pedido"
    ])

    with tab1:
        show_create(df_pedidos_filtrado, df_listas)

    with tab2:
        show_consult(df_pedidos_filtrado, df_listas)

    with tab3:
        show_modify(df_pedidos_filtrado, df_listas)

    with tab4:
        show_delete(df_pedidos_filtrado, df_listas)

# Para pruebas locales
if __name__ == "__main__":
    show_pedidos_page()