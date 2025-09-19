import streamlit as st
from utils.excel_utils import backup_to_dropbox
import time
from apscheduler.triggers.cron import CronTrigger
from firebase_admin import firestore
import pandas as pd
from datetime import datetime

# --- IMPORTAR backup_job desde app.py ---
try:
    from app import backup_job
except ImportError:
    st.error("❌ No se pudo importar 'backup_job' desde app.py. Verifica la estructura del proyecto.")
    backup_job = None

def show_config_page():
    st.header("⚙️ Configuración del Sistema")
    st.write("---")

    tab1, tab2 = st.tabs(["🔄 Backup Automático", "📥 Restaurar Backup"])

    with tab1:
        st.subheader("📅 Configuración de Backup Automático")
        st.markdown("Programa un backup semanal para mantener tus datos seguros.")

        # Cargar valores actuales desde st.session_state
        current_config = st.session_state.get('backup_config', {
            "enabled": False,
            "day": "Sunday",
            "time": "02:00"
        })
        
        enabled = st.checkbox("✅ Activar backup automático", value=current_config["enabled"])
        
        day_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day = st.selectbox(
            "📆 Día de la semana", 
            day_options, 
            index=day_options.index(current_config["day"]) if current_config["day"] in day_options else 6
        )
        
        time_str = st.text_input(
            "⏰ Hora (HH:MM)", 
            value=current_config["time"],
            max_chars=5,
            help="Formato 24h, ej: 02:00, 14:30"
        )

        # Validar formato de hora
        hora_valida = True
        if time_str:
            try:
                hour, minute = time_str.split(":")
                if not (0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
                    hora_valida = False
            except:
                hora_valida = False

        if not hora_valida:
            st.warning("⚠️ Formato de hora inválido. Usa HH:MM (ej: 02:00, 14:30)")

        if st.button("💾 Guardar Configuración", type="primary", disabled=not hora_valida):
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
            
            if enabled and hora_valida:
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
                    
                    if 'scheduler' in st.session_state and backup_job:
                        st.session_state.scheduler.add_job(backup_job, trigger, id='backup_job', replace_existing=True)
                        st.success(f"✅ Backup automático programado para {day} a las {time_str}.")
                    else:
                        st.warning("⚠️ Scheduler no disponible. El backup se programará en el próximo inicio.")
                except Exception as e:
                    st.error(f"❌ Error al programar backup: {e}")
            else:
                if enabled and not hora_valida:
                    st.error("❌ No se puede programar el backup: hora inválida.")
                else:
                    st.info("⏸️ Backup automático desactivado.")

        # --- ✅ Mostrar próximo backup programado ---
        st.markdown("---")
        st.subheader("📅 Próximo Backup Programado")
        if st.session_state.backup_config.get("enabled", False) and hora_valida:
            next_backup = f"{st.session_state.backup_config['day']} a las {st.session_state.backup_config['time']}"
            st.info(f"ℹ️ Próximo backup: **{next_backup}**")
        else:
            st.info("ℹ️ Backup automático desactivado o configuración inválida.")

        # --- ✅ Estado del scheduler ---
        st.markdown("---")
        st.subheader("⚙️ Estado del Sistema de Backups")
        col1, col2 = st.columns(2)
        
        with col1:
            if 'scheduler' in st.session_state and st.session_state.scheduler.get_jobs():
                st.success("✅ Scheduler: Activo")
                jobs = st.session_state.scheduler.get_jobs()
                for job in jobs:
                    st.caption(f"• Job ID: `{job.id}` | Próxima ejecución: {job.next_run_time}")
            else:
                st.warning("⚠️ Scheduler: Inactivo")

        with col2:
            # ✅ Mostrar último backup
            st.subheader("📊 Último Backup Realizado")
            if 'last_backup' in st.session_state and st.session_state.last_backup:
                st.success(f"✅ Fecha: **{st.session_state.last_backup}**")
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
        st.subheader("📥 Backup Manual Inmediato")
        st.info("Haz un backup de tus datos en este momento, sin esperar al programado.")

        if st.button("🚀 Ejecutar Backup Manual", type="primary"):
            with st.spinner("Realizando backup manual..."):
                if 'data' in st.session_state:
                    success, result, upload_success, upload_error = backup_to_dropbox(st.session_state.data)
                    if success and upload_success:
                        st.balloons()
                        st.success(f"✅ ¡Backup manual completado! {result}")
                        
                        # Actualizar último backup en sesión
                        try:
                            db = firestore.client()
                            doc = db.collection('config').document('backup').get()
                            if doc.exists:
                                backup_data = doc.to_dict()
                                st.session_state.last_backup = backup_data.get('last_backup', st.session_state.last_backup)
                        except:
                            pass
                    else:
                        st.error(f"❌ Error en backup manual: {result or upload_error}")
                else:
                    st.error("❌ No hay datos para respaldar.")

    with tab2:
        st.subheader("📂 Restaurar Datos desde Backup")
        st.warning("⚠️ **Esta acción borrará todos los datos actuales y los reemplazará con el backup.**")
        st.markdown("### Pasos para restaurar:")
        st.markdown("1. Sube tu archivo de backup (.xlsx)\n2. Verifica que el archivo es correcto\n3. Haz clic en 'Restaurar Datos'")

        uploaded_file = st.file_uploader("📁 Sube tu archivo de backup (.xlsx)", type=["xlsx"], key="restore_uploader")

        if uploaded_file is not None:
            st.success(f"✅ Archivo cargado: `{uploaded_file.name}`")
            
            # Vista previa del archivo
            try:
                xls = pd.ExcelFile(uploaded_file)
                st.markdown("### 📑 Hojas en el archivo:")
                for sheet in xls.sheet_names:
                    df_preview = pd.read_excel(xls, sheet_name=sheet, nrows=3)
                    st.markdown(f"**{sheet}** ({len(df_preview)} filas de ejemplo)")
                    st.dataframe(df_preview, use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error al leer el archivo: {e}")

            st.warning("⚠️ **Al hacer clic en 'Restaurar', se eliminarán todos los datos actuales.**")
            
            # Confirmación
            confirm_restore = st.checkbox("✅ Confirmo que quiero restaurar los datos y entiendo que se borrarán los actuales")
            
            if confirm_restore:
                if st.button("🚀 RESTAURAR DATOS AHORA", type="primary"):
                    with st.spinner("Restaurando datos... NO CIERRES ESTA PÁGINA"):
                        # Guardar archivo temporalmente
                        temp_path = "temp_restore_backup.xlsx"
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Función de restauración
                        success = restore_data_from_excel(temp_path)
                        
                        # Limpiar archivo temporal
                        import os
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        
                        if success:
                            st.balloons()
                            st.success("🎉 ¡Datos restaurados correctamente!")
                            st.info("✅ Por favor, recarga la app (F5 o botón de recargar) para ver los datos actualizados.")
                            
                            # Limpiar caché de datos
                            if 'data' in st.session_state:
                                del st.session_state['data']
                            if 'data_loaded' in st.session_state:
                                st.session_state['data_loaded'] = False
                        else:
                            st.error("❌ Falló la restauración. Verifica el archivo y los permisos de Firestore.")
            else:
                st.info("ℹ️ Marca la casilla de confirmación para habilitar la restauración.")

def restore_data_from_excel(excel_path):
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

        # Mapeo de hojas a colecciones
        collection_mapping = {
            'pedidos': 'pedidos',
            'gastos': 'gastos',
            'totales': 'totales',
            'listas': 'listas',
            'trabajos': 'trabajos'
        }

        xls = pd.ExcelFile(excel_path)
        
        for sheet_name, collection_name in collection_mapping.items():
            if sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                collection_ref = db.collection(collection_name)
                
                # Limpiar colección existente
                docs = collection_ref.stream()
                batch = db.batch()
                count_deleted = 0
                for doc in docs:
                    batch.delete(doc.reference)
                    count_deleted += 1
                batch.commit()
                
                st.info(f"🧹 Colección '{collection_name}' limpiada ({count_deleted} documentos eliminados). Subiendo {len(df)} registros...")
                
                # Subir nuevos documentos
                count_added = 0
                for _, row in df.iterrows():
                    doc_data = row.to_dict()
                    # Eliminar zona horaria de fechas
                    for key, value in doc_data.items():
                        if isinstance(value, pd.Timestamp):
                            doc_data[key] = value.tz_localize(None)
                        elif isinstance(value, datetime) and value.tzinfo is not None:
                            doc_data[key] = value.replace(tzinfo=None)
                    collection_ref.add(doc_data)
                    count_added += 1
                
                st.success(f"✅ Colección '{collection_name}' restaurada desde hoja '{sheet_name}' ({count_added} documentos añadidos).")
            else:
                st.warning(f"⚠️ Hoja '{sheet_name}' no encontrada en el archivo.")
        return True
    except Exception as e:
        st.error(f"❌ Error al restaurar datos: {e}")
        return False