# utils/excel_utils.py
import streamlit as st
import pandas as pd
import os
from pathlib import Path
from typing import Optional, Dict
import logging
from .data_utils import get_next_id

logger = logging.getLogger(__name__)

# Configuración dinámica
def get_excel_path(year: int, month: int) -> Path:
    return Path(__file__).parent.parent / "data" / f"{year}_{month}_Gastos.xlsm"

SHEET_NAMES = {
    'pedidos': 'Pedidos',
    'gastos': 'Gastos',
    'totales': 'Totales',
    'listas': 'Listas',
    'trabajos': 'Trabajos'
}

REQUIRED_COLUMNS = {
    'pedidos': ['ID', 'Cliente', 'Producto'],
    'gastos': ['Fecha', 'Concepto', 'Importe']
}

@st.cache_data(ttl=600)
def load_dataframes_local(year: int, month: int) -> Optional[Dict[str, pd.DataFrame]]:
    """Carga dataframes desde Excel con validación de estructura."""
    excel_path = get_excel_path(year, month)
    
    if not excel_path.exists():
        logger.error(f"Archivo no encontrado: {excel_path}")
        st.error("Archivo Excel no disponible")
        return None

    try:
        data = {}
        with pd.ExcelFile(excel_path) as xls:
            for key, sheet_name in SHEET_NAMES.items():
                if sheet_name not in xls.sheet_names:
                    logger.warning(f"Hoja {sheet_name} no encontrada")
                    data[f'df_{key}'] = pd.DataFrame(columns=REQUIRED_COLUMNS.get(key, []))
                    continue
                
                df = pd.read_excel(xls, sheet_name=sheet_name)
                missing_cols = [
                    col for col in REQUIRED_COLUMNS.get(key, [])
                    if col not in df.columns
                ]
                
                if missing_cols:
                    logger.error(f"Faltan columnas en {sheet_name}: {missing_cols}")
                    st.warning(f"Estructura inválida en {sheet_name}")
                    continue
                
                data[f'df_{key}'] = df
        
        return data if data else None
    
    except Exception as e:
        logger.error(f"Error cargando Excel: {str(e)}")
        st.error("Error al procesar archivo")
        return None

def save_dataframe_local(
    df: pd.DataFrame,
    sheet_key: str,
    year: int,
    month: int
) -> bool:
    """Guarda un DataFrame en Excel preservando otras hojas."""
    excel_path = get_excel_path(year, month)
    sheet_name = SHEET_NAMES.get(sheet_key)
    
    if not sheet_name:
        logger.error(f"Clave {sheet_key} no válida")
        return False

    try:
        # Leer todas las hojas existentes
        existing_sheets = pd.read_excel(excel_path, sheet_name=None)
        
        # Actualizar la hoja objetivo
        existing_sheets[sheet_name] = df
        
        # Guardar todas las hojas
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for name, df_sheet in existing_sheets.items():
                df_sheet.to_excel(writer, sheet_name=name, index=False)
        
        return True
    except Exception as e:
        logger.error(f"Error guardando Excel: {str(e)}")
        st.error("Error al guardar cambios")
        return False