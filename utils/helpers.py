# utils/helpers.py
import pandas as pd
import numpy as np
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

def convert_to_firestore_type(value):
    """
    Convierte cualquier valor de Pandas/Python a un tipo compatible con Firestore.
    """
    if value is None:
        return None
    if isinstance(value, str):
        if value.strip() in ("", "NaT", "nan", "None"):
            return None
    if isinstance(value, (pd.Timestamp, type(pd.NaT))) and pd.isna(value):
        return None
    if isinstance(value, float) and pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        try:
            return value.to_pydatetime()
        except Exception:
            return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, datetime):
        return value

    if isinstance(value, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(value)
    if isinstance(value, (np.floating, np.float64, np.float32)):
        return float(value)

    if isinstance(value, (int, float, bool, str)):
        return value

    logger.debug(f"Valor convertido a string: {value} (tipo: {type(value)})")
    return str(value)

def safe_select_index(options_list, current_value):
    """
    Devuelve el índice de current_value en options_list.
    Si no existe o hay error, devuelve 0.
    """
    if not isinstance(options_list, (list, tuple)) or len(options_list) == 0:
        return 0
    try:
        return options_list.index(current_value)
    except (ValueError, TypeError):
        return 0