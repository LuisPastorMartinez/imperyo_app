import streamlit as st
from datetime import datetime

from utils.excel_utils import crear_backup_en_memoria
from utils.firestore_utils import load_dataframes_firestore
from utils.restore_from_excel import restore_from_excel


def show_config_page():
    st.header("⚙️ Configuración del Sistema")
    st.write("---")

    tab_backup, tab_restore = st.tabs(["🔐 Backup", "📥 Restaurar"])

    # =================================================
    # BACKUP
    # =================================================
    with tab_backup:
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

    # =================================================
    # RESTAURAR
    # =================================================
    with tab_restore:
        st.subheader("📥 Restaurar desde Excel")
        st.warning("⚠️ Esta acción BORRARÁ todos los datos actuales y los sustituirá por los del Excel.")

        uploaded_file = st.file_uploader(
            "📁 Selecciona un archivo de backup (.xlsx)",
            type=["xlsx"]
        )

        if uploaded_file is not None:
            st.success(f"Archivo cargado: {uploaded_file.name}")

            confirm = st.checkbox(
                "✅ Confirmo que quiero restaurar y borrar los datos actuales"
            )

            if confirm and st.button("🚀 RESTAURAR AHORA", type="primary"):
                with st.spinner("Restaurando datos..."):
                    ok, msg = restore_from_excel(uploaded_file)

                if ok:
                    st.success("🎉 Restauración completada correctamente")
                    st.info("🔄 Recarga la aplicación (F5)")
                else:
                    st.error(f"❌ Error al restaurar: {msg}")
