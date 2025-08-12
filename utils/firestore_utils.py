import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, date
import numpy as np
import json
import os

# Configuración de colecciones
COLLECTION_NAMES = {
    'pedidos': 'pedidos',
    'gastos': 'gastos',
    'totales': 'totales',
    'listas': 'listas',
    'trabajos': 'trabajos'
}

@st.cache_resource
def initialize_firestore():
    """Inicializa la conexión con Firestore."""
    try:
        if not firebase_admin._apps:
            try:
                firebase_config = st.secrets["firestore"]
                if isinstance(firebase_config, str):
                    firebase_config = json.loads(firebase_config)
                creds = credentials.Certificate(firebase_config)
            except (KeyError, FileNotFoundError):
                if "FIREBASE_SERVICE_ACCOUNT" in os.environ:
                    firebase_config_str = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
                    firebase_config = json.loads(firebase_config_str)
                    creds = credentials.Certificate(firebase_config)
                else:
                    creds = credentials.Certificate("firebase_credentials.json") 
            
            firebase_admin.initialize_app(creds)
        
        return firestore.client()
    except Exception as e:
        st.error(f"Error inicializando Firestore: {str(e)}")
        return None

db = initialize_firestore()

def load_dataframes_firestore():
    """Carga todos los DataFrames desde Firestore."""
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
                
                for col in df.columns:
                    # Intenta convertir la columna a tipo datetime, ignorando errores
                    converted_series = pd.to_datetime(df[col], errors='coerce')
                    
                    # Verifica si la conversión fue exitosa antes de usar .dt
                    if pd.api.types.is_datetime64_any_dtype(converted_series):
                         df[col] = converted_series.dt.date
                    
                    # Rellena NaN en columnas booleanas y convierte a bool
                    if col in ['Inicio Trabajo', 'Cobrado', 'Retirado', 'Pendiente', 'Trabajo Terminado']:
                        df[col] = df[col].fillna(False).astype(bool)
                
                # Asegura que la columna ID sea de tipo entero
                if 'ID' in df.columns:
                    df['ID'] = pd.to_numeric(df['ID'], errors='coerce').fillna(0).astype(int)
            else:
                df = create_empty_dataframe(collection_name)
            
            data[f'df_{key}'] = df
        
        return data
    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
        st.exception(e)
        return None

def save_dataframe_firestore(df: pd.DataFrame, collection_key: str) -> bool:
    """Guarda un DataFrame en Firestore de forma segura."""
    if db is None:
        st.error("No hay conexión a Firestore")
        return False

    collection_name = COLLECTION_NAMES.get(collection_key)
    if not collection_name:
        st.error(f"Colección {collection_key} no encontrada")
        return False

    try:
        batch = db.batch()
        collection_ref = db.collection(collection_name)
        
        for _, row in df.iterrows():
            record = row.to_dict()
            
            clean_record = {}
            for k, v in record.items():
                if pd.isna(v) or v is None or v == '':
                    clean_record[k] = None
                elif isinstance(v, date) and not isinstance(v, datetime):
                    clean_record[k] = datetime(v.year, v.month, v.day)
                elif isinstance(v, pd.Timestamp):
                    clean_record[k] = v.to_pydatetime()
                elif isinstance(v, np.integer):
                    clean_record[k] = int(v)
                elif isinstance(v, np.floating):
                    clean_record[k] = float(v)
                else:
                    clean_record[k] = v

            doc_id = clean_record.pop('id_documento_firestore', None)
            
            if doc_id:
                doc_ref = collection_ref.document(str(doc_id))
                batch.set(doc_ref, clean_record, merge=True)
            else:
                new_doc_ref = collection_ref.document()
                batch.set(new_doc_ref, clean_record)
        
        batch.commit()
        return True
    except Exception as e:
        st.error(f"Error guardando en Firestore: {str(e)}")
        st.exception(e)
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
        st.error(f"Error eliminando documento: {str(e)}")
        return False

def create_empty_dataframe(collection_name):
    """Crea DataFrames vacíos con la estructura correcta."""
    if collection_name == 'pedidos':
        return pd.DataFrame(columns=[
            'ID', 'Producto', 'Cliente', 'Telefono', 'Club', 'Talla', 'Tela',
            'Breve Descripción', 'Fecha entrada', 'Fecha Salida', 'Precio',
            'Precio Factura', 'Tipo de pago', 'Adelanto', 'Observaciones',
            'Inicio Trabajo', 'Cobrado', 'Retirado', 'Pendiente', 'Trabajo Terminado',
            'id_documento_firestore'
        ])
    elif collection_name == 'gastos':
        return pd.DataFrame(columns=[
            'ID', 'Fecha', 'Concepto', 'Importe', 'Tipo', 'id_documento_firestore'
        ])
    elif collection_name == 'listas':
        return pd.DataFrame(columns=[
            'Producto', 'Talla', 'Tela', 'Tipo de pago'
        ])
    return pd.DataFrame()

def get_next_id(df: pd.DataFrame, id_column_name: str) -> int:
    """Obtiene el próximo ID disponible de manera segura."""
    if df.empty or id_column_name not in df.columns:
        return 1
    
    try:
        numeric_ids = pd.to_numeric(df[id_column_name], errors='coerce')
        df_clean = numeric_ids.dropna()
        
        if df_clean.empty:
            return 1
        return int(df_clean.max()) + 1
    except Exception:
        st.warning("Error al calcular el próximo ID. Usando 1 como valor por defecto.")
        return 1