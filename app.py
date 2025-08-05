import streamlit as st
import pandas as pd
import os
import hashlib

# Importar las funciones desde nuestro módulo de utilidades para Firestore
from utils.firestore_utils import load_dataframes_firestore, save_dataframe_firestore, delete_document_firestore, get_next_id

# --- CONFIGURACIÓN BÁSICA DE LA PÁGINA ---
st.set_page_config(
    page_title="ImperYo",
    page_icon="https://www.dropbox.com/scl/fi/opp61pwyq2lxleaj3hxs3/Logo-Movil-e-instagran.png?rlkey=4cruzlufwlz9vfr2myezjkz1d&dl=1",
    layout="wide"
)

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
.stImage > img {
    max-width: 100px;
    height: auto;
}
h1 { font-size: 3em; }
h2 { font-size: 2.5em; }
.mobile-only { display: none; }
.pc-only { display: block; }
@media (max-width: 768px) {
    .stImage > img { max-width: 60px; }
    h1 { font-size: 2em; }
    h2 { font-size: 1.5em; }
    .mobile-only { display: block; }
    .pc-only { display: none; }
}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
col_logo, col_title = st.columns([0.1, 0.9])
with col_logo:
    st.image("https://www.dropbox.com/scl/fi/opp61pwyq2lxleaj3hxs3/Logo-Movil-e-instagran.png?rlkey=4cruzlufwlz9vfr2myezjkz1d&dl=1", width=80)
with col_title:
    st.header("Imperyo Sport - Gestión de Pedidos y Gastos")

# --- FUNCIÓN DE COLOREADO CORREGIDA ---
def highlight_pedidos_rows(row):
    """Versión corregida para aplicar estilos a las filas"""
    try:
        row_dict = row.to_dict() if hasattr(row, 'to_dict') else dict(row)
        trabajo_terminado = bool(row_dict.get('Trabajo Terminado', False))
        cobrado = bool(row_dict.get('Cobrado', False))
        retirado = bool(row_dict.get('Retirado', False))
        pendiente = bool(row_dict.get('Pendiente', False))
        empezado = bool(row_dict.get('Inicio Trabajo', False))

        if trabajo_terminado and cobrado and retirado and not pendiente:
            return ['background-color: #00B050'] * len(row)
        elif empezado and not pendiente:
            return ['background-color: #0070C0'] * len(row)
        elif trabajo_terminado and not pendiente:
            return ['background-color: #FFC000'] * len(row)
        elif pendiente:
            return ['background-color: #FF00FF'] * len(row)
    except Exception:
        pass
    return [''] * len(row)

# --- AUTENTICACIÓN ---
def check_password():
    """Verificación de credenciales"""
    try:
        correct_username = st.secrets["auth"]["username"]
        correct_password_hash = st.secrets["auth"]["password_hash"]
    except KeyError:
        st.error("Error de configuración: Credenciales no encontradas")
        st.stop()

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        with st.form("login"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Iniciar Sesión"):
                if username == correct_username and hashlib.sha256(password.encode()).hexdigest() == correct_password_hash:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
        return False
    return True

# --- APLICACIÓN PRINCIPAL ---
if check_password():
    # Carga de datos
    if 'data_loaded' not in st.session_state:
        st.session_state.data = load_dataframes_firestore()
        st.session_state.data_loaded = True

    if st.session_state.data is None:
        st.stop()

    df_pedidos = st.session_state.data['df_pedidos']
    df_gastos = st.session_state.data['df_gastos']
    df_totales = st.session_state.data['df_totales']
    df_listas = st.session_state.data['df_listas']
    df_trabajos = st.session_state.data['df_trabajos']

    # Barra lateral
    st.sidebar.title("Navegación")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()

    page = st.sidebar.radio("Ir a:", ["Inicio", "Pedidos", "Gastos", "Resumen", "Ver Datos"])

    # Páginas
    if page == "Inicio":
        st.header("Bienvenido")
        st.info(f"Total de Pedidos: {len(df_pedidos)}")

    elif page == "Ver Datos":
        st.header("Datos Cargados")
        st.subheader("Pedidos")
        st.dataframe(df_pedidos.style.apply(highlight_pedidos_rows, axis=1))
        st.subheader("Gastos")
        st.dataframe(df_gastos)

    elif page == "Resumen":
        st.header("Resumen de Pedidos")
        
        # Filtrado seguro
        view_options = ["Todos los Pedidos", "Trabajos Empezados", "Trabajos Terminados", "Pedidos Pendientes"]
        selected_view = st.selectbox("Ver por categoría:", view_options)
        
        if selected_view == "Todos los Pedidos":
            filtered_df = df_pedidos
        elif selected_view == "Trabajos Empezados":
            filtered_df = df_pedidos[df_pedidos['Inicio Trabajo'] == True]
        elif selected_view == "Trabajos Terminados":
            filtered_df = df_pedidos[df_pedidos['Trabajo Terminado'] == True]
        else:
            filtered_df = df_pedidos[df_pedidos['Pendiente'] == True]

        if not filtered_df.empty:
            st.dataframe(
                filtered_df.style.apply(highlight_pedidos_rows, axis=1),
                height=600,
                use_container_width=True
            )
        else:
            st.info(f"No hay pedidos en la categoría: {selected_view}")

    # [Resto de tus páginas (Pedidos, Gastos) permanecen igual...]