import streamlit as st
import pandas as pd
import time
from utils import load_dataframes, save_dataframe_firestore
from pages.pedidos_page import show_pedidos_page

st.set_page_config(page_title="Imperyo App", layout="wide")

# --- LOGIN BÁSICO ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Login")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Iniciar sesión"):
        if username == "admin" and password == "admin":
            st.session_state.logged_in = True
            st.success("¡Bienvenido!")
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")
    st.stop()

# --- CARGA DE DATOS ---
df_pedidos, df_listas = load_dataframes()

# --- ESTADO DE PESTAÑA ACTIVA PARA PEDIDOS ---
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "Consultar"

# --- MENÚ PRINCIPAL ---
st.sidebar.title("Menú")
page = st.sidebar.radio("Navegación", ["Inicio", "Pedidos"])

if page == "Inicio":
    st.title("Bienvenido a Imperyo Sport")
    st.write("Sistema de gestión de pedidos.")
elif page == "Pedidos":
    show_pedidos_page(df_pedidos, df_listas)
