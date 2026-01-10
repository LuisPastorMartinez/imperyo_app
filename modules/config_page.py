import streamlit as st
import pandas as pd
from datetime import datetime
import logging
import os

from utils.excel_utils import crear_backup_local
from utils.firestore_utils import load_dataframes_firestore

logger = logging.getLogger(__name__)

# =====================================================
# CONFIG PAGE
# =====================================================
def show_config_page():
    st.header(⚙️ Configuración del Sistema")
    st.write("---")

    tab1, tab2 = st.tabs(["🔐 Backup Local", "📥 Restaurar Backup"])

    # =================================================
    # BACKUP LOCAL
    # =================================================
    with tab1:
        st.subheader("📦 Backup de seguridad (local)")
        st.markdown("""
        El backup se guardará **en una carpeta del PC**, dentro del proyecto.
        
        Recomendado:
        - Antes de hacer cambios importantes
        - Antes de cerrar una sesión de pruebas
        """)

        if st.button("🚀 Crear backup ahora", type="primary"):
            with st.spinner("Creando backup..."):
                data = load_dataframes_firestore()
                ok, result = crear_backup_local(data)

            if ok:
                st.success("✅ Backup creado correctamente")
                st.code(result)
                st.info("📂 El archivo se ha guardado en la carpeta /backups")
            else:
                st.error(f"❌ Error creando backup: {result}")

    # =================================================
    # RESTAURAR BACKUP
    # =================================================
    with tab2:
        st.subheader("📂 Restaurar desde Backup")
        st.warning("⚠️ **Esta acción borrará TODOS los datos actuales.**")

        uploaded_file = st.file_uploader(
            "📁 Sube un archivo de backup (.xlsx)",
            type=["xlsx"]
        )

        if uploaded_file is not None:
            st.success(f"✅ Archivo cargado: `{uploaded_file.name}`")

            try:
                xls = pd.ExcelFile(uploaded_file)
                st.markdown("### 📑 Hojas encontradas:")
                for sheet in xls.sheet_names:
                    df_preview = pd.read_excel(xls, sheet_name=sheet, nrows=2)
                    st.markdown(f"**{sheet}**")
                    st.dataframe(df_preview, use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error al leer el archivo: {e}")
                return

            confirm = st.checkbox("✅ Confirmo que quiero restaurar y borrar datos actuales")

            if confirm and st.button("🚀 RESTAURAR AHORA", type="primary"):
                with st.spinner("Restaurando datos... NO CIERRES"):
                    temp_path = "temp_restore.xlsx"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    success = restore_data_from_excel(temp_path)

                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                    if success:
                        st.success("🎉 Datos restaurados correctamente")
                        st.info("🔄 Recarga la aplicación (F5)")
                        for key in ["data", "data_loaded"]:
                            if key in st.session_state:
                                del st.session_state[key]
                    else:
                        st.error("❌ Error al restaurar datos")


# =====================================================
# RESTORE LOGIC
# =====================================================
def restore_data_from_excel(excel_path):
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            cred = credentials.Certificate(dict(st.secrets["firestore"]))
            firebase_admin.initialize_app(cred)

        db = firestore.client()

        collection_mapping = {
            "pedidos": "pedidos",
            "gastos": "gastos",
            "totales": "totales",
            "listas": "listas",
            "trabajos": "trabajos",
        }

        xls = pd.ExcelFile(excel_path)

        for sheet, collection in collection_mapping.items():
            if sheet not in xls.sheet_names:
                continue

            df = pd.read_excel(xls, sheet_name=sheet)

            # Borrar colección actual
            col_ref = db.collection(collection)
            batch = db.batch()
            for doc in col_ref.stream():
                batch.delete(doc.reference)
            batch.commit()

            # Subir nuevos datos
            for _, row in df.iterrows():
                doc_data = row.to_dict()
                for k, v in doc_data.items():
                    if isinstance(v, pd.Timestamp):
                        doc_data[k] = v.tz_localize(None)
                    elif isinstance(v, datetime) and v.tzinfo:
                        doc_data[k] = v.replace(tzinfo=None)
                col_ref.add(doc_data)

        return True

    except Exception as e:
        st.error(f"❌ Error restaurando datos: {e}")
        logger.error(e)
        return False
