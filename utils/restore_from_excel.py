import pandas as pd
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# =====================================================
# CONFIGURACIÓN
# =====================================================
COLLECTION_MAPPING = {
    "pedidos": "pedidos",
    "gastos": "gastos",
    "totales": "totales",
    "listas": "listas",
}


# =====================================================
# FIRESTORE CLIENT
# =====================================================
def _get_firestore_client():
    if not firebase_admin._apps:
        cred = credentials.Certificate(dict(st.secrets["firestore"]))
        firebase_admin.initialize_app(cred)
    return firestore.client()


# =====================================================
# RESTORE DESDE EXCEL (STREAMLIT CLOUD)
# =====================================================
def restore_from_excel(uploaded_file):
    """
    Restaura datos desde un Excel subido por Streamlit.
    BORRA las colecciones actuales y carga las del Excel.
    """
    try:
        db = _get_firestore_client()
        xls = pd.ExcelFile(uploaded_file)

        for sheet_name, collection_name in COLLECTION_MAPPING.items():
            if sheet_name not in xls.sheet_names:
                logger.warning(f"Hoja '{sheet_name}' no encontrada")
                continue

            df = pd.read_excel(xls, sheet_name=sheet_name)
            col_ref = db.collection(collection_name)

            # =====================================
            # BORRAR COLECCIÓN ACTUAL (BATCH)
            # =====================================
            docs = list(col_ref.stream())
            if docs:
                batch = db.batch()
                for doc in docs:
                    batch.delete(doc.reference)
                batch.commit()

            # =====================================
            # SUBIR DATOS NUEVOS
            # =====================================
            for _, row in df.iterrows():
                data = row.to_dict()

                # Limpiar fechas
                for k, v in data.items():
                    if isinstance(v, pd.Timestamp):
                        data[k] = v.to_pydatetime()
                    elif isinstance(v, datetime):
                        data[k] = v

                col_ref.add(data)

            logger.info(
                f"Colección '{collection_name}' restaurada con {len(df)} documentos."
            )

        return True, "Datos restaurados correctamente"

    except Exception as e:
        logger.error(f"Error al restaurar datos: {e}")
        return False, str(e)
