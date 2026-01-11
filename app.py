import streamlit as st
import pandas as pd
import os
import hashlib
from pathlib import Path
from datetime import datetime
import logging

# =====================================================
# LOGGING
# =====================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =====================================================
# PATH
# =====================================================
BASE_PATH = str(Path(__file__).parent)
if BASE_PATH not in os.sys.path:
    os.sys.path.append(BASE_PATH)

# =====================================================
# CONFIG PÁGINA
# =====================================================
st.set_page_config(
    page_title="Imperyo Sport",
    page_icon="icon.png",
    layout="wide"
)

# =====================================================
# IMPORTS APP
# =====================================================
from utils.firestore_utils import load_dataframes_firestore
from modules.pedidos_page import show_pedidos_page
from modules.gastos_page import show_gastos_page
from modules.resumen_page import show_resumen_page
from modules.config_page import show_config_page
from modules.analisis_productos_page import show_analisis_productos_page
from modules.posibles_clientes_page import show_posibles_clientes_page

# =====================================================
# HEADER
# =====================================================
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

# =====================================================
# AUTENTICACIÓN
# =====================================================
def check_password():
    try:
        correct_username = st.secrets["auth"]["username"]
        correct_password_hash = st.secrets["auth"]["password_hash"]
    except KeyError:
        st.error("❌ Credenciales no configuradas en secrets")
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

# =====================================================
# INIT SESSION
# =====================================================
def init_session_state():
    defaults = {
        "data_loaded": False,
        "selected_year": None,
        "current_page": "Inicio",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# =====================================================
# DATAFRAME VACÍO
# =====================================================
def empty_pedidos_df():
    return pd.DataFrame(columns=[
        "ID", "Año", "Cliente", "Telefono", "Club",
        "Precio", "Precio Factura",
        "Inicio Trabajo", "Trabajo Terminado",
        "Pendiente", "Retirado", "Cobrado",
        "Productos", "id_documento_firestore"
    ])

# =====================================================
# MAIN
# =====================================================
if check_password():
    init_session_state()

    # =================================================
    # SIDEBAR
    # =================================================
    st.sidebar.title("🧭 Navegación")

    if st.sidebar.button("🔄 Recargar aplicación"):
        st.session_state.data_loaded = False
        st.session_state.current_page = "Inicio"
        st.rerun()

    if st.sidebar.button("🚪 Cerrar sesión"):
        st.session_state.clear()
        st.rerun()

    # =================================================
    # CARGA DE DATOS
    # =================================================
    if not st.session_state.data_loaded:
        with st.spinner("Cargando datos..."):
            data = load_dataframes_firestore()
            if not data:
                st.error("No se pudieron cargar los datos.")
                st.stop()

            df_pedidos = data.get("df_pedidos")
            if df_pedidos is None or df_pedidos.empty:
                df_pedidos = empty_pedidos_df()
            else:
                df_pedidos["Año"] = (
                    pd.to_numeric(df_pedidos["Año"], errors="coerce")
                    .fillna(datetime.now().year)
                    .astype("int64")
                )

            st.session_state.data = data
            st.session_state.data["df_pedidos"] = df_pedidos
            st.session_state.data_loaded = True

    # =================================================
    # MENÚ
    # =================================================
    page = st.sidebar.radio(
        "Secciones",
        [
            "Inicio",
            "Pedidos",
            "Posibles clientes",
            "Gastos",
            "Resumen",
            "Ver Datos",
            "Configuración",
        ],
        key="current_page"
    )

    df_pedidos = st.session_state.data.get("df_pedidos", empty_pedidos_df())
    df_gastos = st.session_state.data.get("df_gastos")

    # =================================================
    # PÁGINAS
    # =================================================
    if page == "Inicio":
        st.header("🏠 Pedidos nuevos")

        if df_pedidos.empty:
            st.info("No hay pedidos.")
        else:
            # ---- NORMALIZAR ESTADOS ----
            estado_cols = [
                "Inicio Trabajo",
                "Trabajo Terminado",
                "Pendiente",
                "Retirado",
            ]

            for col in estado_cols:
                if col not in df_pedidos.columns:
                    df_pedidos[col] = False
                df_pedidos[col] = df_pedidos[col].fillna(False).astype(bool)

            nuevos = df_pedidos[
                (~df_pedidos["Inicio Trabajo"]) &
                (~df_pedidos["Trabajo Terminado"]) &
                (~df_pedidos["Pendiente"]) &
                (~df_pedidos["Retirado"])
            ].copy()

            if nuevos.empty:
                st.success("🎉 No hay pedidos nuevos pendientes")
            else:
                nuevos = nuevos.sort_values(["Año", "ID"], ascending=[False, False])

                tabla = nuevos[[
                    "ID", "Año", "Cliente", "Club", "Telefono",
                    "Precio", "Cobrado"
                ]]

                st.dataframe(
                    tabla,
                    use_container_width=True,
                    hide_index=True
                )

    elif page == "Pedidos":
        show_pedidos_page(df_pedidos, st.session_state.data.get("df_listas"))

    elif page == "Posibles clientes":
        show_posibles_clientes_page()

    elif page == "Gastos":
        show_gastos_page(df_gastos)

    elif page == "Resumen":
        show_resumen_page(df_pedidos)

    elif page == "Ver Datos":
        show_analisis_productos_page(df_pedidos)

    elif page == "Configuración":
        show_config_page()
