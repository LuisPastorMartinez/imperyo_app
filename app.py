import streamlit as st
import pandas as pd
import os
import hashlib
import re
from pathlib import Path
from datetime import datetime
import logging

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- PATHS ---
sys_path = str(Path(__file__).parent)
if sys_path not in os.sys.path:
    os.sys.path.append(sys_path)

# --- IMPORTS REALES ---
from utils.firestore_utils import (
    load_dataframes_firestore,
    save_dataframe_firestore,
    delete_document_firestore,
    get_next_id
)
from utils.data_utils import limpiar_telefono, limpiar_fecha

# Intentar importar backup_to_dropbox (si falla, desactivar backup)
try:
    from utils.excel_utils import backup_to_dropbox
    DROPBOX_AVAILABLE = True
except ImportError:
    st.warning("⚠️ Módulo de backup no disponible.")
    DROPBOX_AVAILABLE = False

# Módulos de páginas
from modules.pedidos_page import show_pedidos_page
from modules.gastos_page import show_gastos_page
from modules.resumen_page import show_resumen_page
from modules.config_page import show_config_page

# --- CONSTANTES ---
LOGO_URL = "https://www.dropbox.com/scl/fi/opp61pwyq2lxleaj3hxs3/Logo-Movil-e-instagran.png?rlkey=4cruzlufwlz9vfr2myezjkz1d&dl=1"

# --- CONFIG PÁGINA ---
st.set_page_config(page_title="ImperYo", page_icon=LOGO_URL, layout="wide")

# --- CSS ---
st.markdown("""<style>
.stImage > img { max-width: 100px; height: auto; }
h1 { font-size: 3em; }
@media (max-width: 768px) {
    h1 { font-size: 2em; }
    h2 { font-size: 1.5em; }
}
.stButton>button {
    background-color: #2c3e50; color: white; border-radius: 8px; font-weight: bold;
}
.stButton>button:hover {
    background-color: #1a252f; color: #e0e0e0;
}
</style>""", unsafe_allow_html=True)

