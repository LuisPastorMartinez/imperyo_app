# utils/data_utils.py
import re
import pandas as pd
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

# =====================================
# DATEUTIL (OPCIONAL)
# =====================================
try:
    from dateutil.parser import parse
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False


# =====================================
# LIMPIAR TELÉFONO
# =====================================
def limpiar_telefono(numero, longitud_esperada=9, truncar=True):
    """
    Limpia y normaliza un número de teléfono.

    Devuelve string limpio o None si no es válido.
    """
    try:
        if numero is None or pd.isna(numero):
            return None
    except Exception:
        pass

    numero_limpio = re.sub(r"[^0-9]", "", str(numero))

    if len(numero_limpio) == longitud_esperada:
        return numero_limpio

    if len(numero_limpio) > longitud_esperada and truncar:
        return numero_limpio[-longitud_esperada:]

    return None


# =====================================
# LIMPIAR FECHA (SOLO DATE)
# =====================================
def limpiar_fecha(fecha):
    """
    Convierte una entrada a `date` (SIN hora).
    Devuelve None si no es válida.
    """
    try:
        if fecha is None or pd.isna(fecha):
            return None
    except Exception:
        pass

    try:
        # datetime → date
        if isinstance(fecha, datetime):
            return fecha.date()

        # date → date
        if isinstance(fecha, date):
            return fecha

        # string
        if isinstance(fecha, str):
            fecha = fecha.strip()
            if not fecha:
                return None

            if DATEUTIL_AVAILABLE:
                return parse(fecha, dayfirst=True).date()

            # fallback manual
            if "T" in fecha:
                return datetime.strptime(fecha.split("T")[0], "%Y-%m-%d").date()
            if " " in fecha:
                return datetime.strptime(fecha.split(" ")[0], "%Y-%m-%d").date()
            if "/" in fecha:
                d, m, y = fecha.split("/")
                return date(int(y), int(m), int(d))

            return datetime.strptime(fecha, "%Y-%m-%d").date()

        logger.warning(f"Tipo de fecha no soportado: {type(fecha)}")
        return None

    except Exception as e:
        logger.warning(f"Error parseando fecha '{fecha}': {e}")
        return None
