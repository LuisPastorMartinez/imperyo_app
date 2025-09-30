import streamlit as st
from firebase_admin import firestore
import pandas as pd
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

# Intentar importar backup_to_dropbox
try:
    from utils.excel_utils import backup_to_dropbox
    DROPBOX_AVAILABLE = True
except ImportError:
    DROPBOX_AVAILABLE = False

def show_config_page():
    st.header("⚙️ Configuración del Sistema")
    st.write("---")

    tab1, tab2 = st.tabs(["🔄 Backup Manual", "📥 Restaurar Backup"])

    with tab1:
        st.subheader("📅 Backup de Seguridad")
        st.markdown("""
        > ⚠️ **Importante**:  
        > Por limitaciones de Streamlit, **solo se permite backup manual**.  
        > Haz clic en el botón para guardar tus datos en Dropbox **en cualquier momento**.
        """)

        # Mostrar último backup
        st.markdown("---")
        st.subheader("📊 Último Backup Realizado")
        last_backup = None
        try:
            db = firestore.client()
            doc = db.collection('config').document('backup').get()
            if doc.exists:
                backup_data = doc.to_dict()
                last_backup = backup_data.get('last_backup')
                st.session_state.last_backup = last_backup
        except Exception as e:
            logger.error(f"Error al cargar último backup: {e}")

        if last_backup:
            st.success(f"✅ Fecha: **{last_backup}**")
            try:
                doc = db.collection('config').document('backup').get()
                if doc.exists:
                    backup_data = doc.to_dict()
                    filename = backup_data.get('filename', 'backup.xlsx')
                    st.caption(f"📁 Archivo: `{filename}`")
            except:
                st.caption("📁 Archivo: no disponible")
        else:
            st.info("ℹ️ Aún no se ha realizado ningún backup.")

        # Botón de backup manual
        st.markdown("---")
        st.subheader("📥 Ejecutar Backup Ahora")
        if not DROPBOX_AVAILABLE:
            st.warning("⚠️ Módulo de backup no disponible.")
        else:
            if st.button("🚀 Ejecutar Backup Manual", type="primary"):
                with st.spinner("Realizando backup..."):
                    if 'data' in st.session_state and st.session_state.data:
                        success, result, upload_success, upload_error = backup_to_dropbox(st.session_state.data)
                        if success and upload_success:
                            st.balloons()
                            st.success(f"✅ ¡Backup completado! {result}")
                            # Actualizar en sesión
                            try:
                                doc = db.collection('config').document('backup').get()
                                if doc.exists:
                                    backup_data = doc.to_dict()
                                    st.session_state.last_backup = backup_data.get('last_backup')
                            except Exception as e:
                                logger.error(f"Error al actualizar último backup: {e}")
                        else:
                            st.error(f"❌ Error: {result or upload_error}")
                    else:
                        st.error("❌ No hay datos para respaldar.")

    with tab2:
        st.subheader("📂 Restaurar desde Backup")
        st.warning("⚠️ **Esta acción borrará todos los datos actuales.**")
        
        uploaded_file = st.file_uploader("📁 Sube backup (.xlsx)", type=["xlsx"])

        if uploaded_file is not None:
            st.success(f"✅ Archivo: `{uploaded_file.name}`")
            try:
                xls = pd.ExcelFile(uploaded_file)
                st.markdown("### 📑 Hojas:")
                for sheet in xls.sheet_names:
                    df_preview = pd.read_excel(xls, sheet_name=sheet, nrows=2)
                    st.markdown(f"**{sheet}** ({len(df_preview)} filas)")
                    st.dataframe(df_preview, use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error al leer: {e}")

            confirm = st.checkbox("✅ Confirmo que quiero restaurar y borrar datos actuales")
            
            if confirm:
                if st.button("🚀 RESTAURAR AHORA", type="primary"):
                    with st.spinner("Restaurando... NO CIERRES"):
                        temp_path = "temp_restore.xlsx"
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        success = restore_data_from_excel(temp_path)
                        
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        
                        if success:
                            st.balloons()
                            st.success("🎉 ¡Datos restaurados!")
                            st.info("✅ Recarga la página (F5) para ver los cambios.")
                            # Limpiar caché
                            for key in ['data', 'data_loaded']:
                                if key in st.session_state:
                                    del st.session_state[key]
                        else:
                            st.error("❌ Falló la restauración.")

def restore_data_from_excel(excel_path):
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        import pandas as pd

        if not firebase_admin._apps:
            cred_dict = dict(st.secrets["firestore"])
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        db = firestore.client()

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
                
                # Borrar existentes
                docs = collection_ref.stream()
                batch = db.batch()
                for doc in docs:
                    batch.delete(doc.reference)
                batch.commit()
                
                # Subir nuevos
                for _, row in df.iterrows():
                    doc_data = row.to_dict()
                    for k, v in doc_data.items():
                        if isinstance(v, pd.Timestamp):
                            doc_data[k] = v.tz_localize(None)
                        elif isinstance(v, datetime) and v.tzinfo:
                            doc_data[k] = v.replace(tzinfo=None)
                    collection_ref.add(doc_data)
                
                st.success(f"✅ '{collection_name}' restaurada.")
            else:
                st.warning(f"⚠️ Hoja '{sheet_name}' no encontrada.")
        return True
    except Exception as e:
        st.error(f"❌ Error: {e}")
        logger.error(f"Restore error: {e}")
        return False