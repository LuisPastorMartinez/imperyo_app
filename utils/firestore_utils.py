# utils/firestore_utils.py
import sys
from pathlib import Path

# Ensure proper imports by adding parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

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
def initialize_firestore() -> Optional[firestore.client]:
    """Inicializa la conexión con Firestore de manera segura."""
    try:
        if not firebase_admin._apps:
            if 'firestore' not in st.secrets:
                raise ValueError("Firestore secrets no configurados")
                
            cred_dict = dict(st.secrets["firestore"])
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            
        return firestore.client()
    except Exception as e:
        logger.error(f"Error inicializando Firestore: {str(e)}")
        st.error("Error de conexión con Firestore. Ver logs para detalles.")
        return None

db = initialize_firestore()

def convert_to_firestore_types(value: Any) -> Any:
    """Convierte tipos de Python/pandas a tipos compatibles con Firestore."""
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
    elif isinstance(value, (np.bool_)):
        return bool(value)
    return value

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def load_dataframes_firestore() -> Optional[Dict[str, pd.DataFrame]]:
    """Carga todos los DataFrames desde Firestore con reintentos."""
    if db is None:
        return None

    data = {}
    try:
        for key, collection_name in COLLECTION_NAMES.items():
            docs = db.collection(collection_name).stream()
            records = [dict(doc.to_dict(), id_documento_firestore=doc.id) for doc in docs]
            
            df = pd.DataFrame(records) if records else create_empty_dataframe(collection_name)
            
            # Conversión especial para pedidos
            if key == 'pedidos':
                bool_cols = ['Inicio Trabajo', 'Cobrado', 'Retirado', 'Pendiente', 'Trabajo Terminado']
                date_cols = ['Fecha entrada', 'Fecha Salida']
                
                for col in bool_cols:
                    if col in df.columns:
                        df[col] = df[col].fillna(False).astype(bool)
                
                for col in date_cols:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
            
            data[f'df_{key}'] = df
            
        return data
    except Exception as e:
        logger.error(f"Error cargando datos de Firestore: {str(e)}")
        st.error("Error al cargar datos. Intente nuevamente.")
        return None

def save_dataframe_firestore(df: pd.DataFrame, collection_key: str) -> bool:
    """Guarda un DataFrame en Firestore usando operaciones por lotes."""
    if db is None:
        return False

    collection_name = COLLECTION_NAMES.get(collection_key)
    if not collection_name:
        logger.error(f"Colección {collection_key} no encontrada")
        return False

    try:
        # Convertir tipos y preparar datos
        df = df.copy()
        for col in df.columns:
            df[col] = df[col].apply(convert_to_firestore_types)

        batch = db.batch()
        col_ref = db.collection(collection_name)

        if collection_key == 'pedidos':
            # Actualización incremental para pedidos
            for _, row in df.iterrows():
                doc_data = row.drop('id_documento_firestore', errors='ignore').to_dict()
                doc_id = row.get('id_documento_firestore')
                
                if doc_id:
                    batch.update(col_ref.document(doc_id), doc_data)
                else:
                    new_doc = col_ref.document()
                    batch.set(new_doc, doc_data)
        else:
            # Sobrescritura completa para otras colecciones
            docs = list(col_ref.stream())
            for doc in docs:
                batch.delete(doc.reference)
                
            for _, row in df.iterrows():
                new_doc = col_ref.document()
                batch.set(new_doc, row.to_dict())

        batch.commit()
        return True
    except Exception as e:
        logger.error(f"Error guardando en Firestore ({collection_key}): {str(e)}")
        st.error(f"Error al guardar {collection_key}. Ver logs.")
        return False

def delete_document_firestore(collection_key: str, doc_id: str) -> bool:
    """Elimina un documento específico de Firestore."""
    if db is None:
        return False

    collection_name = COLLECTION_NAMES.get(collection_key)
    if not collection_name:
        return False

    try:
        db.collection(collection_name).document(doc_id).delete()
        return True
    except Exception as e:
        logger.error(f"Error eliminando documento: {str(e)}")
        return False

def create_empty_dataframe(collection_name: str) -> pd.DataFrame:
    """Crea DataFrames vacíos con estructura predefinida."""
    schemas = {
        'pedidos': [
            'ID', 'Producto', 'Cliente', 'Telefono', 'Club', 'Talla', 'Tela',
            'Breve Descripción', 'Fecha entrada', 'Fecha Salida', 'Precio',
            'Precio Factura', 'Tipo de pago', 'Adelanto', 'Observaciones',
            'Inicio Trabajo', 'Cobrado', 'Retirado', 'Pendiente', 'Trabajo Terminado',
            'id_documento_firestore'
        ],
        'gastos': [
            'ID', 'Fecha', 'Concepto', 'Importe', 'Tipo', 'id_documento_firestore'
        ],
        'listas': [
            'Producto', 'Talla', 'Tela', 'Tipo de pago'
        ],
        'trabajos': [
            'ID', 'Descripcion', 'Estado'
        ],
        'totales': [
            'Mes', 'Total_Pedidos', 'Total_Gastos', 'Balance'
        ]
    }
    return pd.DataFrame(columns=schemas.get(collection_name, []))