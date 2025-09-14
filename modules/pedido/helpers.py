# pages/pedido/helpers.py
import pandas as pd
import numpy as np
from datetime import datetime, date

def convert_to_firestore_type(value):
    """Convierte valores a tipos seguros para Firestore (evita NaT)."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    if isinstance(value, str) and value.strip() in ("", "NaT", "nan", "None"):
        return None
    if value is pd.NaT:
        return None

    if isinstance(value, pd.Timestamp):
        if pd.isna(value) or value is pd.NaT:
            return None
        try:
            return value.to_pydatetime()
        except Exception:
            return None

    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime.combine(value, datetime.min.time())

    if isinstance(value, datetime):
        return value

    if isinstance(value, (np.integer, )):
        return int(value)
    if isinstance(value, (np.floating, )):
        return float(value)

    if isinstance(value, (int, float, bool, str)):
        return value

    return str(value)

def safe_select_index(options_list, current_value):
    """Devuelve índice seguro para selectbox (evita ValueError si no está)."""
    try:
        return options_list.index(current_value)
    except Exception:
        return 0
