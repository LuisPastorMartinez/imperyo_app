# utils/firestore_utils.py
import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import numpy as np

# Configuración de colecciones
COLLECTION_NAMES = {
    'pedidos': 'pedidos',
    'gastos': 'gastos',
    'totales': 'totales', 
    'listas': 'listas',
    'trabajos': 'trabajos'
}

@st.cache_resource
def initialize_firestore():
    """Inicializa la conexión con Firestore"""
    try:
        if not firebase_admin._apps:
            cred_dict = dict(st.secrets["firestore"])
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Error inicializando Firestore: {e}")
        return None

db = initialize_firestore()

def convert_to_firestore_types(value):
    """
    Convierte tipos de Python a tipos compatibles con Firestore,
    incluyendo un manejo robusto de booleanos, fechas y valores nulos.
    """
    if pd.isna(value) or value is None or (isinstance(value, str) and value.strip() == ''):
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    elif isinstance(value, datetime.date):
        return datetime.combine(value, datetime.min.time())
    elif isinstance(value, bool):
        return bool(value)
    elif isinstance(value, (np.int64, np.int32)):
        return int(value)
    elif isinstance(value, (np.float64, np.float32)):
        return float(value)
    elif isinstance(value, (int, float, str, datetime)):
        return value
    return str(value)

def save_dataframe_firestore(df, collection_key):
    """
    Guarda un DataFrame en una colección de Firestore.
    Esta función ahora maneja de forma más robusta la conversión de tipos
    para evitar errores al guardar en Firestore.
    """
    if 'id_documento_firestore' not in df.columns:
        df['id_documento_firestore'] = [None] * len(df)

    db = firestore.client()
    collection_name = COLLECTION_NAMES.get(collection_key)

    try:
        for _, row in df.iterrows():
            if pd.isna(row.get('id_documento_firestore')):
                doc_ref = db.collection(collection_name).document()
                row['id_documento_firestore'] = doc_ref.id
            else:
                doc_ref = db.collection(collection_name).document(row['id_documento_firestore'])

            data_to_save = {}
            for col_name, value in row.items():
                if col_name != 'id_documento_firestore':
                    data_to_save[col_name] = convert_to_firestore_types(value)

            doc_ref.set(data_to_save)
        
        st.success(f"DataFrame guardado correctamente en la colección '{collection_name}'.")
        return True
    
    except Exception as e:
        st.error(f"Error guardando en Firestore: {e}")
        return False

def delete_document_firestore(collection_key, doc_id):
    """Elimina un documento específico"""
    if db is None:
        return False
    collection_name = COLLECTION_NAMES.get(collection_key)
    if not collection_name:
        return False
    try:
        db.collection(collection_name).document(doc_id).delete()
        return True
    except Exception as e:
        st.error(f"Error eliminando documento: {e}")
        return False

def create_empty_dataframe(collection_name):
    """Crea DataFrames vacíos con la estructura correcta"""
    if collection_name == 'pedidos':
        return pd.DataFrame(columns=[
            'ID', 'Producto', 'Cliente', 'Telefono', 'Club', 'Talla', 'Tela',
            'Breve Descripción', 'Fecha entrada', 'Fecha Salida', 'Precio',
            'Precio Factura', 'Tipo de pago', 'Adelanto', 'Observaciones',
            'Inicio Trabajo', 'Cobrado', 'Retirado', 'Pendiente', 'Trabajo Terminado',
            'id_documento_firestore'
        ])
    elif collection_name == 'gastos':
        return pd.DataFrame(columns=['ID', 'Fecha', 'Concepto', 'Importe', 'Tipo', 'id_documento_firestore'])
    return pd.DataFrame()

def get_next_id(df, id_column_name):
    """Obtiene el próximo ID disponible"""
    if df.empty or id_column_name not in df.columns:
        return 1
    df[id_column_name] = pd.to_numeric(df[id_column_name], errors='coerce')
    return int(df[id_column_name].max()) + 1 if pd.notna(df[id_column_name].max()) else 1