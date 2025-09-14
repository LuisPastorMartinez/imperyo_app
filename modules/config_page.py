# modules/config_page.py
import streamlit as st
from utils.excel_utils import backup_to_dropbox
import schedule
import time
import threading

def show_config_page():
    st.header("⚙️ Configuración")

    tab1, tab2 = st.tabs(["Backup Automático", "Restaurar Backup"])

    with tab1:
        st.subheader("📅 Configurar Backup Automático")
        st.write("Programa el backup automático semanal.")

        enabled = st.checkbox("Activar backup automático", value=st.session_state.backup_config["enabled"])
        day = st.selectbox("Día de la semana", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], index=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(st.session_state.backup_config["day"]))
        time_str = st.text_input("Hora (HH:MM)", value=st.session_state.backup_config["time"])

        if st.button("💾 Guardar Configuración"):
            st.session_state.backup_config = {
                "enabled": enabled,
                "day": day,
                "time": time_str
            }
            # Programar backup
            schedule.clear()
            if enabled:
                job = lambda: backup_job(st.session_state.data if 'data' in st.session_state else {})
                getattr(schedule.every(), day.lower()).at(time_str).do(job)
                st.success(f"✅ Backup automático programado para {day} a las {time_str}.")
            else:
                st.info("⏸️ Backup automático desactivado.")

    with tab2:
        st.subheader("📂 Restaurar Datos desde Backup")
        st.warning("⚠️ **Esta acción borrará todos los datos actuales y los reemplazará con el backup.**")

        uploaded_file = st.file_uploader("Sube tu archivo de backup (.xlsx)", type=["xlsx"], key="restore_uploader")

        if uploaded_file is not None:
            st.success(f"✅ Archivo cargado: `{uploaded_file.name}`")
            st.info("⚠️ Al hacer clic en 'Restaurar', se eliminarán todos los datos actuales.")

            # Mapeo de hojas a colecciones
            collection_mapping = {
                'pedidos': 'pedidos',
                'gastos': 'gastos',
                'totales': 'totales',
                'listas': 'listas',
                'trabajos': 'trabajos'
            }

            if st.button("🚀 RESTAURAR DATOS AHORA", type="primary"):
                with st.spinner("Restaurando datos... NO CIERRES ESTA PÁGINA"):
                    # Guardar archivo temporalmente
                    temp_path = "temp_restore_backup.xlsx"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Función de restauración (mover desde restore_page.py)
                    success = restore_data_from_excel(temp_path, collection_mapping)
                    
                    # Limpiar archivo temporal
                    import os
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    
                    if success:
                        st.balloons()
                        st.success("🎉 ¡Datos restaurados correctamente!")
                        st.info("✅ Por favor, recarga la app (F5 o botón de recargar) para ver los datos actualizados.")
                        if 'data' in st.session_state:
                            del st.session_state['data']
                        if 'data_loaded' in st.session_state:
                            st.session_state['data_loaded'] = False
                    else:
                        st.error("❌ Falló la restauración. Verifica el archivo y los permisos de Firestore.")

def restore_data_from_excel(excel_path, collection_mapping):
    """Restaura datos desde un archivo Excel a Firestore."""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        import pandas as pd

        # Inicializar Firestore si no está activo
        if not firebase_admin._apps:
            cred_dict = dict(st.secrets["firestore"])
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        db = firestore.client()

        xls = pd.ExcelFile(excel_path)
        
        for sheet_name, collection_name in collection_mapping.items():
            if sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                collection_ref = db.collection(collection_name)
                
                # Limpiar colección existente
                docs = collection_ref.stream()
                batch = db.batch()
                for doc in docs:
                    batch.delete(doc.reference)
                batch.commit()
                
                st.info(f"🧹 Colección '{collection_name}' limpiada. Subiendo {len(df)} registros...")
                
                # Subir nuevos documentos
                for _, row in df.iterrows():
                    doc_data = row.to_dict()
                    # Eliminar zona horaria de fechas
                    for key, value in doc_data.items():
                        if isinstance(value, pd.Timestamp):
                            doc_data[key] = value.tz_localize(None)
                        elif isinstance(value, datetime) and value.tzinfo is not None:
                            doc_data[key] = value.replace(tzinfo=None)
                    collection_ref.add(doc_data)
                
                st.success(f"✅ Colección '{collection_name}' restaurada desde hoja '{sheet_name}'.")
        return True
    except Exception as e:
        st.error(f"❌ Error al restaurar datos: {e}")
        return False

def backup_job(data):
    """Función que se ejecuta en el hilo de backup automático."""
    if not 
        return

    success, result, upload_success, upload_error = backup_to_dropbox(data)
    if success and upload_success:
        print(f"[BACKUP AUTOMÁTICO] Éxito: {result}")
    else:
        print(f"[BACKUP AUTOMÁTICO] Error: {result or upload_error}")