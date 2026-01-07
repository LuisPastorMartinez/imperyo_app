import pandas as pd
import streamlit as st
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, date

logger = logging.getLogger(__name__)

# ================== COLECCIONES ==================
COLLECTION_NAMES = {
    "pedidos": "pedidos",
    "gastos": "gastos",
    "totales": "totales",
    "listas": "listas",
    "trabajos": "trabajos",
    "posibles_clientes": "posibles_clientes",
}

# ================== FIRESTORE CLIENT ==================
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

# ================== SANITIZADOR DEFINITIVO ==================
def _sanitize_value_for_firestore(value):
    """
    Convierte cualquier valor pandas / numpy / date a tipo compatible Firestore.
    """

    # None / NaN / NaT
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    # numpy scalar → python nativo
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    # pandas Timestamp → datetime
    if hasattr(value, "to_pydatetime"):
        try:
            return value.to_pydatetime()
        except Exception:
            pass

    # date → datetime
    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime.combine(value, datetime.min.time())

    return value


# ================== LOAD DATA ==================
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


# ================== SAVE DATAFRAME (CREATE / REWRITE) ==================
def save_dataframe_firestore(df: pd.DataFrame, collection_key: str) -> bool:
    if db is None:
        return False

    collection_name = COLLECTION_NAMES.get(collection_key)
    if not collection_name:
        return False

    try:
        batch = db.batch()
        collection_ref = db.collection(collection_name)

        # ⚠️ Para todo menos pedidos → se rehace completo
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


# ================== UPDATE REAL (MODIFICAR SIN DUPLICAR) ==================
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


# ================== DELETE ==================
def delete_document_firestore(collection_key: str, doc_id: str) -> bool:
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


# ================== ID POR AÑO (CREAR PEDIDO / GASTO) ==================
def get_next_id_por_año(df, año, id_col="ID", año_col="Año"):
    """
    Devuelve el siguiente ID disponible SOLO para el año indicado.
    """
    if df is None or df.empty:
        return 1

    if año_col not in df.columns or id_col not in df.columns:
        return 1

    df_year = df[df[año_col] == año]

    if df_year.empty:
        return 1

    ids = pd.to_numeric(df_year[id_col], errors="coerce").dropna()

    if ids.empty:
        return 1

    return int(ids.max()) + 1
