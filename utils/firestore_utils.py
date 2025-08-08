# utils/firestore_utils.py
import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from .data_utils import get_next_id

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
    """Inicializa conexión con Firestore"""
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(dict(st.secrets["firestore"]))
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Error inicializando Firestore: {e}")
        return None

db = initialize_firestore()

def load_dataframes_firestore():
    """Carga dataframes desde Firestore"""
    if db is None:
        return None

    data = {}
    try:
        for key, collection_name in COLLECTION_NAMES.items():
            docs = db.collection(collection_name).stream()
            records = [dict(doc.to_dict(), id_documento_firestore=doc.id) for doc in docs]
            
            if records:
                df = pd.DataFrame(records)
                # Procesamiento especial para pedidos
                if key == 'pedidos':
                    bool_cols = ['Inicio Trabajo', 'Cobrado', 'Retirado', 'Pendiente', 'Trabajo Terminado']
                    for col in bool_cols:
                        if col in df.columns:
                            df[col] = df[col].apply(lambda x: bool(x) if pd.notna(x) else False)
            else:
                df = create_empty_dataframe(collection_name)
            
            data[f'df_{key}'] = df
        return data
    except Exception as e:
        st.error(f"Error cargando Firestore: {e}")
        return None

def create_empty_dataframe(collection_name):
    """Crea un DataFrame vacío con la estructura adecuada para cada colección"""
    if collection_name == 'pedidos':
        return pd.DataFrame(columns=[
            'ID', 'Producto', 'Cliente', 'Teléfono', 'Club', 'Talla', 'Tela',
            'Breve Descripción', 'Fecha Entrada', 'Fecha Salida', 'Precio',
            'Precio Factura', 'Tipo de pago', 'Adelanto', 'Observaciones',
            'Inicio Trabajo', 'Cobrado', 'Retirado', 'Pendiente', 'Trabajo Terminado',
            'id_documento_firestore'
        ])
    # Agregar otros casos según necesidad
    return pd.DataFrame()

def save_dataframe_firestore(df, collection_key):
    """Guarda un dataframe en Firestore"""
    if db is None:
        return False

    collection_name = COLLECTION_NAMES.get(collection_key)
    if not collection_name:
        return False

    try:
        if collection_key == 'pedidos':
            for _, row in df.iterrows():
                record = row.drop('id_documento_firestore').to_dict()
                doc_id = row.get('id_documento_firestore')
                if doc_id:
                    db.collection(collection_name).document(doc_id).set(record)
                else:
                    db.collection(collection_name).add(record)
        else:
            # Lógica para otras colecciones
            pass
        return True
    except Exception as e:
        st.error(f"Error guardando en Firestore: {e}")
        return False

def delete_document_firestore(collection_key, doc_id):
    """Elimina un documento de Firestore"""
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