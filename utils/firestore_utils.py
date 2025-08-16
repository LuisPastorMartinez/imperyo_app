# utils/firestore_utils.py
import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
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
    """Inicializa la conexión con Firestore"""
    try:
        if not firebase_admin._apps:
            cred_dict = dict(st.secrets["firestore"])
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Error inicializando Firestore: {e}")
        return None

db = initialize_firestore()

def load_dataframes_firestore():
    """Carga todos los DataFrames desde Firestore"""
    if db is None:
        st.error("No hay conexión a Firestore")
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
                
                # Conversión de tipos específicos para pedidos
                if key == 'pedidos':
                    # Columnas booleanas
                    bool_cols = ['Inicio Trabajo', 'Trabajo Terminado', 'Cobrado', 'Retirado', 'Pendiente']
                    for col in bool_cols:
                        if col in df.columns:
                            df[col] = df[col].astype(bool)
                    
                    # Columnas de fecha
                    date_cols = ['Fecha entrada', 'Fecha Salida']
                    for col in date_cols:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col]).dt.date
            else:
                df = create_empty_dataframe(collection_name)
            
            data[f'df_{key}'] = df
        
        return data
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return None

def save_dataframe_firestore(df, collection_key):
    """Guarda un DataFrame en Firestore (versión optimizada)"""
    if db is None:
        st.error("No hay conexión a Firestore")
        return False

    collection_name = COLLECTION_NAMES.get(collection_key)
    if not collection_name:
        st.error(f"Colección {collection_key} no configurada")
        return False

    try:
        batch = db.batch()
        
        if collection_key == 'pedidos':
            # Verificar columnas requeridas
            required_cols = ['ID', 'Cliente', 'Producto', 'Fecha entrada']
            if not all(col in df.columns for col in required_cols):
                st.error(f"Faltan columnas requeridas: {required_cols}")
                return False

            # Actualizar documentos existentes o crear nuevos
            for _, row in df.iterrows():
                record = row.to_dict()
                doc_id = record.pop('id_documento_firestore', None)
                
                if doc_id:
                    doc_ref = db.collection(collection_name).document(doc_id)
                else:
                    doc_ref = db.collection(collection_name).document()
                
                batch.set(doc_ref, record)
        else:
            # Para otras colecciones (limpiar y recrear)
            # Primero eliminar todos los documentos existentes
            for doc in db.collection(collection_name).stream():
                batch.delete(doc.reference)
            
            # Luego agregar los nuevos documentos
            for _, row in df.iterrows():
                doc_ref = db.collection(collection_name).document()
                batch.set(doc_ref, row.to_dict())
        
        # Ejecutar todas las operaciones en lote
        batch.commit()
        return True
        
    except Exception as e:
        st.error(f"Error guardando en Firestore: {e}")
        return False

def delete_document_firestore(collection_key, doc_id):
    """Elimina un documento específico de Firestore"""
    if db is None:
        st.error("No hay conexión a Firestore")
        return False

    collection_name = COLLECTION_NAMES.get(collection_key)
    if not collection_name or not doc_id:
        return False

    try:
        db.collection(collection_name).document(doc_id).delete()
        return True
    except Exception as e:
        st.error(f"Error eliminando documento: {e}")
        return False

def create_empty_dataframe(collection_name):
    """Crea DataFrames vacíos con estructura consistente"""
    if collection_name == 'pedidos':
        return pd.DataFrame(columns=[
            'ID', 'Producto', 'Cliente', 'Telefono', 'Club', 'Talla', 'Tela',
            'Breve Descripción', 'Fecha entrada', 'Fecha Salida', 'Precio',
            'Precio Factura', 'Tipo de pago', 'Adelanto', 'Observaciones',
            'Inicio Trabajo', 'Trabajo Terminado', 'Cobrado', 'Retirado', 'Pendiente',
            'id_documento_firestore'
        ])
    elif collection_name == 'gastos':
        return pd.DataFrame(columns=[
            'ID', 'Fecha', 'Concepto', 'Importe', 'Tipo', 'id_documento_firestore'
        ])
    else:
        return pd.DataFrame()

def get_next_id(df, id_column_name):
    """Obtiene el próximo ID disponible"""
    if df.empty or id_column_name not in df.columns:
        return 1
    
    df[id_column_name] = pd.to_numeric(df[id_column_name], errors='coerce')
    df_clean = df.dropna(subset=[id_column_name])
    
    return 1 if df_clean.empty else int(df_clean[id_column_name].max()) + 1