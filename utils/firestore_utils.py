import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import numpy as np
from datetime import datetime, date
import os
import json
import streamlit as st

# Cargar las credenciales de Firebase de forma segura
# Preferiblemente desde Streamlit secrets o una variable de entorno
# Si usas Streamlit Cloud, configura tus secretos: https://docs.streamlit.io/deploy/streamlit-cloud/secrets-management
# Si usas localmente, puedes usar un archivo .json y os.environ, o hardcodear para pruebas (NO RECOMENDADO PARA PROD)

# Intenta cargar las credenciales desde secrets de Streamlit
# Si no, intenta desde una variable de entorno (para entornos como Docker/otros despliegues)
# Fallback a un archivo local (solo para desarrollo y si tienes el JSON en el mismo directorio, NO PARA PRODUCCIÓN)

try:
    # Intenta cargar desde st.secrets si estás en Streamlit Cloud
    firebase_config = {
        "type": st.secrets["type"],
        "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"].replace('\\n', '\n'),
        "client_email": st.secrets["client_email"],
        "client_id": st.secrets["client_id"],
        "auth_uri": st.secrets["auth_uri"],
        "token_uri": st.secrets["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["client_x509_cert_url"],
        "universe_domain": st.secrets["universe_domain"]
    }
    creds = credentials.Certificate(firebase_config)
    
except Exception as e:
    # Si falla, intenta cargar desde una variable de entorno
    try:
        if "FIREBASE_SERVICE_ACCOUNT" in os.environ:
            firebase_config_str = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
            firebase_config = json.loads(firebase_config_str)
            creds = credentials.Certificate(firebase_config)
        else:
            # Fallback a un archivo local si no hay variable de entorno (solo para desarrollo)
            # Asegúrate de que tu archivo de credenciales esté en la raíz del proyecto o especifica la ruta
            creds = credentials.Certificate("firebase_credentials.json") 
    except Exception as e_env:
        st.error(f"Error al cargar credenciales de Firebase: {e_env}")
        st.stop() # Detener la aplicación si no se pueden cargar las credenciales

# Inicializar Firebase Admin SDK si no ha sido inicializado
if not firebase_admin._apps:
    try:
        firebase_admin.initialize_app(creds)
        db = firestore.client()
        st.success("Conexión a Firebase Firestore exitosa!")
    except Exception as e:
        st.error(f"Error al inicializar Firebase Admin SDK: {e}")
        st.stop() # Detener la aplicación si la inicialización falla
else:
    db = firestore.client()

def save_dataframe_firestore(df: pd.DataFrame, collection_name: str) -> bool:
    """
    Guarda un DataFrame de Pandas en una colección de Firestore.
    Actualiza documentos existentes o añade nuevos.
    Asegura que 'id_documento_firestore' sea la clave del documento en Firestore.
    
    Args:
        df (pd.DataFrame): El DataFrame de Pandas a guardar.
        collection_name (str): El nombre de la colección en Firestore.

    Returns:
        bool: True si el guardado fue exitoso, False en caso contrario.
    """
    if df.empty:
        st.info(f"El DataFrame para la colección '{collection_name}' está vacío. No hay datos para guardar.")
        return True # Considerar un DataFrame vacío como un guardado "exitoso" si no hay nada que hacer

    try:
        # Usar un batch para operaciones más eficientes y atómicas
        batch = db.batch()
        collection_ref = db.collection(collection_name)
        
        # Iterar a través de cada fila del DataFrame
        for index, row in df.iterrows():
            doc_data = row.to_dict()
            
            # Limpiar datos: Convertir NaN/NaT a None, y asegurar que las fechas sean objetos datetime.date/datetime
            for key, value in doc_data.items():
                if pd.isna(value): # Maneja np.nan, pd.NA, pd.NaT
                    doc_data[key] = None
                elif isinstance(value, datetime):
                    # Firestore puede manejar objetos datetime directamente
                    pass
                elif isinstance(value, date):
                    # Convertir date a datetime si se prefiere para consistencia en Firestore
                    doc_data[key] = datetime(value.year, value.month, value.day)
                elif isinstance(value, np.int64):
                    doc_data[key] = int(value)
                elif isinstance(value, np.float64):
                    doc_data[key] = float(value)

            # Obtener el ID del documento de Firestore, si existe
            firestore_doc_id = doc_data.get('id_documento_firestore')

            if firestore_doc_id:
                # Si ya tiene un ID de Firestore, actualizar el documento existente
                doc_ref = collection_ref.document(firestore_doc_id)
                batch.set(doc_ref, doc_data, merge=True) # merge=True para actualizar solo los campos proporcionados
            else:
                # Si es un nuevo documento, añadirlo a la colección y obtener su ID
                # No podemos obtener el ID real de Firestore en el batch, lo haremos después
                # o dejaremos que Firestore genere uno y lo recuperaremos al cargar.
                # Por ahora, simplemente lo añadimos. Streamlit lo re-cargará para obtener el ID.
                # Esto es un caso de uso donde save_dataframe_firestore es un poco tricky
                # Si el ID es None, Firestore generará uno.
                new_doc_ref = collection_ref.document() # Firestore genera un ID
                batch.set(new_doc_ref, doc_data)
                # OJO: Aquí no podemos actualizar el df original con new_doc_ref.id directamente
                # porque estamos en un batch. Esto se manejará al recargar el DF.
        
        batch.commit()
        st.success(f"DataFrame guardado/actualizado en la colección '{collection_name}' en Firestore.")
        return True
    except Exception as e:
        st.error(f"Error guardando en Firestore: {e}")
        st.exception(e) # Para mostrar el traceback completo en Streamlit
        return False

