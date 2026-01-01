import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

COLLECTION_NAMES = {
    'pedidos': 'pedidos',
    'gastos': 'gastos',
    'totales': 'totales',
    'listas': 'listas',
    'trabajos': 'trabajos',
    'posibles_clientes': 'posibles_clientes'
}

def get_firestore_client():
    if 'firestore_client' not in st.session_state:
        try:
            cred_dict = dict(st.secrets["firestore"])
            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            st.session_state.firestore_client = firestore.client()
        except Exception as e:
            st.error(f"Error inicializando Firestore: {e}")
            return None
    return st.session_state.firestore_client

db = get_firestore_client()

def load_dataframes_firestore():
    if db is None:
        return None

    data = {}
    for key, collection_name in COLLECTION_NAMES.items():
        docs = db.collection(collection_name).stream()
        records = []
        for doc in docs:
            r = doc.to_dict()
            r['id_documento_firestore'] = doc.id
            records.append(r)

        df = pd.DataFrame(records) if records else pd.DataFrame()
        data[f'df_{key}'] = df

    return data

def save_dataframe_firestore(df: pd.DataFrame, collection_key: str) -> bool:
    if db is None:
        return False

    collection_name = COLLECTION_NAMES.get(collection_key)
    if not collection_name:
        return False

    try:
        batch = db.batch()
        collection_ref = db.collection(collection_name)

        if collection_key != 'pedidos':
            for doc in collection_ref.stream():
                batch.delete(doc.reference)

        for _, row in df.iterrows():
            record = row.drop('id_documento_firestore', errors='ignore').to_dict()
            doc_id = row.get('id_documento_firestore')
            doc_ref = collection_ref.document(doc_id) if doc_id else collection_ref.document()
            batch.set(doc_ref, record)

        batch.commit()
        return True
    except Exception as e:
        st.error(f"Error guardando en Firestore: {e}")
        return False

def delete_document_firestore(collection_key, doc_id):
    if db is None:
        return False
    collection_name = COLLECTION_NAMES.get(collection_key)
    try:
        db.collection(collection_name).document(doc_id).delete()
        return True
    except Exception as e:
        st.error(f"Error eliminando documento: {e}")
        return False

def get_next_id(df, id_column):
    if df.empty or id_column not in df.columns:
        return 1
    return int(pd.to_numeric(df[id_column], errors='coerce').max()) + 1

# ✅ NUEVA FUNCIÓN — ID REINICIADO POR AÑO
def get_next_id_por_año(df, año, id_column='ID', year_column='Año'):
    if df.empty:
        return 1

    df_año = df[df[year_column] == año]
    if df_año.empty:
        return 1

    df_año[id_column] = pd.to_numeric(df_año[id_column], errors='coerce')
    df_año = df_año.dropna(subset=[id_column])

    return 1 if df_año.empty else int(df_año[id_column].max()) + 1
