import streamlit as st
from utils.cleanup_pedidos_duplicados import limpiar_pedidos_duplicados

st.set_page_config(page_title="Limpieza pruebas", layout="wide")

limpiar_pedidos_duplicados()
