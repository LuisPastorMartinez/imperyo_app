
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
    """Inicializa la conexión con Firestore"""
    try:
        if not firebase_admin._apps:
            cred_dict = dict(st.secrets["firestore"])  # requiere st.secrets configurado
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Error inicializando Firestore: {e}")
        return None

db = initialize_firestore()

def convert_to_firestore_types(value):
    """Convierte tipos de Python a tipos compatibles con Firestore (sin NaT)."""
    # 1) Vacíos / NaN / NaT / None / ""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    if isinstance(value, str) and value.strip() in ("", "NaT", "nan", "None"):
        return None
    if value is pd.NaT:
        return None

    # 2) pandas.Timestamp
    if isinstance(value, pd.Timestamp):
        # proteger doble por si acaso
        if pd.isna(value) or value is pd.NaT:
            return None
        try:
            return value.to_pydatetime()
        except Exception:
            return None

    # 3) datetime.date (de st.date_input)
    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime.combine(value, datetime.min.time())

    # 4) datetime.datetime
    if isinstance(value, datetime):
        return value  # naive OK

    # 5) NumPy numéricos
    if isinstance(value, (np.integer, )):
        return int(value)
    if isinstance(value, (np.floating, )):
        # Si es NaN, ya habría salido arriba con pd.isna
        return float(value)

    # 6) Tipos básicos
    if isinstance(value, (int, float, bool, str)):
        return value

    # 7) Fallback: string
    return str(value)

def _sanitize_dataframe_for_firestore(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica conversión celda a celda y elimina cualquier NaT remanente."""
    if df is None or df.empty:
        return df
    # Aplicación celda a celda
    df = df.copy()
    for col in df.columns:
        df[col] = df[col].apply(convert_to_firestore_types)
    # Reemplazo final de NaT/NaN por None por si algo se coló
    df = df.where(pd.notna(df), None)
    # Doble pasada por tipos especiales que puedan haber quedado en object
    for col in df.columns:
        df[col] = df[col].apply(lambda x: None if x is pd.NaT else x)
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
                    # Bools
                    for col in ['Inicio Trabajo', 'Cobrado', 'Retirado', 'Pendiente', 'Trabajo Terminado']:
                        if col in df.columns:
                            df[col] = df[col].fillna(False).astype(bool)

                    # Fechas -> string para visualización estable en Streamlit
                    for col in ['Fecha entrada', 'Fecha Salida']:
                        if col in df.columns:
                            def _fmt(x):
                                if pd.isna(x) or x is None or x is pd.NaT:
                                    return ''
                                if hasattr(x, 'strftime'):
                                    try:
                                        return x.strftime('%Y-%m-%d')
                                    except Exception:
                                        pass
                                s = str(x)
                                return s[:10] if s and s != 'NaT' else ''
                            df[col] = df[col].apply(_fmt)

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
                                'Breve Descripción', 'Tipo de pago', 'Observaciones']:
                        if col in df.columns:
                            df[col] = df[col].fillna('').astype(str)
            else:
                df = create_empty_dataframe(collection_name)

            data[f'df_{key}'] = df
        return data
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return None

def save_dataframe_firestore(df: pd.DataFrame, collection_key: str) -> bool:
    """Guarda un DataFrame en Firestore con conversión de tipos y limpieza anti-NaT."""
    if db is None:
        return False

    collection_name = COLLECTION_NAMES.get(collection_key)
    if not collection_name:
        return False

    try:
        # Limpieza y conversión robusta
        df = _sanitize_dataframe_for_firestore(df)

        # Última comprobación por si acaso (diagnóstico)
        def _has_nat(obj):
            return obj is pd.NaT or (isinstance(obj, pd.Timestamp) and (pd.isna(obj) or obj is pd.NaT))

        if df.applymap(_has_nat).any().any():
            # Reemplazar cualquier NaT rezagado
            df = df.applymap(lambda x: None if _has_nat(x) else x)

        if collection_key == 'pedidos':
            for _, row in df.iterrows():
                record = row.drop('id_documento_firestore', errors='ignore').to_dict()

                # Limpieza final del dict (defensiva)
                for k, v in list(record.items()):
                    if v is pd.NaT:
                        record[k] = None
                    elif isinstance(v, pd.Timestamp):
                        record[k] = v.to_pydatetime()

                doc_id = row.get('id_documento_firestore')
                if doc_id:
                    db.collection(collection_name).document(doc_id).set(record)
                else:
                    db.collection(collection_name).add(record)
        else:
            batch = db.batch()
            docs = db.collection(collection_name).stream()
            for doc in docs:
                batch.delete(doc.reference)
            for _, row in df.iterrows():
                record = row.to_dict()
                # Limpieza final por si acaso
                for k, v in list(record.items()):
                    if v is pd.NaT:
                        record[k] = None
                    elif isinstance(v, pd.Timestamp):
                        record[k] = v.to_pydatetime()
                new_doc = db.collection(collection_name).document()
                batch.set(new_doc, record)
            batch.commit()

        return True
    except Exception as e:
        st.error(f"Error guardando en Firestore: {e}")
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
        return pd.DataFrame(columns=['ID', 'Fecha', 'Concepto', 'Importe', 'Tipo', 'id_documento_firestore'])
    return pd.DataFrame()

def get_next_id(df, id_column_name):
    """Obtiene el próximo ID disponible"""
    if df.empty or id_column_name not in df.columns:
        return 1
    df[id_column_name] = pd.to_numeric(df[id_column_name], errors='coerce')
    df_clean = df.dropna(subset=[id_column_name])
    return 1 if df_clean.empty else int(df_clean[id_column_name].max()) + 1
