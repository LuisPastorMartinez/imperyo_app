# utils/data_utils.py
import re
import pandas as pd
from datetime import datetime
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

def validar_telefono(numero: Union[str, int, float]) -> Optional[str]:
    """Valida y limpia números de teléfono internacionales o nacionales.
    
    Args:
        numero: Input que puede ser string, número o NaN
        
    Returns:
        Número limpio o None si no es válido
    """
    if pd.isna(numero) or not str(numero).strip():
        return None
    
    numero_limpio = re.sub(r'[^\d+]', '', str(numero))
    
    # Validar formatos internacionales (+XX...) o nacionales (9 dígitos)
    patron = (
        r'^(\+?\d{1,3}?[-.\s]?)?'  # Código país
        r'(\(?\d{1,4}\)?[-.\s]?)?'  # Prefijo
        r'\d{3}[-.\s]?\d{3,4}$'     # Número principal
    )
    
    if re.match(patron, numero_limpio):
        return numero_limpio[:15]  # Limitar longitud
    return None

def limpiar_fecha(fecha: Union[str, datetime, pd.Timestamp, date]) -> Optional[date]:
    """Convierte múltiples formatos de fecha a objeto date.
    
    Formatos soportados:
    - ISO (2023-12-31)
    - Español (31/12/2023)
    - Timestamps de pandas/datetime
    - Fechas como strings con/sin hora
    """
    if pd.isna(fecha) or not fecha:
        return None

    formatos = [
        '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y',
        '%d-%m-%Y', '%Y%m%d', '%d.%m.%Y',
        '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S'
    ]
    
    try:
        if isinstance(fecha, (datetime, pd.Timestamp)):
            return fecha.date()
        elif isinstance(fecha, date):
            return fecha
            
        fecha_str = str(fecha).split('T')[0].split()[0]
        
        for fmt in formatos:
            try:
                return datetime.strptime(fecha_str, fmt).date()
            except ValueError:
                continue
    except Exception as e:
        logger.error(f"Error limpiando fecha {fecha}: {str(e)}")
    
    return None

def get_next_id(df: pd.DataFrame, id_column_name: str) -> int:
    """Obtiene el siguiente ID disponible en un DataFrame.
    
    Args:
        df: DataFrame a analizar
        id_column_name: Nombre de la columna de ID
        
    Returns:
        Entero con el siguiente ID disponible
    """
    if df.empty or id_column_name not in df.columns:
        return 1
    
    try:
        df[id_column_name] = pd.to_numeric(df[id_column_name], errors='coerce')
        max_id = df[id_column_name].max()
        return int(max_id) + 1 if not pd.isna(max_id) else 1
    except Exception as e:
        logger.error(f"Error calculando next ID: {str(e)}")
        return 1