# utils/data_utils.py
import re
import pandas as pd

def limpiar_telefono(numero):
    """
    Convierte el número a string y limpia formatos, devolviendo solo los dígitos.
    Se ha corregido para que siempre devuelva una cadena.
    """
    if pd.isna(numero) or str(numero).strip() == "":
        return ""
    
    numero_limpio = re.sub(r'[^0-9]', '', str(numero))
    
    return numero_limpio
def limpiar_fecha(fecha):
    """Convierte la fecha a formato date (sin hora)"""
    if pd.isna(fecha) or fecha == "":
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
    # Asegura que la columna ID sea numérica, forzando errores a NaN
    df[id_column_name] = pd.to_numeric(df[id_column_name], errors='coerce')
    # Elimina cualquier fila donde el ID se convirtió en NaN (ej., IDs no numéricos)
    df_numeric = df.dropna(subset=[id_column_name])
    if df_numeric.empty:
        return 1
    # Encuentra el ID máximo y le suma 1 para el nuevo ID
    return int(df_numeric[id_column_name].max()) + 1