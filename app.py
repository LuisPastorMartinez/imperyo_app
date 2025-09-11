import streamlit as st
import pandas as pd
import os
import hashlib
import re
import sys
from pathlib import Path
from datetime import datetime
import schedule
import time
import threading

# Configuración de paths para imports
sys.path.append(str(Path(__file__).parent))

# Importaciones desde utils
from utils.firestore_utils import (
    load_dataframes_firestore,
    save_dataframe_firestore,
    delete_document_firestore,
    get_next_id
)
from utils.data_utils import limpiar_telefono, limpiar_fecha
from utils.excel_utils import backup_to_dropbox

# Importaciones desde modules
from modules.pedidos_page import show_pedidos_page
from modules.gastos_page import show_gastos_page
from modules.resumen_page import show_resumen_page
from modules.restore_page import show_restore_page

# --- CONFIGURACIÓN BÁSICA DE LA PÁGINA ---
st.set_page_config(
    page_title="ImperYo",
    page_icon="https://www.dropbox.com/scl/fi/opp61pwyq2lxleaj3hxs3/Logo-Movil-e-instagran.png?rlkey=4cruzlufwlz9vfr2myezjkz1d&dl=1",
    layout="wide"
)

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
.stImage > img {
    max-width: 100px;
    height: auto;
}
h1 {
    font-size: 3em;
}
h2 {
    font-size: 2.5em;
}
.mobile-only {
    display: none;
}
.pc-only {
    display: block;
}
@media (max-width: 768px) {
    .stImage > img {
        max-width: 60px;
    }
    h1 {
        font-size: 2em;
    }
    h2 {
        font-size: 1.5em;
    }
    .mobile-only {
        display: block;
    }
    .pc-only {
        display: none;
    }
}
.telefono-input {
    font-family: monospace;
    letter-spacing: 0.1em;
}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
col_logo, col_title = st.columns([0.1, 0.9])
with col_logo:
    st.image("https://www.dropbox.com/scl/fi/opp61pwyq2lxleaj3hxs3/Logo-Movil-e-instagran.png?rlkey=4cruzlufwlz9vfr2myezjkz1d&dl=1", width=80)
with col_title:
    st.header("Imperyo Sport - Gestión de Pedidos y Gastos")

# --- FUNCIÓN PARA UNIFICAR COLUMNAS ---
def unificar_columnas(df):
    if df.empty:
        return df

    if 'Fechas Entrada' in df.columns:
        df = df.drop(columns=['Fechas Entrada'])
    
    if 'Teléfono' in df.columns and 'Telefono' in df.columns:
        df['Telefono'] = df['Telefono'].combine_first(df['Teléfono'])
        df = df.drop(columns=['Teléfono'])
    elif 'Teléfono' in df.columns:
        df = df.rename(columns={'Teléfono': 'Telefono'})
    
    if 'Telefono ' in df.columns:
        df['Telefono'] = df['Telefono'].combine_first(df['Telefono '])
        df = df.drop(columns=['Telefono '])
    
    if 'Telefono' in df.columns:
        df['Telefono'] = df['Telefono'].apply(lambda x: x if pd.isna(x) else str(x).strip())
        df['Telefono'] = df['Telefono'].apply(limpiar_telefono)
    
    if 'Fecha entrada' in df.columns:
        df['Fecha entrada'] = df['Fecha entrada'].apply(limpiar_fecha)
    
    if 'Fecha Entreda' in df.columns:
        df['Fecha entrada'] = df['Fecha entrada'].combine_first(df['Fecha Entreda'].apply(limpiar_fecha))
        df = df.drop(columns=['Fecha Entreda'])
    
    if 'Fecha salida' in df.columns:
        df['Fecha Salida'] = df['Fecha Salida'].combine_first(df['Fecha salida'].apply(limpiar_fecha))
        df = df.drop(columns=['Fecha salida'])
    
    columnas_a_unificar = {
        'Precio factura': 'Precio Factura',
        'Obserbaciones': 'Observaciones',
        'Descripcion del Articulo': 'Breve Descripción'
    }
    
    for col_vieja, col_nueva in columnas_a_unificar.items():
        if col_vieja in df.columns:
            if col_nueva not in df.columns:
                df[col_nueva] = df[col_vieja]
            else:
                df[col_nueva] = df[col_nueva].combine_first(df[col_vieja])
            df = df.drop(columns=[col_vieja])
    
    return df

