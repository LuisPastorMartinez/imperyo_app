import pandas as pd
import logging
from google.cloud import firestore

logger = logging.getLogger(__name__)

# ---------------- FIRESTORE CLIENT ----------------
def get_firestore_client():
    try:
        return firestore.Client()
    except Exception as e:
        logger.error(f"Error creando cliente Firestore: {e}")
        return None


# ---------------- LOAD DATA ----------------
def load_dataframes_firestore():
    """
    Carga todas las colecciones necesarias de Firestore
    y las devuelve como DataFrames.
    """
    client = get_firestore_client()
    if not client:
        return None

    data = {}

    colecciones = {
        "df_pedidos": "pedidos",
        "df_gastos": "gastos",
        "df_totales": "totales",
        "df_listas": "listas",
        "df_trabajos": "trabajos",
    }

    try:
        for df_name, collection_name in colecciones.items():
            docs = client.collection(collection_name).stream()
            rows = []
            for doc in docs:
                d = doc.to_dict()
                d["id_documento_firestore"] = doc.id
                rows.append(d)

            data[df_name] = pd.DataFrame(rows)

        return data

    except Exception as e:
        logger.error(f"Error cargando datos desde Firestore: {e}")
        return None


# ---------------- SAVE DATA ----------------
def save_dataframe_firestore(df, collection_name):
    """
    Guarda un DataFrame completo en Firestore.
    Usa id_documento_firestore si existe.
    """
    client = get_firestore_client()
    if not client:
        return False

    try:
        collection_ref = client.collection(collection_name)

        for _, row in df.iterrows():
            data = row.to_dict()
            doc_id = data.pop("id_documento_firestore", None)

            # Limpiar NaN
            for k, v in data.items():
                if pd.isna(v):
                    data[k] = None

            if doc_id:
                collection_ref.document(doc_id).set(data)
            else:
                doc_ref = collection_ref.document()
                doc_ref.set(data)
                df.loc[row.name, "id_documento_firestore"] = doc_ref.id

        return True

    except Exception as e:
        logger.error(f"Error guardando DataFrame en Firestore ({collection_name}): {e}")
        return False


# ---------------- DELETE DOCUMENT ----------------
def delete_document_firestore(collection_name, doc_id):
    """
    Elimina un documento concreto por ID técnico de Firestore.
    """
    client = get_firestore_client()
    if not client:
        return False

    try:
        client.collection(collection_name).document(doc_id).delete()
        return True
    except Exception as e:
        logger.error(f"Error eliminando documento {doc_id}: {e}")
        return False


# ---------------- ID HELPERS ----------------
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


# ⚠️ LEGACY (NO USAR PARA PEDIDOS)
def get_next_id(df, id_col="ID"):
    """
    ❌ LEGACY: ID global.
    Se mantiene solo por compatibilidad con otros módulos.
    NO usar para pedidos.
    """
    if df is None or df.empty or id_col not in df.columns:
        return 1

    ids = pd.to_numeric(df[id_col], errors="coerce").dropna()
    return int(ids.max()) + 1 if not ids.empty else 1
