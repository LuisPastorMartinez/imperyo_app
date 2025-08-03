import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import datetime # Import datetime para manejar fechas

# --- Inicialización de Firebase ---
# Obtener la configuración de Firebase desde Streamlit secrets
try:
    firebase_credentials_json = st.secrets["firebase"]["config"]
    # Asegurarse de que los saltos de línea de private_key se interpreten correctamente
    # Esto es crucial para los secretos de Streamlit que pueden aplanar los saltos de línea
    if isinstance(firebase_credentials_json, dict) and "private_key" in firebase_credentials_json:
        firebase_credentials_json["private_key"] = firebase_credentials_json["private_key"].replace('\\n', '\n')
    
    cred = credentials.Certificate(firebase_credentials_json)
    
    # Inicializar el SDK de Firebase Admin si aún no está inicializado
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    db = firestore.client()

except KeyError:
    st.error("Error de configuración: No se encontró la configuración de Firebase en secrets.toml. Asegúrate de que la sección '[firebase]' esté configurada correctamente.")
    st.stop()
except Exception as e:
    st.error(f"Error al inicializar Firebase: {e}. Por favor, revisa tus credenciales.")
    st.stop()


# --- Funciones de Utilidad de Firestore ---

def load_dataframes_firestore():
    """
    Carga todos los DataFrames desde las colecciones de Firestore.
    Asegura el orden de las columnas y la ordenación por ID.
    """
    data = {}
    try:
        # Definir las columnas esperadas para 'pedidos' para mantener la estructura y el orden
        pedidos_expected_columns = [
            'ID', 'Producto', 'Cliente', 'Teléfono', 'Club', 'Talla', 'Tela',
            'Breve Descripción', 'Fecha Entrada', 'Fecha Salida', 'Precio',
            'Precio Factura', 'Tipo de pago', 'Adelanto', 'Observaciones',
            'Inicio Trabajo', 'Cobrado', 'Retirado', 'Pendiente', 'Trabajo Terminado'
        ]

        # Cargar la colección 'pedidos'
        pedidos_list = []
        for doc in db.collection('pedidos').stream():
            doc_data = doc.to_dict()
            doc_data['id_documento_firestore'] = doc.id # Almacenar el ID del documento de Firestore
            pedidos_list.append(doc_data)
        
        df_pedidos = pd.DataFrame(pedidos_list)
        if df_pedidos.empty:
            # Crear un DataFrame vacío con todas las columnas esperadas
            data['df_pedidos'] = pd.DataFrame(columns=pedidos_expected_columns + ['id_documento_firestore'])
        else:
            # Asegurarse de que 'ID' sea numérico para la ordenación, forzando errores a NaN
            df_pedidos['ID'] = pd.to_numeric(df_pedidos['ID'], errors='coerce')
            
            # Reindexar para asegurar que todas las columnas esperadas estén presentes, rellenando las faltantes con NaN
            df_pedidos = df_pedidos.reindex(columns=pedidos_expected_columns + ['id_documento_firestore'])
            
            # Ordenar por 'ID' y restablecer el índice
            df_pedidos = df_pedidos.sort_values(by='ID', ascending=True, na_position='last').reset_index(drop=True)
            data['df_pedidos'] = df_pedidos

        # Cargar la colección 'gastos'
        gastos_expected_columns = ['ID', 'Fecha', 'Concepto', 'Importe', 'Tipo']
        gastos_list = []
        for doc in db.collection('gastos').stream():
            doc_data = doc.to_dict()
            doc_data['id_documento_firestore'] = doc.id
            gastos_list.append(doc_data)
        
        df_gastos = pd.DataFrame(gastos_list)
        if df_gastos.empty:
            data['df_gastos'] = pd.DataFrame(columns=gastos_expected_columns + ['id_documento_firestore'])
        else:
            df_gastos['ID'] = pd.to_numeric(df_gastos['ID'], errors='coerce')
            df_gastos = df_gastos.reindex(columns=gastos_expected_columns + ['id_documento_firestore'])
            df_gastos = df_gastos.sort_values(by='ID', ascending=True, na_position='last').reset_index(drop=True)
            data['df_gastos'] = df_gastos

        # Cargar la colección 'totales'
        totales_list = []
        for doc in db.collection('totales').stream():
            doc_data = doc.to_dict()
            doc_data['id_documento_firestore'] = doc.id
            totales_list.append(doc_data)
        data['df_totales'] = pd.DataFrame(totales_list)
        if data['df_totales'].empty:
            data['df_totales'] = pd.DataFrame(columns=['id_documento_firestore']) # Ajustar con las columnas esperadas reales si las hay

        # Cargar la colección 'listas'
        listas_expected_columns = ['Producto', 'Talla', 'Tela', 'Tipo de pago']
        listas_list = []
        for doc in db.collection('listas').stream():
            doc_data = doc.to_dict()
            doc_data['id_documento_firestore'] = doc.id
            listas_list.append(doc_data)
        data['df_listas'] = pd.DataFrame(listas_list)
        if data['df_listas'].empty:
            data['df_listas'] = pd.DataFrame(columns=listas_expected_columns + ['id_documento_firestore'])

        # Cargar la colección 'trabajos'
        trabajos_list = []
        for doc in db.collection('trabajos').stream():
            doc_data = doc.to_dict()
            doc_data['id_documento_firestore'] = doc.id
            trabajos_list.append(doc_data)
        data['df_trabajos'] = pd.DataFrame(trabajos_list)
        if data['df_trabajos'].empty:
            data['df_trabajos'] = pd.DataFrame(columns=['id_documento_firestore']) # Ajustar con las columnas esperadas reales si las hay

        return data
    except Exception as e:
        st.error(f"Error al cargar datos de Firestore: {e}")
        return None

