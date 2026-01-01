import streamlit as st
import pandas as pd
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime
import logging

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- PATHS ----------------
BASE_PATH = Path(__file__).parent
if str(BASE_PATH) not in sys.path:
    sys.path.append(str(BASE_PATH))

# ---------------- IMPORTS ----------------
from utils.firestore_utils import load_dataframes_firestore
from modules.pedidos_page import show_pedidos_page
from modules.gastos_page import show_gastos_page
from modules.resumen_page import show_resumen_page
from modules.config_page import show_config_page
from modules.analisis_productos_page import show_analisis_productos_page

# ---------------- CONSTANTES ----------------
LOGO_URL = "https://www.dropbox.com/scl/fi/opp61pwyq2lxleaj3hxs3/Logo-Movil-e-instagran.png?rlkey=4cruzlufwlz9vfr2myezjkz1d&dl=1"

# ---------------- CONFIG STREAMLIT ----------------
st.set_page_config(
    page_title="Imperyo Sport",
    page_icon=LOGO_URL,
    layout="wide"
)

# ---------------- CSS ----------------
st.markdown("""
<style>
.stImage img { max-width: 90px; }
h1 { font-size: 2.6em; }
.stButton>button {
    background-color: #2c3e50;
    color: white;
    border-radius: 8px;
    font-weight: bold;
}
.stButton>button:hover {
    background-color: #1a252f;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
def render_header():
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:20px;
                background:#f5f6f7;padding:15px;border-radius:12px;
                box-shadow:0 2px 6px rgba(0,0,0,0.08);">
        <img src="{LOGO_URL}" width="70">
        <div>
            <h1 style="margin:0;">Imperyo Sport</h1>
            <p style="margin:0;color:#666;">Gestión de pedidos y gastos</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

render_header()

# ---------------- AUTENTICACIÓN ----------------
def check_password():
    try:
        correct_user = st.secrets["auth"]["username"]
        correct_pass_hash = st.secrets["auth"]["password_hash"]
    except KeyError:
        st.error("❌ Credenciales no configuradas en secrets.")
        st.stop()

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown("## 🔐 Iniciar sesión")
        st.text_input("Usuario", key="login_user")
        st.text_input("Contraseña", type="password", key="login_pass")

        if st.button("Entrar", use_container_width=True):
            hashed = hashlib.sha256(st.session_state.login_pass.encode()).hexdigest()
            if st.session_state.login_user == correct_user and hashed == correct_pass_hash:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")
        return False

    return True

# ---------------- SESSION STATE ----------------
def init_session_state():
    defaults = {
        "data_loaded": False,
        "selected_year": datetime.now().year,
        "current_summary_view": "Todos los Pedidos"
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ---------------- MAIN ----------------
if not check_password():
    st.stop()

init_session_state()

# ---------------- CARGA DE DATOS ----------------
if not st.session_state.data_loaded:
    with st.spinner("Cargando datos..."):
        data = load_dataframes_firestore()
        if not data:
            st.error("❌ No se pudieron cargar los datos.")
            st.stop()
        st.session_state.data = data
        st.session_state.data_loaded = True

df_pedidos = st.session_state.data.get("df_pedidos", pd.DataFrame())
df_gastos = st.session_state.data.get("df_gastos", pd.DataFrame())
df_listas = st.session_state.data.get("df_listas", pd.DataFrame())

# ---------------- AÑOS DISPONIBLES ----------------
def obtener_años_disponibles(df):
    año_actual = datetime.now().year
    if df.empty or "Año" not in df.columns:
        return [año_actual]
    años = sorted(df["Año"].dropna().unique(), reverse=True)
    if año_actual not in años:
        años.insert(0, año_actual)
    return años

años_disponibles = obtener_años_disponibles(df_pedidos)

# ---------------- SIDEBAR ----------------
st.sidebar.title("🧭 Navegación")

page = st.sidebar.radio(
    "Sección:",
    ["Inicio", "Pedidos", "Gastos", "Resumen", "Ver Datos", "Configuración"]
)

st.sidebar.markdown("---")

# Selector global de año
st.sidebar.subheader("📅 Año de trabajo")
st.session_state.selected_year = st.sidebar.selectbox(
    "Selecciona el año",
    años_disponibles,
    index=años_disponibles.index(st.session_state.selected_year)
    if st.session_state.selected_year in años_disponibles else 0
)

# Cerrar sesión
if st.sidebar.button("🚪 Cerrar sesión", use_container_width=True):
    st.session_state.clear()
    st.rerun()

# ---------------- PÁGINAS ----------------
if page == "Inicio":
    st.header("📊 Resumen general")

    df_year = df_pedidos[df_pedidos["Año"] == st.session_state.selected_year] if not df_pedidos.empty else pd.DataFrame()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Pedidos", len(df_year))
    col2.metric("🆕 Nuevos", len(df_year[
        (df_year["Inicio Trabajo"] == False) &
        (df_year["Pendiente"] == False) &
        (df_year["Trabajo Terminado"] == False)
    ]))
    col3.metric("🔵 Empezados", len(df_year[df_year["Inicio Trabajo"] == True]))
    col4.metric("✅ Terminados", len(df_year[df_year["Trabajo Terminado"] == True]))

elif page == "Pedidos":
    show_pedidos_page(df_pedidos, df_listas)

elif page == "Gastos":
    show_gastos_page(df_gastos)

elif page == "Resumen":
    with st.sidebar.expander("📊 Vista del resumen", expanded=True):
        st.session_state.current_summary_view = st.radio(
            "Ver:",
            [
                "Todos los Pedidos",
                "Trabajos Empezados",
                "Trabajos Terminados",
                "Trabajos Completados",
                "Pedidos Pendientes",
                "Nuevos Pedidos"
            ]
        )
    show_resumen_page(df_pedidos, st.session_state.current_summary_view)

elif page == "Ver Datos":
    show_analisis_productos_page(df_pedidos)

elif page == "Configuración":
    show_config_page()