# --- LÓGICA DE AUTENTICACIÓN ---
def check_password():
    try:
        correct_username = st.secrets["auth"]["username"]
        correct_password_hash = st.secrets["auth"]["password_hash"]
    except KeyError:
        st.error("Error de configuración: No se encontraron las credenciales de autenticación.")
        st.stop()

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "login_attempted" not in st.session_state:
        st.session_state["login_attempted"] = False
    if "username_input" not in st.session_state:
        st.session_state["username_input"] = ""
    if "password_input" not in st.session_state:
        st.session_state["password_input"] = ""

    def authenticate_user():
        hashed_input_password = hashlib.sha256(st.session_state["password_input"].encode()).hexdigest()
        if st.session_state["username_input"] == correct_username and \
           hashed_input_password == correct_password_hash:
            st.session_state["authenticated"] = True
            st.session_state["login_attempted"] = False
            st.session_state["username_input"] = ""
            st.session_state["password_input"] = ""
        else:
            st.session_state["authenticated"] = False
            st.session_state["login_attempted"] = True

    if not st.session_state["authenticated"]:
        st.text_input("Usuario", key="username_input")
        st.text_input("Contraseña", type="password", key="password_input")
        st.button("Iniciar Sesión", on_click=authenticate_user)

        if st.session_state["login_attempted"] and not st.session_state["authenticated"]:
            st.error("Usuario o contraseña incorrectos.")
        return False
    else:
        return True

