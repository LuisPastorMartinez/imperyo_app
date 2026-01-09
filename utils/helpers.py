# utils/helpers.py
import pandas as pd
import numpy as np
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

# =====================================
# CONVERSIÓN SEGURA PARA FIRESTORE
# =====================================
def convert_to_firestore_type(value):
    try:
        if value is None or pd.isna(value):
            return None
    except Exception:
        pass

    if isinstance(value, str) and value.strip() in ("", "NaT", "nan", "None"):
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

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating,)):
        return float(value)

    if isinstance(value, (int, float, bool, str)):
        return value

    return str(value)


# =====================================
# SELECTBOX ÍNDICE SEGURO
# =====================================
def safe_select_index(options, value):
    if not options:
        return 0
    try:
        return options.index(value)
    except Exception:
        return 0