def fetch_data_from_firestore(collection_name: str) -> pd.DataFrame:
    """
    Recupera todos los documentos de una colección de Firestore y los convierte en un DataFrame de Pandas.
    Añade una columna 'id_documento_firestore' con el ID del documento de Firestore.

    Args:
        collection_name (str): El nombre de la colección en Firestore.

    Returns:
        pd.DataFrame: Un DataFrame de Pandas con los datos de la colección.
    """
    try:
        docs = db.collection(collection_name).stream()
        data = []
        for doc in docs:
            doc_dict = doc.to_dict()
            doc_dict['id_documento_firestore'] = doc.id  # Guardar el ID real del documento de Firestore
            
            # Convertir objetos Timestamp de Firestore a datetime de Python
            for key, value in doc_dict.items():
                if isinstance(value, firestore.SERVER_TIMESTAMP):
                    doc_dict[key] = value.date() # o .datetime() si necesitas la hora
                elif isinstance(value, firestore.Timestamp):
                    doc_dict[key] = value.date() # o .datetime()
            data.append(doc_dict)

        if data:
            df = pd.DataFrame(data)
            # Asegurar que las columnas booleanas sean de tipo bool
            for col in ['Inicio Trabajo', 'Trabajo Terminado', 'Cobrado', 'Retirado', 'Pendiente']:
                if col in df.columns:
                    df[col] = df[col].fillna(False).astype(bool) # Rellena NaN con False y convierte a bool
            
            # Ordenar por ID para consistencia, si existe la columna
            if 'ID' in df.columns:
                df['ID'] = pd.to_numeric(df['ID'], errors='coerce') # Asegura que ID sea numérico
                df = df.sort_values(by='ID', ascending=True).reset_index(drop=True)

            return df
        else:
            return pd.DataFrame() # Retorna un DataFrame vacío si no hay documentos
    except Exception as e:
        st.error(f"Error al recuperar datos de Firestore para '{collection_name}': {e}")
        st.exception(e)
        return pd.DataFrame()

def delete_document_firestore(collection_name: str, doc_id: str) -> bool:
    """
    Elimina un documento específico de una colección de Firestore.

    Args:
        collection_name (str): El nombre de la colección.
        doc_id (str): El ID del documento a eliminar.

    Returns:
        bool: True si la eliminación fue exitosa, False en caso contrario.
    """
    try:
        db.collection(collection_name).document(doc_id).delete()
        st.success(f"Documento '{doc_id}' eliminado de la colección '{collection_name}'.")
        return True
    except Exception as e:
        st.error(f"Error al eliminar el documento '{doc_id}' de Firestore: {e}")
        return False

def get_next_id(df: pd.DataFrame, id_column: str = 'ID') -> int:
    """
    Obtiene el siguiente ID consecutivo basado en la columna 'ID' de un DataFrame.

    Args:
        df (pd.DataFrame): El DataFrame de Pandas.
        id_column (str): El nombre de la columna que contiene los IDs.

    Returns:
        int: El siguiente ID disponible.
    """
    if df.empty or id_column not in df.columns or df[id_column].isnull().all():
        return 1
    
    # Asegurarse de que la columna ID sea numérica y manejar errores de conversión
    numeric_ids = pd.to_numeric(df[id_column], errors='coerce').dropna()
    if numeric_ids.empty:
        return 1
    
    return int(numeric_ids.max()) + 1