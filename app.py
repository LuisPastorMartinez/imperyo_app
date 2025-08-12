import streamlit as st
import pandas as pd
import os
import hashlib
from pathlib import Path
from datetime import datetime, date
import json

# Configuración de paths para imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent)) 

# Importaciones desde utils
from utils.firestore_utils import (
    load_dataframes_firestore,
    save_dataframe_firestore,
    delete_document_firestore,
    get_next_id
)
from utils.data_utils import limpiar_telefono, limpiar_fecha

# Importaciones desde pages
from pages.pedidos_page import show_pedidos_page
from pages.gastos_page import show_gastos_page
from pages.resumen_page import show_resumen_page

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

# --- HEADER ---
col_logo, col_title = st.columns([0.1, 0.9])
with col_logo:
    st.image("https://www.dropbox.com/scl/fi/opp61pwyq2lxleaj3hxs3/Logo-Movil-e-instagran.png?rlkey=4cruzlufwlz9vfr2myezjkz1d&dl=1", width=80)
with col_title:
    st.header("Imperyo Sport - Gestión de Pedidos y Gastos")

# --- FUNCIÓN PARA UNIFICAR COLUMNAS ---
def unificar_columnas(df):
    """
    Unifica nombres de columnas inconsistentes y limpia los datos de forma robusta.
    """
    if df.empty:
        return df

    column_mapping = {
        'Teléfono': 'Telefono',
        'Telefono ': 'Telefono',
        'Fecha Entreda': 'Fecha entrada',
        'Fecha salida': 'Fecha Salida',
        'Precio factura': 'Precio Factura',
        'Obserbaciones': 'Observaciones',
        'Descripcion del Articulo': 'Breve Descripción',
        'Inicio del trabajo': 'Inicio Trabajo'
    }
    df.rename(columns=column_mapping, inplace=True)
    
    # Comprobar si la columna existe antes de limpiarla
    if 'Telefono' in df.columns:
        # Rellenar valores nulos con una cadena vacía antes de aplicar el método str.
        df['Telefono'] = df['Telefono'].fillna('').astype(str).str.strip().str.replace(r'[^\d]', '', regex=True)

    # Limpiar columnas de fecha de forma robusta
    for col in ['Fecha entrada', 'Fecha Salida']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.date

    # Asegurar que las columnas booleanas son del tipo correcto y rellenar nulos
    for col in ['Inicio Trabajo', 'Trabajo Terminado', 'Cobrado', 'Retirado', 'Pendiente']:
        if col in df.columns:
            df[col] = df[col].fillna(False).astype(bool)

    if 'ID' in df.columns:
        df['ID'] = pd.to_numeric(df['ID'], errors='coerce').fillna(0).astype(int)

    return df

# --- LÓGICA DE AUTENTICACIÓN ---
def check_password():
    """
    Controla el acceso a la aplicación por medio de un usuario y contraseña.
    """
    try:
        correct_username = st.secrets["auth"]["username"]
        correct_password_hash = st.secrets["auth"]["password_hash"]
    except KeyError:
        st.error("Error de configuración: No se encontraron las credenciales de autenticación.")
        return False

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    def authenticate_user():
        hashed_input_password = hashlib.sha256(st.session_state["password_input"].encode()).hexdigest()
        if st.session_state["username_input"] == correct_username and hashed_input_password == correct_password_hash:
            st.session_state["authenticated"] = True
            st.session_state["login_attempted"] = False
        else:
            st.session_state["authenticated"] = False
            st.session_state["login_attempted"] = True

    if not st.session_state["authenticated"]:
        st.text_input("Usuario", key="username_input")
        st.text_input("Contraseña", type="password", key="password_input")
        st.button("Iniciar Sesión", on_click=authenticate_user)

        if st.session_state.get("login_attempted", False) and not st.session_state["authenticated"]:
            st.error("Usuario o contraseña incorrectos.")
        return False
    else:
        return True

# --- LÓGICA PRINCIPAL DE LA APLICACIÓN ---
if check_password():
    if 'data_loaded' not in st.session_state or not st.session_state.data_loaded:
        with st.spinner("Cargando datos de Firestore..."):
            st.session_state.data = load_dataframes_firestore()
            st.session_state.data_loaded = True
        
        if st.session_state.data is None:
            st.error("Error crítico: no se pudieron cargar los datos de Firestore. La aplicación no puede continuar.")
            st.stop()
        
        if 'df_pedidos' in st.session_state.data:
            st.session_state.data['df_pedidos'] = unificar_columnas(st.session_state.data['df_pedidos'])
        
        st.success("Datos cargados correctamente! ✅")

    df_pedidos = st.session_state.data.get('df_pedidos', pd.DataFrame())
    df_gastos = st.session_state.data.get('df_gastos', pd.DataFrame())
    df_totales = st.session_state.data.get('df_totales', pd.DataFrame())
    df_listas = st.session_state.data.get('df_listas', pd.DataFrame())
    df_trabajos = st.session_state.data.get('df_trabajos', pd.DataFrame())
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()

    st.sidebar.title("Navegación")
    page = st.sidebar.radio("Ir a:", ["Inicio", "Pedidos", "Gastos", "Resumen", "Ver Datos"], key="main_page_radio")

    if 'current_summary_view' not in st.session_state:
        st.session_state.current_summary_view = "Todos los Pedidos"

    if page == "Resumen":
        with st.sidebar.expander("Seleccionar Vista de Resumen", expanded=True):
            selected_summary_view_in_expander = st.radio("Ver por categoría:", ["Todos los Pedidos", "Trabajos Empezados", "Trabajos Terminados", "Pedidos Pendientes", "Pedidos sin estado específico"], key="summary_view_radio")
            st.session_state.current_summary_view = selected_summary_view_in_expander

    if page == "Inicio":
        st.header("Bienvenido a Imperyo Sport")
        st.write("---")
        st.subheader("Estado General de Pedidos")
        st.info(f"Total de Pedidos Registrados: **{len(df_pedidos)}**")

    elif page == "Ver Datos":
        st.header("Datos Cargados de Firestore")
        st.subheader("Colección 'pedidos'")
        if not df_pedidos.empty:
            df_pedidos_sorted = df_pedidos.sort_values(by='ID', ascending=False)
            new_column_order = [
                'ID', 'Producto', 'Cliente', 'Club', 'Telefono', 'Breve Descripción',
                'Fecha entrada', 'Fecha Salida', 'Precio', 'Precio Factura',
                'Tipo de pago', 'Adelanto', 'Observaciones'
            ]
            remaining_columns = [col for col in df_pedidos_sorted.columns if col not in new_column_order]
            final_column_order = new_column_order + remaining_columns
            df_pedidos_reordered = df_pedidos_sorted[final_column_order]
            st.dataframe(df_pedidos_reordered)
        else:
            st.info("No hay datos en la colección 'pedidos'.")
        
        st.subheader("Colección 'gastos'")
        st.dataframe(df_gastos)
        st.subheader("Colección 'totales'")
        st.dataframe(df_totales)
        st.subheader("Colección 'listas'")
        st.dataframe(df_listas)
        st.subheader("Colección 'trabajos'")
        st.dataframe(df_trabajos)

    elif page == "Pedidos":
        show_pedidos_page(df_pedidos, df_listas)

    elif page == "Gastos":
        show_gastos_page(df_gastos)

    elif page == "Resumen":
        show_resumen_page(df_pedidos, st.session_state.current_summary_view)