def save_dataframe_firestore(df, collection_name):
    """
    Guarda un DataFrame completo en una colección de Firestore.
    Elimina todos los documentos existentes y luego añade los nuevos en un proceso por lotes.
    """
    try:
        # Paso 1: Eliminar todos los documentos existentes en la colección usando un lote
        current_docs = db.collection(collection_name).stream()
        delete_batch = db.batch()
        for doc in current_docs:
            delete_batch.delete(doc.reference)
        delete_batch.commit() # Confirmar las eliminaciones

        # Paso 2: Añadir todas las filas del DataFrame como nuevos documentos usando un nuevo lote
        add_batch = db.batch()
        for index, row in df.iterrows():
            doc_data = row.drop('id_documento_firestore', errors='ignore').to_dict()
            
            # Convertir Timestamps de Pandas y NaT a objetos datetime/None de Python para compatibilidad con Firestore
            for key, value in doc_data.items():
                if isinstance(value, pd.Timestamp):
                    doc_data[key] = value.to_pydatetime()
                elif pd.isna(value) and isinstance(value, pd.NaT): # Manejar explícitamente NaT
                    doc_data[key] = None
                elif pd.isna(value): # Manejar otros valores NaN/None
                    doc_data[key] = None
                # Manejar casos donde un valor podría ser una Serie (ej. si una columna contiene listas)
                elif isinstance(value, pd.Series):
                    doc_data[key] = value.tolist() if isinstance(value.iloc[0], list) else value.iloc[0]

            # Firestore generará automáticamente un nuevo ID de documento
            add_batch.set(db.collection(collection_name).document(), doc_data) # Usar set() con auto-ID
        
        add_batch.commit() # Confirmar las adiciones
        return True
    except Exception as e:
        st.error(f"Error al guardar datos en Firestore para la colección '{collection_name}': {e}")
        return False

def delete_document_firestore(collection_name, doc_id_firestore):
    """
    Elimina un documento específico de una colección de Firestore.
    """
    try:
        db.collection(collection_name).document(doc_id_firestore).delete()
        return True
    except Exception as e:
        st.error(f"Error al eliminar el documento '{doc_id_firestore}' de la colección '{collection_name}': {e}")
        return False

def get_next_id(df, id_column_name):
    """
    Calcula el siguiente ID disponible para una columna de ID dada en un DataFrame.
    """
    if df.empty or df[id_column_name].isnull().all():
        return 1
    # Asegurarse de que la columna ID sea numérica antes de encontrar el máximo
    max_id = pd.to_numeric(df[id_column_name], errors='coerce').max()
    return int(max_id) + 1 if pd.notna(max_id) else 1
