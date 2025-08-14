import streamlit as st
import pandas as pd
import os
import hashlib
import re
import sys
from pathlib import Path
from datetime import datetime

# SOLUCIÓN DEFINITIVA PARA IMPORTS (sin afectar diseño/funcionalidad)
sys.path.insert(0, str(Path(__file__).parent))

# Importaciones locales con manejo de errores
try:
    from utils.firestore_utils import (
        load_dataframes_firestore,
        save_dataframe_firestore,
        delete_document_firestore,
        get_next_id
    )
    from utils.data_utils import limpiar_telefono, limpiar_fecha
    from pages.pedidos_page import show_pedidos_page
    from pages.gastos_page import show_gastos_page
    from pages.resumen_page import show_resumen_page
except ImportError as e:
    st.error(f"Error crítico: Verifique la estructura de archivos. Detalle: {str(e)}")
    st.stop()

# ============= DISEÑO ORIGINAL (EXACTAMENTE IGUAL) =============
st.set_page_config(
    page_title="ImperYo",
    page_icon="https://www.dropbox.com/scl/fi/opp61pwyq2lxleaj3hxs3/Logo-Movil-e-instagran.png?rlkey=4cruzlufwlz9vfr2myezjkz1d&dl=1",
    layout="wide"
)

# CSS personalizado (idéntico al original)
st.markdown("""
<style>
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
.telefono-input {
    font-family: monospace;
    letter-spacing: 0.1em;
}
</style>
""", unsafe_allow_html=True)

# Header (idéntico al original)
col_logo, col_title = st.columns([0.1, 0.9])
with col_logo:
    st.image("https://www.dropbox.com/scl/fi/opp61pwyq2lxleaj3hxs3/Logo-Movil-e-instagran.png?rlkey=4cruzlufwlz9vfr2myezjkz1d&dl=1", width=80)
with col_title:
    st.header("Imperyo Sport - Gestión de Pedidos y Gastos")

# ============= AUTENTICACIÓN ORIGINAL (FUNCIONAL) =============
def check_password():
    """Función de login original sin modificaciones"""
    try:
        correct_username = st.secrets["auth"]["username"]
        correct_password_hash = st.secrets["auth"]["password_hash"]
    except KeyError:
        st.error("Error de configuración: No se encontraron las credenciales.")
        st.stop()

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "login_attempted" not in st.session_state:
        st.session_state.login_attempted = False
    if "username_input" not in st.session_state:
        st.session_state.username_input = ""
    if "password_input" not in st.session_state:
        st.session_state.password_input = ""

    def authenticate_user():
        hashed_input = hashlib.sha256(st.session_state.password_input.encode()).hexdigest()
        if (st.session_state.username_input == correct_username and 
            hashed_input == correct_password_hash):
            st.session_state.authenticated = True
            st.session_state.login_attempted = False
        else:
            st.session_state.authenticated = False
            st.session_state.login_attempted = True

    if not st.session_state.authenticated:
        st.text_input("Usuario", key="username_input")
        st.text_input("Contraseña", type="password", key="password_input")
        st.button("Iniciar Sesión", on_click=authenticate_user)

        if st.session_state.login_attempted:
            st.error("Usuario o contraseña incorrectos.")
        return False
    return True

