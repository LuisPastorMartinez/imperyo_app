# utils/excel_utils.py
import pandas as pd
from datetime import datetime
from io import BytesIO

# =====================================================
# GENERAR BACKUP EN MEMORIA (STREAMLIT CLOUD)
# =====================================================
def crear_backup_en_memoria(data: dict):
    """
    Crea un archivo Excel en memoria y lo devuelve como bytes.
    """
    buffer = BytesIO()

    SHEET_NAMES = {
        "df_pedidos": "pedidos",
        "df_gastos": "gastos",
        "df_totales": "totales",
        "df_listas": "listas",
        # "df_trabajos": "trabajos",
    }

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for key, sheet_name in SHEET_NAMES.items():
            df = data.get(key)

            if df is None or df.empty:
                df = pd.DataFrame()
            else:
                df = df.copy()

                # Eliminar timezone si existe
                for col in df.columns:
                    if pd.api.types.is_datetime64_any_dtype(df[col]):
                        df[col] = df[col].dt.tz_localize(None)

            df.to_excel(writer, sheet_name=sheet_name, index=False)

    buffer.seek(0)
    return buffer
