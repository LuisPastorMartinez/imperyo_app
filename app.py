import streamlit as st
import pandas as pd
import os
import hashlib
from pathlib import Path
from datetime import datetime
import logging

# ===============================
# LOGGING
# ===============================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===============================
# PATH
# ===============================
sys_path = str(Path(__file__).parent)
if sys_path not in os.sys.path:
    os.sys.path.append(sys_path)

# ===============================
# CONFIG PÁGINA
# ===============================
st.set_page_config(
    page_title="Imperyo Sport",
    page_icon="🧵",
    layout="wide"
)

# ===============================
# COOKIES (SEGURO, NO BLOQUEANTE)
# ===============================
cookies = None
cookie_password = st.secrets.get("cookie_password")

if cookie_password:
    try:
        from streamlit_cookies_manager import EncryptedCookieManager

        cookies = EncryptedCookieManager(
            prefix="imperyo_",
            password=cookie_password
        )

        if not cookies.ready():
            st.stop()

    except Exception as e:
        cookies = None
        st.warning("⚠️ Cookies desactivadas (configuración)")

# ===============================
# IMPORTS APP
# ===============================
from utils.firestore_utils import load_dataframes_firestore
from modules.pedidos_page import show_pedidos_page
from modules.gastos_page import show_gastos_page
from modules.resumen_page import show_resumen_page
from modules.config_page import show_config_page
from modules.analisis_productos_page import show_analisis_productos_page

# ===============================
# HEADER
# ===============================
def render_header():
    st.markdown("""
    <div style="
        padding:18px 20px;
        border-radius:10px;
        background:#0e1117;
        margin-bottom:20px;
    ">
        <h1 style="margin:0;color:#ffffff;font-weight:700;">
            Imperyo Sport
        </h1>
        <p style="margin:4px 0 0 0;color:#b0b3b8;font-size:14px;">
            Gestión de pedidos y gastos
        </p>
    </div>
    """, unsafe_allow_html=True)

render_header()

# ===============================
# AUTENTICACIÓN
# ===============================
def check_password():
    try:
        correct_username = st.secrets["auth"]["username"]
        correct_password_hash = st.secrets["auth"]["password_hash"]
    except KeyError:
        st.error("❌ Credenciales no configuradas en secrets")
        st.stop()

    # 🔁 Auto-login por cookie
    if cookies and cookies.get("authenticated") == "true":
        st.session_state.authenticated = True
        return True

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

                if cookies:
                    cookies["authenticated"] = "true"
                    cookies.save()

                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

        return False

    return True

# ===============================
# INIT SESSION
# ===============================
def init_session_state():
    defaults = {
        "data_loaded": False,
        "selected_year": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ===============================
# DATAFRAME VACÍO
# ===============================
def empty_pedidos_df():
    return pd.DataFrame(columns=[
        "ID", "Año", "Cliente", "Telefono", "Club",
        "Precio", "Productos", "id_documento_firestore"
    ])

# ===============================
# MAIN
# ===============================
if check_password():
    init_session_state()

    # 🔓 CERRAR SESIÓN
    if st.sidebar.button("🚪 Cerrar sesión"):
        if cookies:
            cookies["authenticated"] = ""
            cookies.save()
        st.session_state.clear()
        st.rerun()

    if not st.session_state.data_loaded:
        with st.spinner("Cargando datos..."):
            data = load_dataframes_firestore()
            if not data:
                st.error("No se pudieron cargar los datos.")
                st.stop()

            df_pedidos = data.get("df_pedidos")

            if df_pedidos is None or df_pedidos.empty:
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

    # ===============================
    # SIDEBAR
    # ===============================
    st.sidebar.title("🧭 Navegación")
    page = st.sidebar.radio(
        "Secciones",
        ["Inicio", "Pedidos", "Gastos", "Resumen", "Ver Datos", "Configuración"]
    )

    df_pedidos = st.session_state.data.get("df_pedidos", empty_pedidos_df())
    df_gastos = st.session_state.data.get("df_gastos")

    if page == "Inicio":
        st.header("📊 Resumen General")
        st.info("Inicio cargado correctamente")

    elif page == "Pedidos":
        show_pedidos_page(df_pedidos, st.session_state.data.get("df_listas"))

    elif page == "Gastos":
        show_gastos_page(df_gastos)

    elif page == "Resumen":
        show_resumen_page(df_pedidos)

    elif page == "Ver Datos":
        show_analisis_productos_page(df_pedidos)

    elif page == "Configuración":
        show_config_page()
