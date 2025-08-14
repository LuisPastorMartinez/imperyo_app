# utils/data_utils.py
import re
import pandas as pd
from datetime import datetime, date
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

def limpiar_telefono(numero: Union[str, int, float]) -> Optional[str]:
    """Limpia y valida números telefónicos"""
    if pd.isna(numero) or numero == "":
        return None
    
    # Elimina todo excepto dígitos y signo +
    numero_limpio = re.sub(r'[^\d+]', '', str(numero))
    
    # Validación básica (ajusta según tu país)
    if 8 <= len(numero_limpio) <= 15:
        return numero_limpio
    return None

def limpiar_fecha(fecha: Union[str, date, datetime, pd.Timestamp]) -> Optional[date]:
    """Normaliza diferentes formatos de fecha a date"""
    if pd.isna(fecha) or not fecha:
        return None

    try:
        if isinstance(fecha, (datetime, pd.Timestamp)):
            return fecha.date()
        if isinstance(fecha, date):
            return fecha
            
        # Intenta parsear diferentes formatos
        str_fecha = str(fecha).strip()
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y'):
            try:
                return datetime.strptime(str_fecha, fmt).date()
            except ValueError:
                continue
    except Exception as e:
        logger.error(f"Error limpiando fecha: {str(e)}")
    
    return None

def get_next_id(df: pd.DataFrame, id_column: str) -> int:
    """Obtiene el próximo ID disponible"""
    if df.empty or id_column not in df.columns:
        return 1
    try:
        return int(df[id_column].max()) + 1
    except:
        return 1