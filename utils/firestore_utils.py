import streamlit as st

import pandas as pd

import firebase_admin

from firebase_admin import credentials, firestore

import json  



# No es necesario importar 'json' si st.secrets ya devuelve un diccionario TOML



# Define los nombres de tus colecciones en Firestore (equivalente a las hojas de Excel)

# ¡IMPORTANTE! Estos nombres deben ser los que usarás en Firestore.

# Por simplicidad, usaremos los mismos nombres que tus hojas de Excel, pero en minúsculas.

COLLECTION_NAMES = {

    'pedidos': 'pedidos',

    'gastos': 'gastos',

    'totales': 'totales',

    'listas': 'listas',

    'trabajos': 'trabajos'

}



# --- Inicialización de Firebase (solo una vez) ---

# Usamos st.cache_resource para asegurarnos de que Firebase se inicialice solo una vez

@st.cache_resource

def initialize_firestore():

    try:

        # Recupera las credenciales de Firebase desde st.secrets

        creds_dict = st.secrets["firestore"]

        

        # Convierte el AttrDict a un diccionario de Python

        # NOTA: `st.secrets` ya es un diccionario normal en versiones recientes,

        # así que esta conversión a `dict()` podría no ser necesaria,

        # pero es una buena práctica de seguridad.

        creds_dict_puro = dict(creds_dict)

        

        # Inicializa la aplicación Firebase con las credenciales

        if not firebase_admin._apps:

            # ¡LA CORRECCIÓN ESTÁ AQUÍ!

            # Pasa el diccionario directamente a credentials.Certificate()

            cred = credentials.Certificate(creds_dict_puro) 

            firebase_admin.initialize_app(cred)

        

        db = firestore.client()

        return db

    except Exception as e:

        st.error(f"Error al inicializar Firebase Firestore: {e}")

        st.info("Asegúrate de que el archivo .streamlit/secrets.toml esté correctamente configurado con las credenciales de Firebase Firestore bajo la sección '[firestore]' y que el formato TOML sea válido.")

        return None





# Inicializa Firestore y obtén la instancia de la base de datos

db = initialize_firestore()



def load_dataframes_firestore():

    """

    Carga todos los DataFrames necesarios desde las colecciones de Firestore.

    Devuelve un diccionario de DataFrames.

    """

    if db is None:

        st.error("La conexión a Firestore no está disponible. No se pueden cargar los datos.")

        return None



    data = {}

    try:

        for key, collection_name in COLLECTION_NAMES.items():

            docs = db.collection(collection_name).stream()

            records = []

            for doc in docs:

                record = doc.to_dict()

                record['id_documento_firestore'] = doc.id # Guarda el ID del documento de Firestore

                records.append(record)

            

            # Convierte la lista de diccionarios a DataFrame

            df = pd.DataFrame(records)

            

            # Asegura que las columnas booleanas se carguen correctamente

            if key == 'pedidos':

                # Columnas booleanas esperadas en la colección 'pedidos'

                boolean_cols = ['Inicio Trabajo', 'Cobrado', 'Retirado', 'Pendiente', 'Trabajo Terminado']

                for col in boolean_cols:

                    if col in df.columns:

                        # Convierte a booleano, tratando None/NaN/0/False como False, y otros como True

                        df[col] = df[col].apply(lambda x: bool(x) if pd.notna(x) else False)

            

            data[f'df_{key}'] = df

        return data

    except Exception as e:

        st.error(f"Error al cargar datos de Firestore: {e}")

        st.info("Asegúrate de que las reglas de seguridad de Firestore permitan la lectura y que las colecciones existan.")

        return None



