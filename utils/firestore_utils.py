# utils/firestore_utils.py
import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, date
import numpy as np

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
    """Inicializa la conexión con Firestore de manera segura"""
    try:
        if not firebase_admin._apps:
            # Cargar credenciales desde secrets
            firebase_config = {
                "type": st.secrets["firestore"]["type"],
                "project_id": st.secrets["firestore"]["project_id"],
                "private_key_id": st.secrets["firestore"]["private_key_id"],
                "private_key": st.secrets["firestore"]["private_key"].replace('\\n', '\n'),
                "client_email": st.secrets["firestore"]["client_email"],
                "client_id": st.secrets["firestore"]["client_id"],
                "auth_uri": st.secrets["firestore"]["auth_uri"],
                "token_uri": st.secrets["firestore"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["firestore"]["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["firestore"]["client_x509_cert_url"],
                "universe_domain": st.secrets["firestore"]["universe_domain"]
            }
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Error inicializando Firestore: {str(e)}")
        return None

db = initialize_firestore()

def convert_to_firestore_types(value):
    """
    Convierte tipos de Python a tipos compatibles con Firestore
    Versión robusta que maneja todos los casos posibles
    """
    if value is None or pd.isna(value):
        return None
    
    # Manejo de tipos de fecha y hora
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    
    # Manejo de tipos numéricos
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value)
    
    # Manejo de booleanos
    if isinstance(value, bool):
        return bool(value)
    
    # Para cualquier otro tipo, convertimos a string
    try:
        return str(value)
    except Exception:
        return None

def load_dataframes_firestore():
    """Carga todos los DataFrames desde Firestore con manejo de tipos seguro"""
    if db is None:
        st.error("No se pudo conectar a Firestore")
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
                
                # Conversión específica para pedidos
                if key == 'pedidos':
                    # Convertir booleanos
                    bool_cols = ['Inicio Trabajo', 'Cobrado', 'Retirado', 'Pendiente', 'Trabajo Terminado']
                    for col in bool_cols:
                        if col in df.columns:
                            df[col] = df[col].fillna(False).astype(bool)
                    
                    # Convertir fechas
                    date_cols = ['Fecha entrada', 'Fecha Salida']
                    for col in date_cols:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col]).dt.date
            else:
                df = create_empty_dataframe(collection_name)
            
            data[f'df_{key}'] = df
        
        return data
    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
        return None

def save_dataframe_firestore(df, collection_key):
    """Guarda un DataFrame en Firestore con conversión segura de tipos"""
    if db is None:
        st.error("No hay conexión a Firestore")
        return False

    collection_name = COLLECTION_NAMES.get(collection_key)
    if not collection_name:
        st.error(f"Colección {collection_key} no encontrada")
        return False

    try:
        # Crear copia para no modificar el original
        df_to_save = df.copy()
        
        # Aplicar conversión de tipos a todas las columnas
        for col in df_to_save.columns:
            df_to_save[col] = df_to_save[col].apply(convert_to_firestore_types)

        if collection_key == 'pedidos':
            # Para pedidos, manejamos documentos individualmente
            batch = db.batch()
            for _, row in df_to_save.iterrows():
                record = row.to_dict()
                doc_id = record.pop('id_documento_firestore', None)
                
                if doc_id:
                    doc_ref = db.collection(collection_name).document(doc_id)
                else:
                    doc_ref = db.collection(collection_name).document()
                
                batch.set(doc_ref, record)
            
            batch.commit()
        else:
            # Para otras colecciones, borramos y recreamos
            batch = db.batch()
            
            # Eliminar documentos existentes
            docs = db.collection(collection_name).stream()
            for doc in docs:
                batch.delete(doc.reference)
            
            # Añadir nuevos documentos
            for _, row in df_to_save.iterrows():
                record = row.to_dict()
                new_doc = db.collection(collection_name).document()
                batch.set(new_doc, record)
            
            batch.commit()
        
        return True
    except Exception as e:
        st.error(f"Error guardando en Firestore: {str(e)}")
        return False

def delete_document_firestore(collection_key, doc_id):
    """Elimina un documento específico de Firestore"""
    if db is None:
        st.error("No hay conexión a Firestore")
        return False

    collection_name = COLLECTION_NAMES.get(collection_key)
    if not collection_name:
        st.error(f"Colección {collection_key} no encontrada")
        return False

    try:
        db.collection(collection_name).document(doc_id).delete()
        return True
    except Exception as e:
        st.error(f"Error eliminando documento: {str(e)}")
        return False

def create_empty_dataframe(collection_name):
    """Crea DataFrames vacíos con la estructura correcta"""
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
    return pd.DataFrame()

def get_next_id(df, id_column_name):
    """Obtiene el próximo ID disponible de manera segura"""
    if df.empty or id_column_name not in df.columns:
        return 1
    
    try:
        # Convertir a numérico y limpiar valores no válidos
        df[id_column_name] = pd.to_numeric(df[id_column_name], errors='coerce')
        df_clean = df.dropna(subset=[id_column_name])
        
        if df_clean.empty:
            return 1
        return int(df_clean[id_column_name].max()) + 1
    except Exception:
        return 1