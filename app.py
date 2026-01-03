import streamlit as st
import pandas as pd
import os
import hashlib
from pathlib import Path
from datetime import datetime
import logging

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- PATH ---
sys_path = str(Path(__file__).parent)
if sys_path not in os.sys.path:
    os.sys.path.append(sys_path)

# --- CONFIG PÁGINA ---
st.set_page_config(
    page_title="Imperyo Sport",
    page_icon="🧵",
    layout="wide"
)

# --- IMPORTS ---
from utils.firestore_utils import load_dataframes_firestore
from modules.pedidos_page import show_pedidos_page
from modules.gastos_page import show_gastos_page
from modules.resumen_page import show_resumen_page
from modules.config_page import show_config_page
from modules.analisis_productos_page import show_analisis_productos_page

# --- HEADER APP (NEGRO, CORRECTO) ---
def render_header():
    st.markdown("""
    <div style="
        padding:18px 20px;
        border-radius:10px;
        background:#0e1117;
        margin-bottom:20px;
    ">
        <h1 style="
            margin:0;
            color:#ffffff;
            font-weight:700;
        ">
            Imperyo Sport
        </h1>
        <p style="
            margin:4px 0 0 0;
            color:#b0b3b8;
            font-size:14px;
        ">
            Gestión de pedidos y gastos
        </p>
    </div>
    """, unsafe_allow_html=True)

render_header()

# --- AUTENTICACIÓN ---
def check_password():
    try:
        correct_username = st.secrets["auth"]["username"]
        correct_password_hash = st.secrets["auth"]["password_hash"]
    except KeyError:
        st.error("Credenciales no configuradas.")
        st.stop()

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.text_input("Usuario", key="username_input")
        st.text_input("Contraseña", type="password", key="password_input")

        if st.button("Iniciar sesión", type="primary"):
            hashed = hashlib.sha256(
                st.session_state.password_input.encode()
            ).hexdigest()

            if (
                st.session_state.username_input == correct_username
                and hashed == correct_password_hash
            ):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
        return False

    return True

# --- INIT SESSION ---
def init_session_state():
    defaults = {
        "data_loaded": False,
        "selected_year": None,
        "current_summary_view": "Todos los Pedidos"
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# --- ESTADO PEDIDO ---
def calcular_estado(row):
    if row.get("Pendiente"):
        return "Pendiente"
    if row.get("Trabajo Terminado") and row.get("Cobrado") and row.get("Retirado"):
        return "Completado"
    if row.get("Trabajo Terminado"):
        return "Terminado"
    if row.get("Inicio Trabajo"):
        return "Empezado"
    return "Nuevo"

# --- DATAFRAME VACÍO SEGURO ---
def empty_pedidos_df():
    return pd.DataFrame(columns=[
        "ID",
        "Año",
        "Cliente",
        "Telefono",
        "Club",
        "Precio",
        "Productos",
        "id_documento_firestore"
    ])

# --- CONTADOR SEGURO ---
def count_estado(df, estado):
    if df is None or df.empty or "Estado" not in df.columns:
        return 0
    return len(df[df["Estado"] == estado])

# --- MAIN ---
if check_password():
    init_session_state()

    if not st.session_state.data_loaded:
        with st.spinner("Cargando datos..."):
            data = load_dataframes_firestore()
            if not data:
                st.error("No se pudieron cargar los datos.")
                st.stop()

            df_pedidos = data.get("df_pedidos")

            if df_pedidos is None or df_pedidos.empty or "Año" not in df_pedidos.columns:
                df_pedidos = empty_pedidos_df()
                años = [datetime.now().year]
            else:
                df_pedidos["Año"] = (
                    pd.to_numeric(df_pedidos["Año"], errors="coerce")
                    .fillna(datetime.now().year)
                    .astype("int64")
                )
                años = sorted(df_pedidos["Año"].unique(), reverse=True)

            st.session_state.selected_year = años[0]
            st.session_state.data = data
            st.session_state.data["df_pedidos"] = df_pedidos
            st.session_state.data_loaded = True

    # --- SIDEBAR ---
    st.sidebar.title("🧭 Navegación")
    page = st.sidebar.radio(
        "Secciones",
        ["Inicio", "Pedidos", "Gastos", "Resumen", "Ver Datos", "Configuración"]
    )

    # --- DATA ---
    df_pedidos = st.session_state.data.get("df_pedidos", empty_pedidos_df())
    df_gastos = st.session_state.data.get("df_gastos")

    # --- PÁGINAS ---
    if page == "Inicio":
        st.header("📊 Resumen General")
        st.write("---")
        # (resto del código igual que antes)
        st.info("Inicio cargado correctamente")

    elif page == "Pedidos":
        show_pedidos_page(df_pedidos, st.session_state.data.get("df_listas"))

    elif page == "Gastos":
        show_gastos_page(df_gastos)

    elif page == "Resumen":
        show_resumen_page(df_pedidos, st.session_state.current_summary_view)

    elif page == "Ver Datos":
        show_analisis_productos_page(df_pedidos)

    elif page == "Configuración":
        show_config_page()
