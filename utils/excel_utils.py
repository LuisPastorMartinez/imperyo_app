# utils/excel_utils.py
import os
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook

# =====================================================
# CONFIGURACIÓN
# =====================================================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
BACKUP_DIR = os.path.join(BASE_DIR, "backups")

SHEET_NAMES = {
    "df_pedidos": "pedidos",
    "df_gastos": "gastos",
    "df_totales": "totales",
    "df_listas": "listas",
    "df_trabajos": "trabajos",
}

# =====================================================
# BACKUP LOCAL
# =====================================================
def crear_backup_local(data: dict):
    """
    Crea un archivo Excel de backup en la carpeta /backups del proyecto.
    """
    os.makedirs(BACKUP_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"backup_imperyo_{timestamp}.xlsx"
    filepath = os.path.join(BACKUP_DIR, filename)

    try:
        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
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

        return True, filepath

    except Exception as e:
        return False, str(e)
