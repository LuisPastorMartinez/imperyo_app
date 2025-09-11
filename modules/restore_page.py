# modules/restore_page.py
import streamlit as st
import pandas as pd
from utils.restore_from_excel import restore_data_from_excel

def show_restore_page():
    st.header("Restaurar Datos desde Backup")
    st.warning("⚠️ Esta acción borrará todos los datos actuales y los reemplazará con el backup.")

    uploaded_file = st.file_uploader("Sube tu archivo de backup (.xlsx)", type=["xlsx"])

    if uploaded_file is not None:
        st.success("Archivo cargado correctamente.")

        # Mapeo de hojas a colecciones
        collection_mapping = {
            'pedidos': 'pedidos',
            'gastos': 'gastos',
            'totales': 'totales',
            'listas': 'listas',
            'trabajos': 'trabajos'
        }

        if st.button("🚀 Restaurar Datos"):
            with st.spinner("Restaurando datos..."):
                # Guardar archivo temporalmente
                with open("temp_backup.xlsx", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                success = restore_data_from_excel("temp_backup.xlsx", collection_mapping)
                
                if success:
                    st.balloons()
                    st.success("✅ ¡Datos restaurados correctamente!")
                    st.info("Por favor, recarga la app para ver los datos actualizados.")
                else:
                    st.error("❌ Falló la restauración. Verifica el archivo y los permisos.")