import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import logging

# Importar función compartida
from utils.helpers import convert_to_firestore_type

# Configuración de colecciones (SOLO LAS ORIGINALES)
COLLECTION_NAMES = {
    'pedidos': 'pedidos',
    'gastos': 'gastos',
    'totales': 'totales', 
    'listas': 'listas',
    'trabajos': 'trabajos'
}

logger = logging.getLogger(__name__)

def get_firestore_client():
    """Obtiene el cliente de Firestore, inicializándolo si es necesario."""
    if 'firestore_client' not in st.session_state:
        try:
            if "firestore" not in st.secrets:
                st.error("Error: No se encontraron credenciales de Firestore en secrets.")
                return None

            # 🔥 Versión segura: asume que st.secrets["firestore"] YA ES UN DICCIONARIO
            # (así funciona en Streamlit Cloud)
            creds_dict = dict(st.secrets["firestore"])
            
            if not firebase_admin._apps:
                cred = credentials.Certificate(creds_dict)
                firebase_admin.initialize_app(cred)
            
            st.session_state.firestore_client = firestore.client()
        except Exception as e:
            st.error(f"Error inicializando Firestore: {e}")
            logger.error(f"Error inicializando Firestore: {e}")
            return None
    return st.session_state.firestore_client

db = get_firestore_client()

def _sanitize_dataframe_for_firestore(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica conversión celda a celda usando la función compartida."""
    if df is None or df.empty:
        return df
    df = df.copy()
    for col in df.columns:
        df[col] = df[col].apply(convert_to_firestore_type)
    df = df.where(pd.notna(df), None)
    return df

def load_dataframes_firestore():
    """Carga todos los DataFrames desde Firestore"""
    if db is None:
        return None

    data = {}
    try:
        for key, collection_name in COLLECTION_NAMES.items():
            docs = db.collection(collection_name).stream()
            records = []
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data['id_documento_firestore'] = doc.id
                records.append(doc_data)

            if records:
                df = pd.DataFrame(records)

                if key == 'pedidos':
                    # Booleanos
                    for col in ['Inicio Trabajo', 'Cobrado', 'Retirado', 'Pendiente', 'Trabajo Terminado']:
                        if col in df.columns:
                            def safe_bool(x):
                                if isinstance(x, bool):
                                    return x
                                if isinstance(x, str):
                                    return x.lower() in ('true', '1', 'yes', 'si')
                                if isinstance(x, (int, float)):
                                    return bool(x)
                                return False
                            df[col] = df[col].apply(safe_bool).fillna(False).astype(bool)

                    # Fechas
                    for col in ['Fecha entrada', 'Fecha Salida']:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col], errors='coerce')

                    # Números
                    for col in ['ID', 'Precio', 'Precio Factura', 'Adelanto']:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                            if col == 'ID':
                                df[col] = df[col].astype('int64')
                            else:
                                df[col] = df[col].astype('float64')

                    # Textos
                    for col in ['Producto', 'Cliente', 'Telefono', 'Club', 'Talla', 'Tela', 
                                'Breve Descripción', 'Tipo de pago', 'Observaciones', 'Año']:
                        if col in df.columns:
                            df[col] = df[col].fillna('').astype(str)
            else:
                df = create_empty_dataframe(collection_name)

            data[f'df_{key}'] = df

        return data
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        logger.error(f"Error cargando datos: {e}")
        return None

def save_dataframe_firestore(df: pd.DataFrame, collection_key: str) -> bool:
    """Guarda un DataFrame en Firestore usando batch para mayor eficiencia."""
    if db is None:
        return False

    collection_name = COLLECTION_NAMES.get(collection_key)
    if not collection_name:
        return False

    try:
        df = _sanitize_dataframe_for_firestore(df)

        batch = db.batch()
        collection_ref = db.collection(collection_name)

        # Si no es pedidos, borrar todo y reescribir (como antes)
        if collection_key != 'pedidos':
            docs = collection_ref.stream()
            for doc in docs:
                batch.delete(doc.reference)

        # Guardar cada fila
        for _, row in df.iterrows():
            record = row.drop('id_documento_firestore', errors='ignore').to_dict()

            # Limpieza final por si acaso
            for k, v in list(record.items()):
                if v is pd.NaT:
                    record[k] = None
                elif isinstance(v, pd.Timestamp):
                    record[k] = v.to_pydatetime()

            doc_id = row.get('id_documento_firestore')
            if doc_id:
                doc_ref = collection_ref.document(doc_id)
            else:
                doc_ref = collection_ref.document()

            batch.set(doc_ref, record)

        batch.commit()
        return True

    except Exception as e:
        st.error(f"Error guardando en Firestore: {e}")
        logger.error(f"Error guardando en Firestore: {e}")
        return False

def delete_document_firestore(collection_key, doc_id):
    """Elimina un documento específico"""
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
        logger.error(f"Error eliminando documento: {e}")
        return False

def create_empty_dataframe(collection_name):
    """Crea DataFrames vacíos con la estructura correcta"""
    if collection_name == 'pedidos':
        return pd.DataFrame(columns=[
            'ID', 'Producto', 'Cliente', 'Telefono', 'Club', 'Talla', 'Tela',
            'Breve Descripción', 'Fecha entrada', 'Fecha Salida', 'Precio',
            'Precio Factura', 'Tipo de pago', 'Adelanto', 'Observaciones',
            'Inicio Trabajo', 'Cobrado', 'Retirado', 'Pendiente', 'Trabajo Terminado',
            'Año',  # ✅ ¡AÑADIDO!
            'id_documento_firestore'
        ])
    elif collection_name == 'gastos':
        return pd.DataFrame(columns=['ID', 'Fecha', 'Concepto', 'Importe', 'Tipo', 'id_documento_firestore'])
    return pd.DataFrame()

def get_next_id(df, id_column_name):
    """Obtiene el próximo ID disponible"""
    if df.empty or id_column_name not in df.columns:
        return 1
    df[id_column_name] = pd.to_numeric(df[id_column_name], errors='coerce')
    df_clean = df.dropna(subset=[id_column_name])
    return 1 if df_clean.empty else int(df_clean[id_column_name].max()) + 1