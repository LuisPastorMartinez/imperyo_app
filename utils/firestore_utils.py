import pandas as pd
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

COLLECTIONS = {
    "pedidos": "pedidos",
    "gastos": "gastos",
    "totales": "totales",
    "listas": "listas",
    "trabajos": "trabajos",
    "posibles_clientes": "posibles_clientes",
}

# =====================================
# CLIENTE FIRESTORE
# =====================================
def get_firestore_client():
    if "firestore_client" not in st.session_state:
        cred = credentials.Certificate(dict(st.secrets["firestore"]))
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        st.session_state.firestore_client = firestore.client()
    return st.session_state.firestore_client


# =====================================
# CARGA DE DATAFRAMES
# =====================================
def load_dataframes_firestore():
    db = get_firestore_client()
    data = {}

    for key, collection in COLLECTIONS.items():
        rows = []
        for doc in db.collection(collection).stream():
            r = doc.to_dict()
            r["id_documento_firestore"] = doc.id
            rows.append(r)
        data[f"df_{key}"] = pd.DataFrame(rows)

    return data


# =====================================
# GUARDAR DATAFRAME COMPLETO
# =====================================
def save_dataframe_firestore(df, collection_key):
    db = get_firestore_client()
    collection = COLLECTIONS[collection_key]
    col_ref = db.collection(collection)

    batch = db.batch()

    if collection_key != "pedidos":
        for doc in col_ref.stream():
            batch.delete(doc.reference)

    for _, row in df.iterrows():
        data = {
            k: _sanitize(v)
            for k, v in row.items()
            if k != "id_documento_firestore"
        }

        doc_id = row.get("id_documento_firestore")
        ref = col_ref.document(doc_id) if doc_id else col_ref.document()
        batch.set(ref, data)

    batch.commit()
    return True


# =====================================
# AÑADIR DOCUMENTO NUEVO (CORRECCIÓN)
# =====================================
def add_document_firestore(collection_key, data):
    db = get_firestore_client()
    collection = COLLECTIONS[collection_key]
    clean = {k: _sanitize(v) for k, v in data.items()}
    db.collection(collection).add(clean)
    return True


# =====================================
# ACTUALIZAR DOCUMENTO EXISTENTE
# =====================================
def update_document_firestore(collection_key, doc_id, data):
    if not doc_id:
        raise ValueError("doc_id es obligatorio para update_document_firestore")

    db = get_firestore_client()
    collection = COLLECTIONS[collection_key]
    clean = {k: _sanitize(v) for k, v in data.items()}
    db.collection(collection).document(doc_id).update(clean)
    return True


# =====================================
# BORRAR DOCUMENTO
# =====================================
def delete_document_firestore(collection_key, doc_id):
    db = get_firestore_client()
    collection = COLLECTIONS[collection_key]
    db.collection(collection).document(doc_id).delete()
    return True


# =====================================
# NEXT ID POR AÑO (NO TOCAR)
# =====================================
def get_next_id_por_año(df, año):
    if df is None or df.empty:
        return 1
    df_año = df[df["Año"] == año]
    if df_año.empty:
        return 1
    return int(pd.to_numeric(df_año["ID"], errors="coerce").max()) + 1


# =====================================
# SANITIZADOR INTERNO
# =====================================
def _sanitize(value):
    try:
        if value is None or pd.isna(value):
            return None
    except Exception:
        pass

    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime.combine(value, datetime.min.time())

    if hasattr(value, "to_pydatetime"):
        try:
            return value.to_pydatetime()
        except Exception:
            pass

    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    return value
