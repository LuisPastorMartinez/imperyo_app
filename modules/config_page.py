import streamlit as st
from datetime import datetime

from utils.excel_utils import crear_backup_en_memoria
from utils.firestore_utils import load_dataframes_firestore


def show_config_page():
    st.header("⚙️ Configuración del Sistema")
    st.write("---")

    st.subheader("🔐 Backup de seguridad")

    st.markdown(
        """
        Este backup se genera **al momento** y se descarga en tu ordenador.
        
        Recomendado:
        - Antes de hacer cambios importantes
        - Antes de cerrar una sesión de trabajo
        """
    )

    if st.button("📦 Generar backup"):
        with st.spinner("Generando backup..."):
            data = load_dataframes_firestore()
            buffer = crear_backup_en_memoria(data)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"backup_imperyo_{timestamp}.xlsx"

        st.success("✅ Backup listo para descargar")

        st.download_button(
            label="⬇️ Descargar backup",
            data=buffer,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
