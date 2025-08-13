import sys
import os

# Asegura que el directorio raíz y la carpeta 'utils' están en sys.path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
UTILS_DIR = os.path.join(ROOT_DIR, "utils")
if UTILS_DIR not in sys.path:
    sys.path.insert(0, UTILS_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
import hashlib
import re
from datetime import datetime

# Importa todas las utilidades desde utils
from utils import (
    limpiar_telefono,
    limpiar_fecha,
    get_next_id,
    load_dataframes_local,
    save_dataframe_local,
    load_dataframes_firestore,
    save_dataframe_firestore,
    delete_document_firestore,
)

# Importa las páginas
from pages.pedidos_page import show_pedidos_page
from pages.gastos_page import show_gastos_page
from pages.resumen_page import show_resumen_page

# Inicializa y carga los datos desde Firestore al inicio
if 'data' not in st.session_state:
    st.session_state.data = load_dataframes_firestore()

# Sidebar para navegación
st.sidebar.title("Menú")
page = st.sidebar.radio(
    "Selecciona una página",
    (
        "Gestión de Pedidos",
        "Gestión de Gastos",
        "Resumen de Pedidos"
    )
)

# Obtiene los DataFrames del estado
df_pedidos = st.session_state.data.get('df_pedidos', pd.DataFrame())
df_gastos = st.session_state.data.get('df_gastos', pd.DataFrame())
df_listas = st.session_state.data.get('df_listas', pd.DataFrame())

# Renderiza la página seleccionada
if page == "Gestión de Pedidos":
    show_pedidos_page(df_pedidos, df_listas)
elif page == "Gestión de Gastos":
    show_gastos_page(df_gastos)
elif page == "Resumen de Pedidos":
    # Vista en el resumen puede ser más dinámica
    resumen_view = st.sidebar.selectbox(
        "Filtrar resumen por:",
        (
            "Todos los Pedidos",
            "Trabajos Empezados",
            "Trabajos Terminados",
            "Pedidos Pendientes",
            "Pedidos sin estado específico"
        )
    )
    show_resumen_page(df_pedidos, resumen_view)

# Opcional: Footer simple
st.markdown("---")
st.markdown("Imperyo App &copy; 2025")
