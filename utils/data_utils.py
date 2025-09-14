# utils/data_utils.py
import re
import pandas as pd
from datetime import datetime, date
import logging

# Opcional: para parseo flexible de fechas (recomendado)
try:
    from dateutil.parser import parse
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)

def limpiar_telefono(numero, longitud_esperada=9, truncar=True):
    """
    Limpia y normaliza un número de teléfono.
    
    Ejemplos:
        limpiar_telefono("600 123 456") → "600123456"
        limpiar_telefono("+34 600 123 456") → "600123456" (si truncar=True)
        limpiar_telefono("123") → None

    Args:
        numero: entrada (str, int, float, etc.)
        longitud_esperada: longitud deseada del resultado (default: 9)
        truncar: si True, trunca números más largos (últimos dígitos)

    Returns:
        str con número limpio, o None si no es válido.
    """
    if pd.isna(numero) or numero == "" or numero is None:
        return None

    # Convertir a string y limpiar
    numero_limpio = re.sub(r'[^0-9]', '', str(numero))

    if len(numero_limpio) == longitud_esperada:
        return numero_limpio
    elif len(numero_limpio) > longitud_esperada and truncar:
        # Tomar los últimos N dígitos (más útil que los primeros)
        return numero_limpio[-longitud_esperada:]
    elif len(numero_limpio) < longitud_esperada:
        # Número demasiado corto
        return None

    return None

def limpiar_fecha(fecha):
    """
    Convierte la fecha a formato date (sin hora).
    Soporta múltiples formatos si dateutil está instalado.
    """
    if pd.isna(fecha) or fecha == "" or fecha is None:
        return None

    try:
        if isinstance(fecha, str):
            if DATEUTIL_AVAILABLE:
                # Usa dateutil para parseo flexible
                parsed = parse(fecha, dayfirst=True)  # DD/MM/YYYY primero
                return parsed.date()
            else:
                # Parseo manual básico
                if 'T' in fecha:
                    return datetime.strptime(fecha.split('T')[0], '%Y-%m-%d').date()
                elif ' ' in fecha:
                    return datetime.strptime(fecha.split()[0], '%Y-%m-%d').date()
                elif '/' in fecha:
                    # Intentar DD/MM/YYYY
                    parts = fecha.split('/')
                    if len(parts) == 3:
                        day, month, year = parts
                        return date(int(year), int(month), int(day))
                else:
                    return datetime.strptime(fecha, '%Y-%m-%d').date()
        elif isinstance(fecha, datetime):
            return fecha.date()
        elif isinstance(fecha, date):
            return fecha
        else:
            logger.warning(f"Tipo de fecha no soportado: {type(fecha)} - valor: {fecha}")
            return None
    except Exception as e:
        logger.warning(f"Error al parsear fecha '{fecha}': {e}")
        return None

# NOTA: get_next_id se ha movido a firestore_utils.py para evitar duplicación.
# Si necesitas usarla aquí, importa desde firestore_utils:
# from .firestore_utils import get_next_id