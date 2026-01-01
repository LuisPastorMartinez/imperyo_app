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


def _sanitize_value_for_firestore(value):
    """
    Convierte cualquier valor de pandas/python a algo
    100% compatible con Firestore.
    """
    # NaT / NaN / None
    try:
        if value is None or pd.isna(value):
            return None
    except Exception:
        pass

    # pandas Timestamp
    if isinstance(value, pd.Timestamp):
        try:
            if value.tzinfo is not None:
                return value.tz_convert(None).to_pydatetime()
            return value.to_pydatetime()
        except Exception:
            return None

    # datetime con timezone
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            return value.replace(tzinfo=None)
        return value

    return value


def save_dataframe_firestore(df: pd.DataFrame, collection_key: str) -> bool:
    if db is None:
        return False

    collection_name = COLLECTION_NAMES.get(collection_key)
    if not collection_name:
        return False

    try:
        batch = db.batch()
        collection_ref = db.collection(collection_name)

        # Limpiar colección completa salvo pedidos
        if collection_key != 'pedidos':
            for doc in collection_ref.stream():
                batch.delete(doc.reference)

        for _, row in df.iterrows():
            record = {}
            for k, v in row.items():
                if k == 'id_documento_firestore':
                    continue
                record[k] = _sanitize_value_for_firestore(v)

            doc_id = row.get('id_documento_firestore')
            doc_ref = (
                collection_ref.document(doc_id)
                if doc_id else
                collection_ref.document()
            )

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


# ❌ LEGACY (no usar para pedidos)
def get_next_id(df, id_column):
    if df.empty or id_column not in df.columns:
        return 1
    return int(pd.to_numeric(df[id_column], errors='coerce').max()) + 1


# ✅ ID POR AÑO
def get_next_id_por_año(df, año, id_column='ID', year_column='Año'):
    if df.empty:
        return 1

    df_año = df[df[year_column] == año]
    if df_año.empty:
        return 1

    df_año[id_column] = pd.to_numeric(df_año[id_column], errors='coerce')
    df_año = df_año.dropna(subset=[id_column])

    return int(df_año[id_column].max()) + 1
