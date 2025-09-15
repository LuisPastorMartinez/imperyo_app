# utils/excel_utils.py
import streamlit as st
import pandas as pd
import os
from openpyxl import load_workbook
from .firestore_utils import get_next_id
import dropbox
from datetime import datetime

# Configuración de rutas y nombres de hojas
EXCEL_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "2025_1 Gastos.xlsm")

SHEET_NAMES = {
    'pedidos': 'Pedidos',
    'gastos': 'Gastos',
    'totales': 'Totales',
    'listas': 'Listas',
    'trabajos': 'Trabajos'
}

@st.cache_data(ttl=600)
def load_dataframes_local():
    """Carga dataframes desde archivo Excel local"""
    if not os.path.exists(EXCEL_FILE_PATH):
        st.warning(f"Archivo Excel no encontrado en {EXCEL_FILE_PATH}. Se crearán DataFrames vacíos.")
        return create_empty_dataframes()

    try:
        data = {}
        xls = pd.ExcelFile(EXCEL_FILE_PATH)
        available_sheets = xls.sheet_names

        for key, sheet_name in SHEET_NAMES.items():
            if sheet_name in available_sheets:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                data[f'df_{key}'] = df
            else:
                st.warning(f"Hoja '{sheet_name}' no encontrada. Se creará vacía.")
                data[f'df_{key}'] = create_empty_dataframe(key)

        return data
    except Exception as e:
        st.error(f"Error al cargar Excel: {e}")
        return create_empty_dataframes()

def save_dataframe_local(df, sheet_key):
    """Guarda un dataframe en una hoja específica del Excel"""
    sheet_name = SHEET_NAMES.get(sheet_key)
    if not sheet_name:
        st.error(f"Hoja '{sheet_key}' no reconocida")
        return False

    try:
        if not os.path.exists(EXCEL_FILE_PATH):
            st.warning(f"Archivo Excel no existe. Creando nuevo archivo en {EXCEL_FILE_PATH}")
            with pd.ExcelWriter(EXCEL_FILE_PATH, engine='openpyxl') as writer:
                for sn in SHEET_NAMES.values():
                    create_empty_dataframe_from_key(sn).to_excel(writer, sheet_name=sn, index=False)
        
        book = load_workbook(EXCEL_FILE_PATH)
        writer = pd.ExcelWriter(EXCEL_FILE_PATH, engine='openpyxl')
        writer.book = book
        writer.sheets = {ws.title: ws for ws in book.worksheets}

        df.to_excel(writer, sheet_name=sheet_name, index=False)
        writer.save()
        writer.close()

        load_dataframes_local.clear()
        return True

    except Exception as e:
        st.error(f"Error al guardar Excel: {e}")
        return False

def create_empty_dataframe_from_key(sheet_key):
    """Crea DataFrame vacío según el tipo de hoja"""
    if sheet_key == 'Pedidos':
        return pd.DataFrame(columns=[
            'ID', 'Producto', 'Cliente', 'Telefono', 'Club', 'Talla', 'Tela',
            'Breve Descripción', 'Fecha entrada', 'Fecha Salida', 'Precio',
            'Precio Factura', 'Tipo de pago', 'Adelanto', 'Observaciones',
            'Inicio Trabajo', 'Cobrado', 'Retirado', 'Pendiente', 'Trabajo Terminado'
        ])
    elif sheet_key == 'Gastos':
        return pd.DataFrame(columns=['ID', 'Fecha', 'Concepto', 'Importe', 'Tipo'])
    elif sheet_key == 'Totales':
        return pd.DataFrame()
    elif sheet_key == 'Listas':
        return pd.DataFrame()
    elif sheet_key == 'Trabajos':
        return pd.DataFrame()
    return pd.DataFrame()

def create_empty_dataframe(key):
    """Crea DataFrame vacío según la clave del diccionario"""
    if key == 'pedidos':
        return create_empty_dataframe_from_key('Pedidos')
    elif key == 'gastos':
        return create_empty_dataframe_from_key('Gastos')
    return pd.DataFrame()

def create_empty_dataframes():
    """Crea todos los DataFrames vacíos"""
    return {
        'df_pedidos': create_empty_dataframe('pedidos'),
        'df_gastos': create_empty_dataframe('gastos'),
        'df_totales': pd.DataFrame(),
        'df_listas': pd.DataFrame(),
        'df_trabajos': pd.DataFrame()
    }

# ✅ FUNCIONES PARA BACKUP A DROPBOX
def upload_to_dropbox(file_path, dropbox_path, access_token):
    """Sube un archivo a Dropbox."""
    try:
        dbx = dropbox.Dropbox(access_token)
        with open(file_path, "rb") as f:
            dbx.files_upload(
                f.read(),
                dropbox_path,
                mode=dropbox.files.WriteMode.overwrite
            )
        return True, None
    except Exception as e:
        return False, str(e)

def backup_to_dropbox(data, backup_folder="backups"):
    """Genera un backup en Excel y lo sube a Dropbox."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_imperyo_{timestamp}.xlsx"
    backup_path = os.path.join(backup_folder, filename)

    os.makedirs(backup_folder, exist_ok=True)

    try:
        with pd.ExcelWriter(backup_path, engine='openpyxl') as writer:
            for key, df in data.items():
                # ✅ Eliminar zona horaria de columnas de fecha/hora
                df = df.copy()  # No modificar el original
                for col in df.columns:
                    if pd.api.types.is_datetime64_any_dtype(df[col]):
                        df[col] = df[col].dt.tz_localize(None)  # ✅ Eliminar zona horaria
                
                sheet_name = key.replace("df_", "")[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        # ✅ Verificar que el archivo se creó
        if not os.path.exists(backup_path):
            raise Exception(f"Archivo no creado: {backup_path}")

        # Subir a Dropbox
        DROPBOX_ACCESS_TOKEN = st.secrets["dropbox"]["access_token"]
        DROPBOX_PATH = f"/{filename}"
        upload_success, upload_error = upload_to_dropbox(backup_path, DROPBOX_PATH, DROPBOX_ACCESS_TOKEN)

        if not upload_success:
            raise Exception(f"Error al subir a Dropbox: {upload_error}")

        # ✅ Guardar fecha del último backup en sesión
        st.session_state.last_backup = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return True, f"Backup subido correctamente: {filename}", True, None

    except Exception as e:
        return False, str(e), False, str(e)