# modules/pedidos_page.py
import streamlit as st
from utils.firestore_utils import load_dataframes_firestore

# Importamos las funciones de pedido (asegúrate de que existan)1
try:
    from modules.pedido import show_create, show_consult, show_modify, show_delete
except ImportError:
    st.error("❌ Error: No se pudo importar 'modules.pedido'. Verifica que el archivo exista y tenga las funciones necesarias.")
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

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Crear Pedido",
        "Consultar Pedidos", 
        "Modificar Pedido",
        "Eliminar Pedido"
    ])

    with tab1:
        show_create(df_pedidos, df_listas)

    with tab2:
        show_consult(df_pedidos, df_listas)

    with tab3:
        show_modify(df_pedidos, df_listas)

    with tab4:
        show_delete(df_pedidos, df_listas)

# Para pruebas locales
if __name__ == "__main__":
    show_pedidos_page()