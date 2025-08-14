# utils/excel_utils.py
import streamlit as st
import pandas as pd
import os
from .data_utils import get_next_id

# Configuración de rutas y nombres de hojas
EXCEL_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "2025_1 Gastos.xlsm")

SHEET_NAMES = {
    'pedidos': 'Pedidos',
    'gastos': 'Gastos',
    'totales': 'Totales',
    'listas': 'Listas',
    'trabajos': 'Trabajos'
}

@st.cache_data(ttl=600)
def load_dataframes_local():
    """Carga dataframes desde archivo Excel local"""
    if not os.path.exists(EXCEL_FILE_PATH):
        st.error(f"Error: Archivo Excel no encontrado en {EXCEL_FILE_PATH}")
        return None
    
    try:
        data = {}
        for key, sheet_name in SHEET_NAMES.items():
            data[f'df_{key}'] = pd.read_excel(EXCEL_FILE_PATH, sheet_name=sheet_name)
        return data
    except Exception as e:
        st.error(f"Error al cargar Excel: {e}")
        return None

def save_dataframe_local(df, sheet_key):
    """Guarda un dataframe en una hoja específica del Excel"""
    sheet_name = SHEET_NAMES.get(sheet_key)
    if not sheet_name:
        st.error(f"Hoja '{sheet_key}' no reconocida")
        return False

    try:
        existing_sheets = pd.read_excel(EXCEL_FILE_PATH, sheet_name=None)
        existing_sheets[sheet_name] = df
        
        with pd.ExcelWriter(EXCEL_FILE_PATH, engine='openpyxl') as writer:
            for sheet_name_to_write, df_to_write in existing_sheets.items():
                df_to_write.to_excel(writer, sheet_name=sheet_name_to_write, index=False)
        return True
    except Exception as e:
        st.error(f"Error al guardar Excel: {e}")
        return False
