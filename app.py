import streamlit as st
import pandas as pd
import os
import hashlib # Para el hash de la contraseña

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
/* Tus estilos CSS existentes */
.stImage > img {
    max-width: 100px;
    height: auto;
}
h1 {
    font-size: 3em;
}
h2 {
    font-size: 2.5em;
}
.mobile-only {
    display: none;
}
.pc-only {
    display: block;
}
@media (max-width: 768px) {
    .stImage > img {
        max-width: 60px;
    }
    h1 {
        font-size: 2em;
    }
    h2 {
        font-size: 1.5em;
    }
    .mobile-only {
        display: block;
    }
    .pc-only {
        display: none;
    }
}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
col_logo, col_title = st.columns([0.1, 0.9])
with col_logo:
    st.image("https://www.dropbox.com/scl/fi/opp61pwyq2lxleaj3hxs3/Logo-Movil-e-instagran.png?rlkey=4cruzlufwlz9vfr2myezjkz1d&dl=1", width=80)
with col_title:
    st.header("Imperyo Sport - Gestión de Pedidos y Gastos")

# --- FUNCIÓN DE COLOREADO DE FILAS (CORREGIDA) ---
def highlight_pedidos_rows(row):
    styles = [''] * len(row)
    
    # Usar .get() con valores por defecto para evitar KeyError
    trabajo_terminado = row.get('Trabajo Terminado', False)
    cobrado = row.get('Cobrado', False)
    retirado = row.get('Retirado', False)
    pendiente = row.get('Pendiente', False)
    empezado = row.get('Inicio Trabajo', False)

    if trabajo_terminado and cobrado and retirado and not pendiente:
        styles = ['background-color: #00B050'] * len(row)
    elif empezado and not pendiente:
        styles = ['background-color: #0070C0'] * len(row)
    elif trabajo_terminado and not pendiente:
        styles = ['background-color: #FFC000'] * len(row)
    elif pendiente:
        styles = ['background-color: #FF00FF'] * len(row)

    return styles

# --- LÓGICA DE AUTENTICACIÓN (SIN CAMBIOS) ---
def check_password():
    """Función de autenticación existente"""
    try:
        correct_username = st.secrets["auth"]["username"]
        correct_password_hash = st.secrets["auth"]["password_hash"]
    except KeyError:
        st.error("Error de configuración: No se encontraron las credenciales en secrets.toml.")
        st.stop()

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "login_attempted" not in st.session_state:
        st.session_state["login_attempted"] = False
    if "username_input" not in st.session_state:
        st.session_state["username_input"] = ""
    if "password_input" not in st.session_state:
        st.session_state["password_input"] = ""

    def authenticate_user():
        hashed_input_password = hashlib.sha256(st.session_state["password_input"].encode()).hexdigest()
        if st.session_state["username_input"] == correct_username and hashed_input_password == correct_password_hash:
            st.session_state["authenticated"] = True
            st.session_state["login_attempted"] = False
            st.session_state["username_input"] = ""
            st.session_state["password_input"] = ""
        else:
            st.session_state["authenticated"] = False
            st.session_state["login_attempted"] = True

    if not st.session_state["authenticated"]:
        st.text_input("Usuario", key="username_input")
        st.text_input("Contraseña", type="password", key="password_input")
        st.button("Iniciar Sesión", on_click=authenticate_user)

        if st.session_state["login_attempted"] and not st.session_state["authenticated"]:
            st.error("Usuario o contraseña incorrectos.")
        return False
    else:
        return True

# --- LÓGICA PRINCIPAL ---
if check_password():
    # --- CARGA DE DATOS CON VERIFICACIÓN DE COLUMNAS ---
    if 'data_loaded' not in st.session_state:
        st.session_state.data = load_dataframes_firestore()
        st.session_state.data_loaded = True

        # Asegurar que las columnas de estado existan
        if st.session_state.data is not None and 'df_pedidos' in st.session_state.data:
            status_columns = ['Inicio Trabajo', 'Trabajo Terminado', 'Cobrado', 'Retirado', 'Pendiente']
            for col in status_columns:
                if col not in st.session_state.data['df_pedidos'].columns:
                    st.session_state.data['df_pedidos'][col] = False

    if st.session_state.data is None:
        st.stop()

    # Resto del código original sin cambios...
    # [Aquí iría todo el resto de tu código exactamente como está]
    # Solo se modificó la función highlight_pedidos_rows y se añadió la verificación de columnas

    # --- EJEMPLO DE CÓMO QUEDARÍA UNA SECCIÓN (para referencia) ---
    df_pedidos = st.session_state.data['df_pedidos']
    
    if 'Ver Datos' in st.sidebar.radio("Ir a:", ["Inicio", "Pedidos", "Gastos", "Resumen", "Ver Datos"], key="main_page_radio"):
        st.header("Datos Cargados de Firestore")
        if not df_pedidos.empty:
            df_pedidos_sorted = df_pedidos.sort_values(by='ID', ascending=False)
            st.dataframe(df_pedidos_sorted.style.apply(highlight_pedidos_rows, axis=1))
        else:
            st.info("No hay datos en la colección 'pedidos'.")

    # ... (todo el resto de tu código permanece exactamente igual)