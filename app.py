import streamlit as st
import pandas as pd
from utils import load_dataframe_firestore
from pages.pedidos_page import show_pedidos_page
from login import check_password

st.set_page_config(page_title="Gestión de Pedidos - Imperyo Sport", layout="wide")

# --- Inicializar estado de autenticación ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# --- Pantalla de login ---
if check_password():
    st.session_state["authenticated"] = True
else:
    st.session_state["authenticated"] = False
    st.stop()  # Si no está autenticado, detener la ejecución

# --- Protección extra ---
if not st.session_state["authenticated"]:
    st.warning("Debes iniciar sesión para acceder a esta aplicación.")
    st.stop()

# --- Cargar datos desde Firestore ---
try:
    df_pedidos = load_dataframe_firestore("pedidos")
except Exception as e:
    st.error(f"Error al cargar pedidos: {e}")
    df_pedidos = pd.DataFrame()

try:
    df_listas = load_dataframe_firestore("listas")
except Exception as e:
    st.error(f"Error al cargar listas: {e}")
    df_listas = pd.DataFrame()

# --- Mostrar página principal de pedidos ---
show_pedidos_page(df_pedidos, df_listas)
