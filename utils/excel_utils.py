import streamlit as st
import pandas as pd
import os

# Define the path to your local Excel file, now assuming it's in a 'data' folder
# relative to the 'Imperyo_app' root, which is one level up from 'utils'.
# os.path.dirname(__file__) gets the directory of the current file (excel_utils.py)
# ".." goes up one level (to Imperyo_app/)
# "data" goes into the data folder
# "2025_1 Gastos.xlsm" is the file name
EXCEL_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "2025_1 Gastos.xlsm")

# Define the names of your Excel sheets (MUST match exactly)
SHEET_NAMES = {
    'pedidos': 'Pedidos',
    'gastos': 'Gastos',
    'totales': 'Totales',
    'listas': 'Listas',
    'trabajos': 'Trabajos'
}

@st.cache_data(ttl=600) # Cache data for 10 minutes
def load_dataframes_local():
    """
    Loads all necessary dataframes from the local Excel file.
    Returns a dictionary of Dataframes.
    """
    if not os.path.exists(EXCEL_FILE_PATH):
        st.error(f"Error: El archivo Excel '{EXCEL_FILE_PATH}' no se encontró.")
        st.info(f"Asegúrate de que el archivo Excel esté en la carpeta 'data' dentro de la carpeta principal de tu aplicación: {os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))}")
        return None
    
    try:
        data = {} # <-- ¡CORRECCIÓN: Inicializamos el diccionario 'data' aquí!
        for key, sheet_name in SHEET_NAMES.items():
            data[f'df_{key}'] = pd.read_excel(EXCEL_FILE_PATH, sheet_name=sheet_name)
        return data
    except Exception as e:
        st.error(f"Error al cargar datos del archivo Excel '{EXCEL_FILE_PATH}': {e}")
        st.info("Asegúrate de que los nombres de las hojas en tu Excel coincidan exactamente (mayúsculas/minúsculas) con los definidos en SHEET_NAMES.")
        return None

def save_dataframe_local(df, sheet_key):
    """
    Saves a given DataFrame back to a specific sheet in the local Excel file.
    This overwrites the existing sheet.
    """
    sheet_name = SHEET_NAMES.get(sheet_key)
    if not sheet_name:
        st.error(f"Error: Clave de hoja '{sheet_key}' no reconocida para guardar.")
        return False

    try:
        # Load all sheets to preserve those not being updated
        # We need to read the existing file to get all sheets, then update one
        # and write all back. This is more complex for Excel than just replacing one sheet.
        # A simpler approach for local Excel is to just overwrite the specific sheet.
        # However, if you have other sheets not handled by the app, they would be lost.
        # For this local version, we will assume only the sheets managed by the app are important.
        
        # Read all existing sheets into a dictionary of dataframes
        existing_sheets = pd.read_excel(EXCEL_FILE_PATH, sheet_name=None) # sheet_name=None reads all sheets

        # Update the specific sheet with the new dataframe
        existing_sheets[sheet_name] = df

        # Write all dataframes back to the Excel file
        with pd.ExcelWriter(EXCEL_FILE_PATH, engine='openpyxl') as writer:
            for sheet_name_to_write, df_to_write in existing_sheets.items():
                df_to_write.to_excel(writer, sheet_name=sheet_name_to_write, index=False)
        return True
    except Exception as e:
        st.error(f"Error al guardar datos en la hoja de Excel '{sheet_name}': {e}")
        st.info("Asegúrate de que el archivo Excel no esté abierto en otra aplicación y que los permisos sean correctos.")
        return False

def get_next_id(df, id_column_name):
    """
    Finds the next available ID by looking at the maximum existing ID
    in a DataFrame and adding 1. If the DataFrame is empty, starts from 1.
    """
    if df.empty or id_column_name not in df.columns:
        return 1
    # Ensure the ID column is numeric, coercing errors to NaN
    df[id_column_name] = pd.to_numeric(df[id_column_name], errors='coerce')
    # Drop any rows where the ID became NaN (e.g., non-numeric IDs)
    df_clean = df.dropna(subset=[id_column_name])
    if df_clean.empty:
        return 1
    return int(df_clean[id_column_name].max()) + 1


