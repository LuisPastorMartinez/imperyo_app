import pandas as pd
import streamlit as st
import logging
import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger(__name__)

# ---------- COLECCIONES ----------
COLLECTION_NAMES = {
    "pedidos": "pedidos",
    "gastos": "gastos",
    "totales": "totales",
    "listas": "listas",
    "trabajos": "trabajos",
    "posibles_clientes": "posibles_clientes",
}

# ---------- FIRESTORE CLIENT ----------
def get_firestore_client():
    if "firestore_client" not in st.session_state:
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


# ---------- SANITIZAR ----------
def _sanitize_value_for_firestore(value):
    if pd.isna(value):
        return None
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime()
    return value


# ---------- LOAD ----------
def load_dataframes_firestore():
    if db is None:
        return None

    data = {}

    for key, collection_name in COLLECTION_NAMES.items():
        docs = db.collection(collection_name).stream()
        rows = []

        for doc in docs:
            r = doc.to_dict()
            r["id_documento_firestore"] = doc.id
            rows.append(r)

        data[f"df_{key}"] = pd.DataFrame(rows) if rows else pd.DataFrame()

    return data


# ---------- SAVE (CREATE / REWRITE) ----------
def save_dataframe_firestore(df: pd.DataFrame, collection_key: str) -> bool:
    if db is None:
        return False

    collection_name = COLLECTION_NAMES.get(collection_key)
    if not collection_name:
        return False

    try:
        batch = db.batch()
        collection_ref = db.collection(collection_name)

        # 🔥 borrar colección (menos pedidos)
        if collection_key != "pedidos":
            for doc in collection_ref.stream():
                batch.delete(doc.reference)

        for _, row in df.iterrows():
            record = {}
            for k, v in row.items():
                if k == "id_documento_firestore":
                    continue
                record[k] = _sanitize_value_for_firestore(v)

            doc_id = row.get("id_documento_firestore")
            doc_ref = (
                collection_ref.document(doc_id)
                if doc_id
                else collection_ref.document()
            )
            batch.set(doc_ref, record)

        batch.commit()
        return True

    except Exception as e:
        st.error(f"Error guardando en Firestore: {e}")
        return False


# ---------- UPDATE REAL (🔥 CLAVE 🔥) ----------
def update_document_firestore(collection_key: str, doc_id: str, data: dict) -> bool:
    if db is None or not doc_id:
        return False

    collection_name = COLLECTION_NAMES.get(collection_key)
    if not collection_name:
        return False

    try:
        clean_data = {}
        for k, v in data.items():
            if k == "id_documento_firestore":
                continue
            clean_data[k] = _sanitize_value_for_firestore(v)

        db.collection(collection_name).document(doc_id).update(clean_data)
        return True

    except Exception as e:
        st.error(f"Error actualizando documento en Firestore: {e}")
        return False


# ---------- DELETE ----------
def delete_document_firestore(collection_key: str, doc_id: str) -> bool:
    if db is None:
        return False

    collection_name = COLLECTION_NAMES.get(collection_key)
    try:
        db.collection(collection_name).document(doc_id).delete()
        return True
    except Exception as e:
        st.error(f"Error eliminando documento: {e}")
        return False
