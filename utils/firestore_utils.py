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
    """Convierte tipos de Python a tipos compatibles con Firestore"""
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    elif isinstance(value, datetime.date):
        return datetime.combine(value, datetime.min.time())
    elif pd.isna(value) or value is None:
        return None
    elif isinstance(value, (np.int64, np.int32)):
        return int(value)
    elif isinstance(value, (np.float64, np.float32)):
        return float(value)
    return value

def load_dataframes_firestore():
    """Carga todos los DataFrames desde Firestore"""
    if db is None:
        return None

    data = {}
    try:
        for key, collection_name in COLLECTION_NAMES.items():
            docs = db.collection(collection_name).stream()
            records = []
            
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data['id_documento_firestore'] = doc.id
                records.append(doc_data)

            if records:
                df = pd.DataFrame(records)
                
                # Conversión de tipos para pedidos
                if key == 'pedidos':
                    bool_cols = ['Inicio Trabajo', 'Cobrado', 'Retirado', 'Pendiente', 'Trabajo Terminado']
                    for col in bool_cols:
                        if col in df.columns:
                            df[col] = df[col].astype(bool)
                    
                    date_cols = ['Fecha entrada', 'Fecha Salida']
                    for col in date_cols:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col]).dt.date
            else:
                df = create_empty_dataframe(collection_name)
            
            data[f'df_{key}'] = df
        return data
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return None

def save_dataframe_firestore(df, collection_key):
    """Guarda un DataFrame en Firestore con conversión de tipos"""
    if db is None:
        return False

    collection_name = COLLECTION_NAMES.get(collection_key)
    if not collection_name:
        return False

    try:
        # Convertir tipos antes de guardar
        df = df.copy()
        for col in df.columns:
            df[col] = df[col].apply(convert_to_firestore_types)

        if collection_key == 'pedidos':
            for _, row in df.iterrows():
                record = row.drop('id_documento_firestore', errors='ignore').to_dict()
                doc_id = row.get('id_documento_firestore')
                
                if doc_id:
                    db.collection(collection_name).document(doc_id).set(record)
                else:
                    db.collection(collection_name).add(record)
        else:
            # Para otras colecciones (borrar y recrear)
            batch = db.batch()
            docs = db.collection(collection_name).stream()
            
            for doc in docs:
                batch.delete(doc.reference)
            
            for _, row in df.iterrows():
                record = row.to_dict()
                new_doc = db.collection(collection_name).document()
                batch.set(new_doc, record)
            
            batch.commit()
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
    df_clean = df.dropna(subset=[id_column_name])
    return 1 if df_clean.empty else int(df_clean[id_column_name].max()) + 1