def save_dataframe_firestore(df, collection_key):

    """

    Guarda un DataFrame en una colección específica de Firestore.

    Para 'pedidos', actualiza documentos existentes o añade nuevos.

    Para otras colecciones, sobrescribe la colección completa.

    """

    if db is None:

        st.error("La conexión a Firestore no está disponible. No se pueden guardar los datos.")

        return False



    collection_name = COLLECTION_NAMES.get(collection_key)

    if not collection_name:

        st.error(f"Error: Clave de colección '{collection_key}' no reconocida para guardar.")

        return False



    try:

        if collection_key == 'pedidos':

            # Para la colección 'pedidos', iteramos sobre el DataFrame

            # y usamos el 'id_documento_firestore' para actualizar o añadimos nuevos

            for index, row in df.iterrows():

                doc_id = row.get('id_documento_firestore') # Obtiene el ID de Firestore si existe

                record_to_save = row.drop('id_documento_firestore', errors='ignore').to_dict() # Elimina la columna temporal



                # Convierte Timestamp de Pandas a datetime.date o None

                for col in ['Fecha Entrada', 'Fecha Salida']:

                    if pd.notna(record_to_save.get(col)):

                        record_to_save[col] = record_to_save[col].to_pydatetime().date()

                    else:

                        record_to_save[col] = None # Almacena como None si es NaT



                # Convierte booleanos de Python a booleanos nativos de Firestore

                for col in ['Inicio Trabajo', 'Cobrado', 'Retirado', 'Pendiente', 'Trabajo Terminado']:

                    if col in record_to_save:

                        record_to_save[col] = bool(record_to_save[col])



                if doc_id:

                    # Si el documento ya tiene un ID de Firestore, lo actualizamos

                    db.collection(collection_name).document(doc_id).set(record_to_save)

                else:

                    # Si es un nuevo registro, Firestore generará un ID automáticamente

                    db.collection(collection_name).add(record_to_save)

            st.success(f"Colección '{collection_name}' actualizada en Firestore.")

        else:

            # Para otras colecciones (Listas, Gastos, etc.), borramos y reescribimos

            # Esto es más simple para datos que no se modifican individualmente con frecuencia

            

            # 1. Borrar todos los documentos existentes en la colección

            docs_to_delete = db.collection(collection_name).stream()

            for doc in docs_to_delete:

                doc.reference.delete()

            

            # 2. Añadir los nuevos documentos del DataFrame

            for index, row in df.iterrows():

                record_to_save = row.to_dict()

                # Convertir Timestamp a datetime.date si es necesario (para fechas)

                for col in df.select_dtypes(include=['datetime64[ns]']).columns:

                    if pd.notna(record_to_save.get(col)):

                        record_to_save[col] = record_to_save[col].to_pydatetime().date()

                    else:

                        record_to_save[col] = None

                db.collection(collection_name).add(record_to_save)

            st.success(f"Colección '{collection_name}' sobrescrita en Firestore.")

        return True

    except Exception as e:

        st.error(f"Error al guardar datos en Firestore para la colección '{collection_name}': {e}")

        st.info("Asegúrate de que las reglas de seguridad de Firestore permitan la escritura y que el formato de los datos sea compatible.")

        return False



def delete_document_firestore(collection_key, doc_id_firestore):

    """

    Elimina un documento específico de una colección en Firestore usando su ID de documento de Firestore.

    """

    if db is None:

        st.error("La conexión a Firestore no está disponible. No se puede eliminar el documento.")

        return False



    collection_name = COLLECTION_NAMES.get(collection_key)

    if not collection_name:

        st.error(f"Error: Clave de colección '{collection_key}' no reconocida para eliminar.")

        return False



    try:

        db.collection(collection_name).document(doc_id_firestore).delete()

        st.success(f"Documento con ID de Firestore '{doc_id_firestore}' eliminado de la colección '{collection_name}'.")

        return True

    except Exception as e:

        st.error(f"Error al eliminar el documento '{doc_id_firestore}' de Firestore: {e}")

        return False



def get_next_id(df, id_column_name):

    """

    Encuentra el siguiente ID disponible buscando el máximo ID existente

    en un DataFrame y sumando 1. Si el DataFrame está vacío, comienza desde 1.

    """

    if df.empty or id_column_name not in df.columns:

        return 1

    # Asegura que la columna ID sea numérica, forzando errores a NaN

    df[id_column_name] = pd.to_numeric(df[id_column_name], errors='coerce')

    # Elimina cualquier fila donde el ID se convirtió en NaN (ej., IDs no numéricos)

    df_clean = df.dropna(subset=[id_column_name])

    if df_clean.empty:

        return 1

    return int(df_clean[id_column_name].max()) + 1