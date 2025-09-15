# modules/config_page.py
import streamlit as st
from utils.excel_utils import backup_to_dropbox
import time
from apscheduler.triggers.cron import CronTrigger
from firebase_admin import firestore  # ✅ Importado para guardar en Firestore

def show_config_page():
    st.header("⚙️ Configuración")

    tab1, tab2 = st.tabs(["Backup Automático", "Restaurar Backup"])

    with tab1:
        st.subheader("📅 Configurar Backup Automático")
        st.write("Programa el backup automático semanal.")

        # Cargar valores actuales desde st.session_state
        current_config = st.session_state.backup_config
        enabled = st.checkbox("Activar backup automático", value=current_config["enabled"])
        day = st.selectbox("Día de la semana", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], index=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(current_config["day"]))
        time_str = st.text_input("Hora (HH:MM)", value=current_config["time"])

        if st.button("💾 Guardar Configuración"):
            # Guardar configuración en sesión
            st.session_state.backup_config = {
                "enabled": enabled,
                "day": day,
                "time": time_str
            }
            
            # ✅ Guardar configuración en Firestore
            try:
                db = firestore.client()
                db.collection('config').document('backup_settings').set({
                    'enabled': enabled,
                    'day': day,
                    'time': time_str,
                    'updated_at': firestore.SERVER_TIMESTAMP
                })
                st.success("✅ Configuración guardada permanentemente en Firestore.")
            except Exception as e:
                st.error(f"❌ Error al guardar configuración en Firestore: {e}")

            # Reiniciar scheduler
            if 'scheduler' in st.session_state:
                st.session_state.scheduler.remove_all_jobs()
            
            if enabled:
                try:
                    hour, minute = time_str.split(":")
                    day_map = {
                        "Monday": "mon",
                        "Tuesday": "tue",
                        "Wednesday": "wed",
                        "Thursday": "thu",
                        "Friday": "fri",
                        "Saturday": "sat",
                        "Sunday": "sun"
                    }
                    cron_day = day_map.get(day, "sun")
                    trigger = CronTrigger(day_of_week=cron_day, hour=int(hour), minute=int(minute))
                    
                    if 'scheduler' in st.session_state:
                        st.session_state.scheduler.add_job(backup_job, trigger, id='backup_job', replace_existing=True)
                    
                    st.success(f"✅ Backup automático programado para {day} a las {time_str}.")
                except Exception as e:
                    st.error(f"❌ Error al programar backup: {e}")
            else:
                st.info("⏸️ Backup automático desactivado.")

        # --- ✅ Mostrar próximo backup programado ---
        st.markdown("---")
        st.subheader("📅 Próximo Backup Programado")
        if st.session_state.backup_config["enabled"]:
            next_backup = f"{st.session_state.backup_config['day']} a las {st.session_state.backup_config['time']}"
            st.info(f"ℹ️ Próximo backup: **{next_backup}**")
        else:
            st.info("ℹ️ Backup automático desactivado.")

        # --- ✅ Estado del scheduler ---
        st.markdown("---")
        st.subheader("⚙️ Estado del Scheduler")
        if 'scheduler' in st.session_state and st.session_state.scheduler.get_jobs():
            st.success("✅ Scheduler activo y funcionando.")
            jobs = st.session_state.scheduler.get_jobs()
            for job in jobs:
                st.caption(f"• Job ID: `{job.id}` | Próxima ejecución: {job.next_run_time}")
        else:
            st.warning("⚠️ Scheduler inactivo o sin jobs programados.")

        # --- ✅ Mostrar último backup ---
        st.markdown("---")
        st.subheader("📊 Último Backup")
        if 'last_backup' in st.session_state and st.session_state.last_backup:
            st.success(f"✅ Último backup: **{st.session_state.last_backup}**")
            # ✅ Mostrar nombre del archivo desde Firestore
            try:
                db = firestore.client()
                doc = db.collection('config').document('backup').get()
                if doc.exists:
                    backup_data = doc.to_dict()
                    filename = backup_data.get('filename', 'backup_desconocido.xlsx')
                    st.caption(f"📁 Archivo: `{filename}`")
            except Exception as e:
                st.caption("📁 Archivo: no disponible")
        else:
            st.info("ℹ️ Aún no se ha realizado ningún backup.")

        # --- ✅ Botón de backup manual ---
        st.markdown("---")
        st.subheader("📥 Backup Manual")
        if st.button("🚀 Hacer Backup Ahora", type="primary"):
            with st.spinner("Realizando backup manual..."):
                if 'data' in st.session_state:
                    success, result, upload_success, upload_error = backup_to_dropbox(st.session_state.data)
                    if success and upload_success:
                        st.balloons()
                        st.success(f"✅ ¡Backup manual completado! {result}")
                    else:
                        st.error(f"❌ Error en backup manual: {result or upload_error}")
                else:
                    st.error("❌ No hay datos para respaldar.")

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
                    
                    # Función de restauración
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

# --- IMPORTAR backup_job desde app.py ---
from app import backup_job