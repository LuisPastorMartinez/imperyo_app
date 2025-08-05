import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Configuración de colecciones
COLLECTION_CONFIG = {
    'pedidos': {
        'required_columns': [
            'ID', 'Cliente', 'Producto', 'Fecha Entrada', 'Precio',
            'Inicio Trabajo', 'Trabajo Terminado', 'Pendiente'
        ],
        'optional_columns': [
            'Teléfono', 'Club', 'Talla', 'Tela', 'Breve Descripción',
            'Fecha Salida', 'Precio Factura', 'Tipo de pago', 'Adelanto',
            'Observaciones', 'Cobrado', 'Retirado'
        ]
    },
    'gastos': {
        'required_columns': ['ID', 'Concepto', 'Monto', 'Fecha'],
        'optional_columns': ['Tipo', 'Comentarios']
    }
}

@st.cache_resource
def initialize_firestore():
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(dict(st.secrets["firestore"]))
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Error inicializando Firestore: {str(e)}")
        st.stop()

db = initialize_firestore()

def load_dataframes_firestore():
    """Carga datos eliminando columnas duplicadas pero manteniendo vacías"""
    if not db: 
        return None
    
    data = {}
    for col_name, config in COLLECTION_CONFIG.items():
        try:
            docs = db.collection(col_name).stream()
            records = []
            
            for doc in docs:
                doc_data = doc.to_dict()
                # Eliminar duplicados dentro de cada documento
                unique_data = {}
                for k, v in doc_data.items():
                    if k not in unique_data:  # Conserva solo la primera aparición
                        unique_data[k] = v
                unique_data['id_documento_firestore'] = doc.id
                records.append(unique_data)
            
            # Crear DataFrame manteniendo todas las columnas
            df = pd.DataFrame(records)
            
            # Eliminar columnas duplicadas a nivel de DataFrame
            df = df.loc[:, ~df.columns.duplicated()]
            
            # Asegurar columnas requeridas
            for col in config['required_columns']:
                if col not in df.columns:
                    df[col] = None
            
            # Conversión de tipos
            if col_name == 'pedidos':
                bool_cols = ['Inicio Trabajo', 'Trabajo Terminado', 'Cobrado', 'Retirado', 'Pendiente']
                for col in bool_cols:
                    if col in df.columns:
                        df[col] = df[col].fillna(False).astype(bool)
                
                date_cols = ['Fecha Entrada', 'Fecha Salida']
                for col in date_cols:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
            
            data[f'df_{col_name}'] = df
            
        except Exception as e:
            st.error(f"Error cargando {col_name}: {str(e)}")
            # Crear DataFrame vacío con estructura completa
            all_columns = config['required_columns'] + config['optional_columns'] + ['id_documento_firestore']
            data[f'df_{col_name}'] = pd.DataFrame(columns=all_columns)
    
    return data

def save_dataframe_firestore(df, collection_key):
    """Guarda datos eliminando duplicados antes de enviar"""
    if not db or collection_key not in COLLECTION_CONFIG:
        return False
    
    try:
        batch = db.batch()
        col_ref = db.collection(collection_key)
        
        # Limpiar colección existente
        for doc in col_ref.list_documents():
            batch.delete(doc)
        
        # Procesar y guardar cada fila
        for _, row in df.iterrows():
            # Eliminar valores nulos y duplicados
            doc_data = {}
            for k, v in row.items():
                if pd.notna(v) and k != 'id_documento_firestore':
                    if k not in doc_data:  # Conservar solo primera aparición
                        doc_data[k] = v
            
            # Conversión de tipos para Firestore
            if collection_key == 'pedidos':
                for col in ['Fecha Entrada', 'Fecha Salida']:
                    if col in doc_data and pd.notna(doc_data[col]):
                        doc_data[col] = datetime.combine(doc_data[col], datetime.min.time())
            
            new_doc = col_ref.document()
            batch.set(new_doc, doc_data)
        
        batch.commit()
        return True
        
    except Exception as e:
        st.error(f"Error guardando {collection_key}: {str(e)}")
        return False

def get_next_id(df, id_column='ID'):
    """Genera nuevo ID numérico secuencial"""
    if df.empty or id_column not in df.columns:
        return 1
    
    try:
        # Convertir a numérico y manejar posibles errores
        df[id_column] = pd.to_numeric(df[id_column], errors='coerce')
        max_id = df[id_column].max()
        return int(max_id + 1) if pd.notna(max_id) else 1
    except Exception:
        return 1