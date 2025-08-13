import re
import pandas as pd
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

def limpiar_telefono(numero):
    """Convierte el número a string y limpia formatos, manteniendo 9 dígitos"""
    if pd.isna(numero) or numero == "":
        return None
    
    numero_limpio = re.sub(r'[^0-9]', '', str(numero))
    
    if len(numero_limpio) == 9:
        return numero_limpio
    elif len(numero_limpio) > 9:
        return numero_limpio[:9]
    
    return None

def limpiar_fecha(fecha):
    """Convierte la fecha a formato date (sin hora) de manera robusta"""
    if pd.isna(fecha) or fecha == "" or fecha is None:
        return None
    
    try:
        # Si ya es datetime.date
        if isinstance(fecha, date):
            return fecha
            
        # Si es datetime.datetime
        if isinstance(fecha, datetime):
            return fecha.date()
            
        # Si es pd.Timestamp
        if isinstance(fecha, pd.Timestamp):
            return fecha.date()
            
        # Si es string
        if isinstance(fecha, str):
            fecha = fecha.strip()
            # Intenta parsear diferentes formatos
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y%m%d'):
                try:
                    return datetime.strptime(fecha, fmt).date()
                except ValueError:
                    continue
                    
        # Si es numpy.datetime64
        if hasattr(fecha, 'item'):  # Para numpy types
            return pd.Timestamp(fecha).date()
            
    except Exception as e:
        logger.error(f"Error limpiando fecha {fecha}: {str(e)}")
        return None
        
    logger.warning(f"Formato de fecha no reconocido: {fecha} (tipo: {type(fecha)})")
    return None

def get_next_id(df, id_column_name):
    """
    Encuentra el siguiente ID disponible buscando el máximo ID existente
    en un DataFrame y sumando 1. Si el DataFrame está vacío, comienza desde 1.
    """
    if df.empty or id_column_name not in df.columns:
        return 1
    df[id_column_name] = pd.to_numeric(df[id_column_name], errors='coerce')
    df_clean = df.dropna(subset=[id_column_name])
    if df_clean.empty:
        return 1
    return int(df_clean[id_column_name].max()) + 1