# --- FUNCIÓN PARA INICIALIZAR SESIÓN ---
def init_session_state():
    defaults = {
        "authenticated": False,
        "login_attempted": False,
        "username_input": "",
        "password_input": "",
        "data_loaded": False,
        "current_summary_view": "Todos los Pedidos",
        "backup_config": {
            "enabled": False,
            "day": "Sunday",
            "time": "02:00"
        }
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# --- FUNCIÓN PARA PROGRAMAR BACKUP AUTOMÁTICO ---
def schedule_backup():
    if not st.session_state.backup_config["enabled"]:
        return

    day = st.session_state.backup_config["day"]
    time_str = st.session_state.backup_config["time"]

    # Limpiar trabajos anteriores
    schedule.clear()

    # Programar nuevo trabajo
    job = lambda: backup_job(st.session_state.data if 'data' in st.session_state else {})
    getattr(schedule.every(), day.lower()).at(time_str).do(job)

    st.success(f"✅ Backup automático programado para {day} a las {time_str}.")

def backup_job(data):
    """Función que se ejecuta en el hilo de backup automático."""
    if not data:
        return

    success, result, upload_success, upload_error = backup_to_dropbox(data)
    if success and upload_success:
        print(f"[BACKUP AUTOMÁTICO] Éxito: {result}")
    else:
        print(f"[BACKUP AUTOMÁTICO] Error: {result or upload_error}")

# --- HILO PARA EJECUTAR BACKUP AUTOMÁTICO ---
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

# Iniciar hilo de scheduler
if 'scheduler_started' not in st.session_state:
    st.session_state.scheduler_started = True
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

# --- LÓGICA PRINCIPAL DE LA APLICACIÓN ---
if check_password():
    init_session_state()

    # --- CARGA Y CORRECCIÓN DE DATOS ---
    if not st.session_state.get('data_loaded', False):
        try:
            data = load_dataframes_firestore()
            if data is None:
                st.error("No se pudieron cargar los datos. Verifica la conexión a Firestore.")
                st.stop()

            st.session_state.data = data

            if 'df_pedidos' in st.session_state.data:
                st.session_state.data['df_pedidos'] = unificar_columnas(st.session_state.data['df_pedidos'])

            st.session_state.data_loaded = True
        except Exception as e:
            st.error(f"Error al cargar datos: {e}")
            st.stop()

    if 'data' not in st.session_state or st.session_state.data is None:
        st.error("No se cargaron los datos correctamente.")
        st.stop()

    required_dfs = ['df_pedidos', 'df_gastos', 'df_totales', 'df_listas', 'df_trabajos']
    for df_name in required_dfs:
        if df_name not in st.session_state.data:
            st.error(f"Error: No se encontró el DataFrame '{df_name}' en los datos cargados.")
            st.stop()

    df_pedidos = st.session_state.data['df_pedidos']
    df_gastos = st.session_state.data['df_gastos']
    df_totales = st.session_state.data['df_totales']
    df_listas = st.session_state.data['df_listas']
    df_trabajos = st.session_state.data['df_trabajos']

    # --- BOTÓN DE CERRAR SESIÓN ---
    st.sidebar.markdown("---")
    if st.sidebar.button("Cerrar Sesión"):
        for key in ["authenticated", "data_loaded", "login_attempted", "username_input", "password_input"]:
            if key in st.session_state:
                del st.session_state[key]
        if 'data' in st.session_state:
            del st.session_state['data']
        st.rerun()

    # --- NAVEGACIÓN ---
    st.sidebar.title("Navegación")
    page = st.sidebar.radio("Ir a:", ["Inicio", "Pedidos", "Gastos", "Resumen", "Ver Datos", "Restaurar Backup", "Configurar Backup"], key="main_page_radio")

    if 'current_summary_view' not in st.session_state:
        st.session_state.current_summary_view = "Todos los Pedidos"

    if page == "Resumen":
        with st.sidebar.expander("Seleccionar Vista de Resumen", expanded=True):
            selected_summary_view_in_expander = st.radio(
                "Ver por categoría:",
                ["Todos los Pedidos", "Trabajos Empezados", "Trabajos Terminados", "Pedidos Pendientes", "Pedidos sin estado específico"],
                key="summary_view_radio"
            )
            st.session_state.current_summary_view = selected_summary_view_in_expander

    # --- CONTENIDO DE LAS PÁGINAS ---
    if page == "Inicio":
        st.header("Bienvenido a Imperyo Sport")
        st.write("---")
        st.subheader("Estado General de Pedidos")
        st.info(f"Total de Pedidos Registrados: **{len(df_pedidos)}**")

        st.markdown("### 🔐 Backup de Seguridad")
        if st.button("💾 Generar Backup y Subir a Dropbox"):
            with st.spinner("Generando backup..."):
                success, result, upload_success, upload_error = backup_to_dropbox(st.session_state.data)
                if success:
                    with open(result, "rb") as f:
                        st.download_button(
                            "📥 Descargar Backup (Excel)",
                            f,
                            file_name=os.path.basename(result),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    if upload_success:
                        st.success(f"✅ Backup subido a Dropbox: `{os.path.basename(result)}`")
                    else:
                        st.warning(f"⚠️ Backup generado, pero error al subir a Dropbox: {upload_error}")
                else:
                    st.error(f"❌ Error al generar backup: {result}")

    elif page == "Ver Datos":
        st.header("Datos Cargados de Firestore")
        st.subheader("Colección 'pedidos'")
        if not df_pedidos.empty:
            df_pedidos_sorted = df_pedidos.sort_values(by='ID', ascending=False)
            new_column_order = [
                'ID', 'Producto', 'Cliente', 'Club', 'Telefono', 'Breve Descripción',
                'Fecha entrada', 'Fecha Salida', 'Precio', 'Precio Factura',
                'Tipo de pago', 'Adelanto', 'Observaciones'
            ]
            existing_columns = [col for col in new_column_order if col in df_pedidos_sorted.columns]
            remaining_columns = [col for col in df_pedidos_sorted.columns if col not in existing_columns]
            final_column_order = existing_columns + remaining_columns
            df_pedidos_reordered = df_pedidos_sorted[final_column_order]
            st.dataframe(df_pedidos_reordered)
        else:
            st.info("No hay datos en la colección 'pedidos'.")
        
        st.subheader("Colección 'gastos'")
        st.dataframe(df_gastos)
        st.subheader("Colección 'totales'")
        st.dataframe(df_totales)
        st.subheader("Colección 'listas'")
        st.dataframe(df_listas)
        st.subheader("Colección 'trabajos'")
        st.dataframe(df_trabajos)

    elif page == "Pedidos":
        show_pedidos_page(df_pedidos, df_listas)

    elif page == "Gastos":
        show_gastos_page(df_gastos)

    elif page == "Resumen":
        show_resumen_page(df_pedidos, st.session_state.current_summary_view)

    elif page == "Restaurar Backup":
        show_restore_page()

    elif page == "Configurar Backup":
        st.header("Configurar Backup Automático")
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
            schedule_backup()
            st.success("✅ Configuración guardada y programada.")