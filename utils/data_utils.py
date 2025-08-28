# utils/data_utils.py
import re
import pandas as pd
from datetime import datetime
import numpy as np

def limpiar_telefono(numero):
    """Convierte el número a string y limpia formatos, manteniendo 9 dígitos"""
    if pd.isna(numero) or numero == "" or numero is None:
        return None
    
    numero_limpio = re.sub(r'[^0-9]', '', str(numero))
    
    if len(numero_limpio) == 9:
        return numero_limpio
    elif len(numero_limpio) > 9:
        return numero_limpio[:9]
    
    return None

def limpiar_fecha(fecha):
    """Convierte la fecha a formato date (sin hora)"""
    if pd.isna(fecha) or fecha == "" or fecha is None:
        return None
    
    try:
        if isinstance(fecha, str):
            if 'T' in fecha:
                return datetime.strptime(fecha.split('T')[0], '%Y-%m-%d').date()
            elif ' ' in fecha:
                return datetime.strptime(fecha.split()[0], '%Y-%m-%d').date()
            elif '/' in fecha:
                return datetime.strptime(fecha, '%d/%m/%Y').date()
            else:
                return datetime.strptime(fecha, '%Y-%m-%d').date()
        elif hasattr(fecha, 'date'):
            return fecha.date()
    except:
        return None
    
    return None

def get_next_id(df, id_column_name):
    """
    Encuentra el siguiente ID disponible buscando el máximo ID existente
    en un DataFrame y sumando 1. Si el DataFrame está vacío, comienza desde 1.
    """
    if df.empty or id_column_name not in df.columns:
        return 1
    # Asegura que la columna ID sea numérica, forzando a NaN los valores no válidos
    df[id_column_name] = pd.to_numeric(df[id_column_name], errors='coerce')
    # Elimina cualquier fila donde el ID se convirtió en NaN
    df_cleaned = df.dropna(subset=[id_column_name])
    if df_cleaned.empty:
        return 1
    max_id = df_cleaned[id_column_name].max()
    return int(max_id) + 1 if pd.notna(max_id) else 1