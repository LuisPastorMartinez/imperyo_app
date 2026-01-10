import streamlit as st
import pandas as pd
from datetime import datetime
import os
import logging

from utils.excel_utils import crear_backup_local
from utils.firestore_utils import load_dataframes_firestore

logger = logging.getLogger(__name__)


def show_config_page():
    st.header("⚙️ Configuración del Sistema")
    st.write("---")

    tab_backup, tab_restore = st.tabs(["🔐 Backup local", "📥 Restaurar"])

    # ===============================
    # BACKUP LOCAL
    # ===============================
    with tab_backup:
        st.subheader("📦 Backup de seguridad")

        st.markdown(
            "El backup se guarda **localmente en tu PC**, dentro del proyecto.\n\n"
            "Recomendado antes de hacer cambios importantes."
        )

        if st.button("🚀 Crear backup ahora", type="primary"):
            with st.spinner("Creando backup..."):
                data = load_dataframes_firestore()
                ok, result = crear_backup_local(data)

            if ok:
                st.success("✅ Backup creado correctamente")
                st.code(result)
            else:
                st.error(f"❌ Error creando backup: {result}")

    # ===============================
    # RESTAURAR (DESACTIVADO POR AHORA)
    # ===============================
    with tab_restore:
        st.info("🔒 Restaurar estará disponible más adelante.")