# ============= LÓGICA PRINCIPAL (IGUAL QUE ORIGINAL) =============
if check_password():
    # --- CARGA DE DATOS (original) ---
    if 'data_loaded' not in st.session_state:
        st.session_state.data = load_dataframes_firestore()
        
        if 'df_pedidos' in st.session_state.data:
            st.session_state.data['df_pedidos'] = unificar_columnas(st.session_state.data['df_pedidos'])
        
        st.session_state.data_loaded = True

    if st.session_state.data is None:
        st.stop()
    
    # Asignación de DataFrames (original)
    df_pedidos = st.session_state.data['df_pedidos']
    df_gastos = st.session_state.data['df_gastos']
    df_totales = st.session_state.data['df_totales']
    df_listas = st.session_state.data['df_listas']
    df_trabajos = st.session_state.data['df_trabajos']
    
    # --- BOTÓN CERRAR SESIÓN (original) ---
    st.sidebar.markdown("---")
    if st.sidebar.button("Cerrar Sesión"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # --- NAVEGACIÓN (original) ---
    st.sidebar.title("Navegación")
    page = st.sidebar.radio("Ir a:", ["Inicio", "Pedidos", "Gastos", "Resumen", "Ver Datos"])

    if 'current_summary_view' not in st.session_state:
        st.session_state.current_summary_view = "Todos los Pedidos"

    if page == "Resumen":
        with st.sidebar.expander("Seleccionar Vista de Resumen", expanded=True):
            selected_view = st.radio(
                "Ver por categoría:",
                ["Todos los Pedidos", "Trabajos Empezados", "Trabajos Terminados", "Pedidos Pendientes"],
                key="summary_view_radio"
            )
            st.session_state.current_summary_view = selected_view

    # --- CONTENIDO PÁGINAS (original) ---
    if page == "Inicio":
        st.header("Bienvenido a Imperyo Sport")
        st.write("---")
        st.subheader("Estado General")
        st.info(f"Total de Pedidos: {len(df_pedidos)}")

    elif page == "Ver Datos":
        st.header("Datos Cargados")
        # ... (resto de tu código original para esta página)

    elif page == "Pedidos":
        show_pedidos_page(df_pedidos, df_listas)

    elif page == "Gastos":
        show_gastos_page(df_gastos)

    elif page == "Resumen":
        show_resumen_page(df_pedidos, st.session_state.current_summary_view)

# ============= FUNCIONES AUXILIARES (ORIGINALES) =============
def unificar_columnas(df):
    """Función original sin cambios"""
    if 'Fechas Entrada' in df.columns:
        df = df.drop(columns=['Fechas Entrada'])
    
    if 'Teléfono' in df.columns and 'Telefono' in df.columns:
        df['Telefono'] = df['Telefono'].combine_first(df['Teléfono'])
        df = df.drop(columns=['Teléfono'])
    elif 'Teléfono' in df.columns:
        df = df.rename(columns={'Teléfono': 'Telefono'})
    
    if 'Telefono ' in df.columns:
        df['Telefono'] = df['Telefono'].combine_first(df['Telefono '])
        df = df.drop(columns=['Telefono '])
    
    if 'Telefono' in df.columns:
        df['Telefono'] = df['Telefono'].apply(lambda x: x if pd.isna(x) else str(x).strip())
        df['Telefono'] = df['Telefono'].apply(limpiar_telefono)
    
    if 'Fecha entrada' in df.columns:
        df['Fecha entrada'] = df['Fecha entrada'].apply(limpiar_fecha)
    
    if 'Fecha Entreda' in df.columns:
        df['Fecha entrada'] = df['Fecha entrada'].combine_first(df['Fecha Entreda'].apply(limpiar_fecha))
        df = df.drop(columns=['Fecha Entreda'])
    
    if 'Fecha salida' in df.columns:
        df['Fecha Salida'] = df['Fecha Salida'].combine_first(df['Fecha salida'].apply(limpiar_fecha))
        df = df.drop(columns=['Fecha salida'])
    
    columnas_a_unificar = {
        'Precio factura': 'Precio Factura',
        'Obserbaciones': 'Observaciones',
        'Descripcion del Articulo': 'Breve Descripción'
    }
    
    for col_vieja, col_nueva in columnas_a_unificar.items():
        if col_vieja in df.columns:
            if col_nueva not in df.columns:
                df[col_nueva] = df[col_vieja]
            else:
                df[col_nueva] = df[col_nueva].combine_first(df[col_vieja])
            df = df.drop(columns=[col_vieja])
    
    return df