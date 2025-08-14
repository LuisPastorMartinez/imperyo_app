import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, date
import numpy as np
import logging
from typing import Dict, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

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
    """Convierte tipos de Python/pandas a tipos compatibles con Firestore"""
    if pd.isna(value) or value is None:
        return None
    elif isinstance(value, (pd.Timestamp, datetime)):
        return value.to_pydatetime()
    elif isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    elif isinstance(value, (np.integer)):
        return int(value)
    elif isinstance(value, (np.floating)):
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
            records = [dict(doc.to_dict(), id_documento_firestore=doc.id) for doc in docs]
            
            df = pd.DataFrame(records) if records else pd.DataFrame()
            
            if key == 'pedidos':
                bool_cols = ['Inicio Trabajo', 'Cobrado', 'Retirado', 'Pendiente', 'Trabajo Terminado']
                for col in bool_cols:
                    if col in df.columns:
                        df[col] = df[col].fillna(False).astype(bool)
            
            data[f'df_{key}'] = df
        return data
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return None

def save_dataframe_firestore(df, collection_key):
    """Guarda un DataFrame en Firestore"""
    if db is None:
        return False

    collection_name = COLLECTION_NAMES.get(collection_key)
    if not collection_name:
        return False

    try:
        batch = db.batch()
        col_ref = db.collection(collection_name)
        
        if collection_key == 'pedidos':
            for _, row in df.iterrows():
                doc_data = row.drop('id_documento_firestore', errors='ignore').to_dict()
                doc_id = row.get('id_documento_firestore')
                
                if doc_id:
                    batch.update(col_ref.document(doc_id), doc_data)
                else:
                    new_doc = col_ref.document()
                    batch.set(new_doc, doc_data)
        else:
            docs = list(col_ref.stream())
            for doc in docs:
                batch.delete(doc.reference)
                
            for _, row in df.iterrows():
                new_doc = col_ref.document()
                batch.set(new_doc, row.to_dict())
        
        batch.commit()
        return True
    except Exception as e:
        st.error(f"Error guardando datos: {e}")
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