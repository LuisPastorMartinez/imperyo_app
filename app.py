import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
import logging

from utils.firestore_utils import load_dataframes_firestore
from modules.pedidos_page import show_pedidos_page
from modules.gastos_page import show_gastos_page
from modules.resumen_page import show_resumen_page
from modules.config_page import show_config_page
from modules.analisis_productos_page import show_analisis_productos_page

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- CONFIG APP ----------------
st.set_page_config(
    page_title="Imperyo Sport",
    page_icon="🧵",
    layout="wide"
)

# ---------------- HEADER ----------------
st.markdown("""
<div style="padding:15px;border-radius:10px;background:#f4f6f8;margin-bottom:20px">
    <h1 style="margin:0">Imperyo Sport</h1>
    <p style="margin:0;color:#666">Gestión de pedidos y gastos</p>
</div>
""", unsafe_allow_html=True)


# ---------------- AUTH ----------------
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


# ---------------- INIT STATE ----------------
def init_session_state():
    defaults = {
        "data_loaded": False,
        "selected_year": None,
        "current_summary_view": "Todos los Pedidos"
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ---------------- MAIN ----------------
if check_password():
    init_session_state()

    if not st.session_state.data_loaded:
        with st.spinner("Cargando datos..."):
            data = load_dataframes_firestore()
            if not data or "df_pedidos" not in data:
                st.error("No se pudieron cargar los datos.")
                st.stop()

            df_pedidos = data["df_pedidos"]

            if not df_pedidos.empty and "Año" in df_pedidos.columns:
                años = sorted(
                    df_pedidos["Año"].dropna().unique(),
                    reverse=True
                )
            else:
                años = [datetime.now().year]

            st.session_state.selected_year = años[0]
            st.session_state.data = data
            st.session_state.data_loaded = True

    st.sidebar.title("🧭 Navegación")
    page = st.sidebar.radio(
        "Secciones",
        ["Inicio", "Pedidos", "Gastos", "Resumen", "Ver Datos", "Configuración"]
    )

    df_pedidos = st.session_state.data["df_pedidos"]
    df_gastos = st.session_state.data.get("df_gastos")

    if page == "Inicio":
        st.header("📊 Resumen General")
        st.write("---")

        años = sorted(
            df_pedidos["Año"].dropna().unique(),
            reverse=True
        ) if not df_pedidos.empty else [datetime.now().year]

        año = st.selectbox(
            "📅 Año",
            años,
            index=0
        )

        st.session_state.selected_year = año
        df = df_pedidos[df_pedidos["Año"] == año].copy()

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("📦 Total", len(df))
        with c2:
            st.metric("🔵 Empezados", len(df[df["Inicio Trabajo"]]))
        with c3:
            st.metric("✅ Terminados", len(df[df["Trabajo Terminado"]]))
        with c4:
            st.metric("📌 Pendientes", len(df[df["Pendiente"]]))

        st.write("---")
        st.subheader(f"Últimos pedidos {año}")

        for _, r in df.sort_values("ID", ascending=False).head(5).iterrows():
            st.markdown(
                f"**Pedido {int(r['ID'])} / {int(r['Año'])}** — "
                f"{r.get('Cliente','')} — "
                f"{r.get('Precio',0):.2f} €"
            )

    elif page == "Pedidos":
        show_pedidos_page(df_pedidos, st.session_state.data.get("df_listas"))

    elif page == "Gastos":
        show_gastos_page(df_gastos)

    elif page == "Resumen":
        show_resumen_page(
            df_pedidos,
            st.session_state.current_summary_view
        )

    elif page == "Ver Datos":
        show_analisis_productos_page(df_pedidos)

    elif page == "Configuración":
        show_config_page()