# --- HEADER ---
def render_header():
    st.markdown(f"""
    <div style="display: flex; align-items: center; padding: 15px; border-radius: 12px; 
                background: linear-gradient(to right, #f8f9fa, #e9ecef); 
                box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px;">
        <img src="{LOGO_URL}" width="80" style="margin-right: 25px; border-radius: 8px;">
        <div>
            <h1 style="margin: 0; color: #2c3e50; font-weight: 700;">Imperyo Sport</h1>
            <p style="margin: 0; color: #6c757d; font-size: 1.2em;">Gestión de Pedidos y Gastos</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

render_header()

# --- AUTENTICACIÓN ---
def check_password():
    try:
        correct_username = st.secrets["auth"]["username"]
        correct_password_hash = st.secrets["auth"]["password_hash"]
    except KeyError:
        st.error("❌ Error: credenciales no configuradas en secrets.")
        st.stop()

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.markdown(f"""
        <div style="text-align: center; padding: 30px; border-radius: 15px; 
                    background: #f8f9fa; box-shadow: 0 4px 12px rgba(0,0,0,0.08); 
                    margin: 20px auto; max-width: 400px;">
            <img src="{LOGO_URL}" width="100" style="margin-bottom: 20px; border-radius: 50%;">
            <h3>🔐 Iniciar Sesión</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.text_input("👤 Usuario", key="username_input")
        st.text_input("🔒 Contraseña", type="password", key="password_input")
        
        def authenticate():
            hashed = hashlib.sha256(st.session_state["password_input"].encode()).hexdigest()
            if (st.session_state["username_input"] == correct_username and 
                hashed == correct_password_hash):
                st.session_state["authenticated"] = True
            else:
                st.session_state["login_failed"] = True

        st.button("🚀 Iniciar Sesión", on_click=authenticate, use_container_width=True)

        if st.session_state.get("login_failed", False):
            st.error("❌ Usuario o contraseña incorrectos.")
        return False
    return True

# --- INICIALIZAR SESIÓN ---
def init_session_state():
    defaults = {
        "authenticated": False,
        "data_loaded": False,
        "selected_year": datetime.now().year,
        "last_backup": None,
        "current_summary_view": "Todos los Pedidos"
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# --- CALCULAR ESTADO ---
def calcular_estado(row):
    if row.get('Pendiente', False):
        return 'Pendiente'
    if (row.get('Trabajo Terminado', False) and 
        row.get('Cobrado', False) and 
        row.get('Retirado', False)):
        return 'Completado'
    if row.get('Trabajo Terminado', False):
        return 'Terminado'
    if row.get('Inicio Trabajo', False):
        return 'Empezado'
    return 'Nuevo'

# --- LÓGICA PRINCIPAL ---
if check_password():
    init_session_state()
    
    if not st.session_state.data_loaded:
        with st.spinner("Cargando datos desde Firestore..."):
            data = load_dataframes_firestore()
            if data is None:
                st.error("❌ No se pudieron cargar los datos.")
                st.stop()

            # ✅ CORRECCIÓN: Inferir 'Año' desde 'Fecha entrada'
            if 'df_pedidos' in data:
                df = data['df_pedidos']
                if 'Año' not in df.columns:
                    logger.info("Añadiendo columna 'Año' a pedidos...")
                    if 'Fecha entrada' in df.columns:
                        df['Año'] = pd.to_datetime(df['Fecha entrada'], errors='coerce').dt.year
                    else:
                        df['Año'] = datetime.now().year
                    df['Año'] = df['Año'].fillna(datetime.now().year).astype('int64')
                    if save_dataframe_firestore(df, 'pedidos'):
                        logger.info("✅ Campo 'Año' guardado en Firestore.")
                        st.success("✅ Campo 'Año' añadido a los pedidos.")
                    else:
                        st.warning("⚠️ No se pudo guardar el campo 'Año'.")
                data['df_pedidos'] = df

            st.session_state.data = data
            st.session_state.data_loaded = True

    # Validar DataFrames
    required_dfs = ['df_pedidos', 'df_gastos', 'df_totales', 'df_listas', 'df_trabajos']
    for df_name in required_dfs:
        if df_name not in st.session_state.data:
            st.error(f"❌ Falta '{df_name}' en los datos.")
            st.stop()

    df_pedidos = st.session_state.data['df_pedidos']
    df_gastos = st.session_state.data['df_gastos']
    df_totales = st.session_state.data['df_totales']
    df_listas = st.session_state.data['df_listas']
    df_trabajos = st.session_state.data['df_trabajos']

    # Cerrar sesión
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Cerrar Sesión", type="primary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # Navegación
    st.sidebar.title("🧭 Navegación Principal")
    page = st.sidebar.radio(
        "Selecciona una sección:",
        ["Inicio", "Pedidos", "Gastos", "Resumen", "Ver Datos", "Configuración"],
        index=0
    )

    if page == "Resumen":
    with st.sidebar.expander("📊 Filtrar Resumen", expanded=True):
        selected_summary_view_in_expander = st.radio(
            "Ver por estado:",
            ["Todos los Pedidos", "Trabajos Empezados", "Trabajos Terminados", "Trabajos Completados", "Pedidos Pendientes", "Nuevos Pedidos"],
            key="summary_view_radio"
        )
        st.session_state.current_summary_view = selected_summary_view_in_expander

    # Páginas
    if page == "Inicio":
        st.header("📊 Bienvenido a Imperyo Sport")
        st.write("---")

        años = sorted(df_pedidos['Año'].dropna().unique(), reverse=True) if 'Año' in df_pedidos.columns else [datetime.now().year]
        selected_year = st.selectbox("📅 Selecciona el año:", años)
        st.session_state.selected_year = selected_year

        df_filtrado = df_pedidos[df_pedidos['Año'] == selected_year].copy()
        df_filtrado['Estado'] = df_filtrado.apply(calcular_estado, axis=1)

        col1, col2, col3, col4, col5 = st.columns(5)
        total = len(df_filtrado)
        with col1: st.metric(f"📆 {selected_year} Total", total)
        with col2: st.metric("🆕 Nuevos", len(df_filtrado[df_filtrado['Estado'] == 'Nuevo']))
        with col3: st.metric("🔄 Empezados", len(df_filtrado[df_filtrado['Estado'] == 'Empezado']))
        with col4: st.metric("⏳ Pendientes", len(df_filtrado[df_filtrado['Estado'] == 'Pendiente']))
        with col5: st.metric("✅ Terminados", len(df_filtrado[df_filtrado['Estado'] == 'Terminado']))

        st.write("---")
        st.subheader(f"📅 Últimos 5 Pedidos ({selected_year})")
        if not df_filtrado.empty:
            for _, r in df_filtrado.sort_values('ID', ascending=False).head(5).iterrows():
                st.markdown(f"**ID {r['ID']}** — {r.get('Cliente','N/A')} — {r.get('Producto','N/A')} — 📅 {r.get('Fecha entrada','N/A')} — 🏷️ *{r['Estado']}*")
        else:
            st.info(f"No hay pedidos en {selected_year}.")

    elif page == "Ver Datos":
        st.header("🗃️ Datos Cargados de Firestore")
        for name, df in st.session_state.data.items():
            st.subheader(f"Colección '{name.replace('df_', '')}'")
            st.dataframe(df, use_container_width=True)

    elif page == "Pedidos":
        show_pedidos_page(df_pedidos, df_listas)
    elif page == "Gastos":
        show_gastos_page(df_gastos)
    elif page == "Resumen":
        show_resumen_page(df_pedidos, st.session_state.current_summary_view)
    elif page == "Configuración":
        show_config_page()