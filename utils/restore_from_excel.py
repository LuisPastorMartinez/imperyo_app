# utils/restore_from_excel.py
import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def restore_data_from_excel(excel_path, collection_mapping):
    """
    Restaura datos desde un archivo Excel a Firestore.
    
    Args:
        excel_path: Ruta al archivo Excel.
        collection_mapping: Diccionario {'sheet_name': 'collection_name'}
    """
    try:
        # Inicializar Firestore si no está activo
        if not firebase_admin._apps:
            cred_dict = dict(st.secrets["firestore"])
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        db = firestore.client()

        xls = pd.ExcelFile(excel_path)
        
        for sheet_name, collection_name in collection_mapping.items():
            if sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                collection_ref = db.collection(collection_name)
                
                # Limpiar colección existente
                docs = collection_ref.stream()
                for doc in docs:
                    doc.reference.delete()
                
                # Subir nuevos documentos
                for _, row in df.iterrows():
                    doc_data = row.to_dict()
                    # Eliminar zona horaria de fechas
                    for key, value in doc_data.items():
                        if isinstance(value, pd.Timestamp):
                            doc_data[key] = value.tz_localize(None)
                    collection_ref.add(doc_data)
                
                st.success(f"✅ Colección '{collection_name}' restaurada desde hoja '{sheet_name}'.")
                logger.info(f"Colección '{collection_name}' restaurada con {len(df)} documentos.")
            else:
                st.warning(f"⚠️ Hoja '{sheet_name}' no encontrada en el Excel.")
        
        return True
    except Exception as e:
        st.error(f"❌ Error al restaurar datos: {e}")
        logger.error(f"Error al restaurar datos: {e}")
        return False