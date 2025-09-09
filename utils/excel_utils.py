# utils/excel_utils.py
import streamlit as st
import pandas as pd
import os
from openpyxl import load_workbook
from .firestore_utils import get_next_id  # ✅ CORREGIDO: ahora importa desde firestore_utils

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
        st.warning(f"Archivo Excel no encontrado en {EXCEL_FILE_PATH}. Se crearán DataFrames vacíos.")
        return create_empty_dataframes()

    try:
        data = {}
        xls = pd.ExcelFile(EXCEL_FILE_PATH)
        available_sheets = xls.sheet_names

        for key, sheet_name in SHEET_NAMES.items():
            if sheet_name in available_sheets:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                data[f'df_{key}'] = df
            else:
                st.warning(f"Hoja '{sheet_name}' no encontrada. Se creará vacía.")
                data[f'df_{key}'] = create_empty_dataframe(key)

        return data
    except Exception as e:
        st.error(f"Error al cargar Excel: {e}")
        return create_empty_dataframes()

def save_dataframe_local(df, sheet_key):
    """Guarda un dataframe en una hoja específica del Excel (sin borrar otras hojas)"""
    sheet_name = SHEET_NAMES.get(sheet_key)
    if not sheet_name:
        st.error(f"Hoja '{sheet_key}' no reconocida")
        return False

    try:
        if not os.path.exists(EXCEL_FILE_PATH):
            st.warning(f"Archivo Excel no existe. Creando nuevo archivo en {EXCEL_FILE_PATH}")
            # Crear archivo nuevo con todas las hojas vacías
            with pd.ExcelWriter(EXCEL_FILE_PATH, engine='openpyxl') as writer:
                for sn in SHEET_NAMES.values():
                    create_empty_dataframe_from_key(sn).to_excel(writer, sheet_name=sn, index=False)
        
        # Cargar libro existente
        book = load_workbook(EXCEL_FILE_PATH)
        writer = pd.ExcelWriter(EXCEL_FILE_PATH, engine='openpyxl')
        writer.book = book
        writer.sheets = {ws.title: ws for ws in book.worksheets}

        # Guardar solo la hoja especificada
        df.to_excel(writer, sheet_name=sheet_name, index=False)

        writer.save()
        writer.close()

        # Invalidar caché
        load_dataframes_local.clear()
        return True

    except Exception as e:
        st.error(f"Error al guardar Excel: {e}")
        return False

def create_empty_dataframe_from_key(sheet_key):
    """Crea DataFrame vacío según el tipo de hoja"""
    if sheet_key == 'Pedidos':
        return pd.DataFrame(columns=[
            'ID', 'Producto', 'Cliente', 'Telefono', 'Club', 'Talla', 'Tela',
            'Breve Descripción', 'Fecha entrada', 'Fecha Salida', 'Precio',
            'Precio Factura', 'Tipo de pago', 'Adelanto', 'Observaciones',
            'Inicio Trabajo', 'Cobrado', 'Retirado', 'Pendiente', 'Trabajo Terminado'
        ])
    elif sheet_key == 'Gastos':
        return pd.DataFrame(columns=['ID', 'Fecha', 'Concepto', 'Importe', 'Tipo'])
    elif sheet_key == 'Totales':
        return pd.DataFrame()
    elif sheet_key == 'Listas':
        return pd.DataFrame()
    elif sheet_key == 'Trabajos':
        return pd.DataFrame()
    return pd.DataFrame()

def create_empty_dataframe(key):
    """Crea DataFrame vacío según la clave del diccionario"""
    if key == 'pedidos':
        return create_empty_dataframe_from_key('Pedidos')
    elif key == 'gastos':
        return create_empty_dataframe_from_key('Gastos')
    return pd.DataFrame()

def create_empty_dataframes():
    """Crea todos los DataFrames vacíos"""
    return {
        'df_pedidos': create_empty_dataframe('pedidos'),
        'df_gastos': create_empty_dataframe('gastos'),
        'df_totales': pd.DataFrame(),
        'df_listas': pd.DataFrame(),
        'df_trabajos': pd.DataFrame()
    }