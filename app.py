import streamlit as st
import pandas as pd
import os
import hashlib
import re
import sys
from pathlib import Path
from datetime import datetime
import time
import threading

# --- IMPORTACIONES ADICIONALES PARA APSCHEDULER ---
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# --- IMPORTACIÓN DE FIRESTORE ---
from firebase_admin import firestore

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
from modules.config_page import show_config_page

# --- CONFIGURACIÓN BÁSICA DE LA PÁGINA ---
st.set_page_config(
    page_title="ImperYo",
    page_icon="https://www.dropbox.com/scl/fi/opp61pwyq2lxleaj3hxs3/Logo-Movil-e-instagran.png?rlkey=4cruzlufwlz9vfr2myezjkz1d&dl=1",
    layout="wide"
)

# --- CSS PERSONALIZADO MEJORADO PARA MÓVIL ---
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
    /* Botones más grandes en móvil */
    .stButton>button {
        font-size: 1.2em !important;
        padding: 12px 24px !important;
    }
    /* Inputs más grandes */
    input, select, textarea {
        font-size: 1.1em !important;
        padding: 10px !important;
    }
}
.telefono-input {
    font-family: monospace;
    letter-spacing: 0.1em;
}
/* Estilo para botones primarios */
.stButton>button {
    background-color: #2c3e50;
    color: white;
    border-radius: 8px;
    font-weight: bold;
}
.stButton>button:hover {
    background-color: #1a252f;
    color: #e0e0e0;
}
/* Estilo para métricas */
[data-testid="stMetricValue"] {
    font-size: 1.8em !important;
}
[data-testid="stMetricLabel"] {
    font-size: 1.1em !important;
}
/* Gráficos más responsivos */
.plotly-graph-div {
    width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

# --- FUNCIÓN PARA RENDERIZAR EL HEADER MEJORADO ---
def render_header():
    logo_url = "https://www.dropbox.com/scl/fi/opp61pwyq2lxleaj3hxs3/Logo-Movil-e-instagran.png?rlkey=4cruzlufwlz9vfr2myezjkz1d&dl=1"
    st.markdown(f"""
    <div style="display: flex; align-items: center; padding: 15px; border-radius: 12px; 
                background: linear-gradient(to right, #f8f9fa, #e9ecef); 
                box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px;">
        <img src="{logo_url}" width="80" style="margin-right: 25px; border-radius: 8px;">
        <div>
            <h1 style="margin: 0; color: #2c3e50; font-weight: 700;">Imperyo Sport</h1>
            <p style="margin: 0; color: #6c757d; font-size: 1.2em;">Gestión de Pedidos y Gastos</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- RENDERIZAR HEADER ---
render_header()

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

# --- LÓGICA DE AUTENTICACIÓN MEJORADA ---
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
        st.markdown("""
        <div style="text-align: center; padding: 30px; border-radius: 15px; 
                    background: #f8f9fa; box-shadow: 0 4px 12px rgba(0,0,0,0.08); 
                    margin: 20px auto; max-width: 400px;">
            <img src="https://www.dropbox.com/scl/fi/opp61pwyq2lxleaj3hxs3/Logo-Movil-e-instagran.png?rlkey=4cruzlufwlz9vfr2myezjkz1d&dl=1" 
                 width="100" style="margin-bottom: 20px; border-radius: 50%;">
            <h3>🔐 Iniciar Sesión</h3>
            <p style="color: #6c757d;">Por favor, ingresa tus credenciales para acceder al sistema.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.text_input("👤 Usuario", key="username_input", placeholder="Ingresa tu usuario")
        st.text_input("🔒 Contraseña", type="password", key="password_input", placeholder="Ingresa tu contraseña")
        
        st.button("🚀 Iniciar Sesión", on_click=authenticate_user, use_container_width=True)

        if st.session_state["login_attempted"] and not st.session_state["authenticated"]:
            st.error("❌ Usuario o contraseña incorrectos. Inténtalo de nuevo.")
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
        },
        "last_backup": None,
        "selected_year": 2025  # ← AÑADIDO: Año seleccionado por defecto
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # ✅ Cargar último backup desde Firestore
    if "last_backup" not in st.session_state or st.session_state.last_backup is None:
        try:
            db = firestore.client()
            doc = db.collection('config').document('backup').get()
            if doc.exists:
                st.session_state.last_backup = doc.to_dict().get('last_backup', None)
            else:
                st.session_state.last_backup = None
        except Exception as e:
            st.session_state.last_backup = None
            print(f"[INICIO] Error al cargar último backup: {e}")

# --- FUNCIÓN PARA PROGRAMAR BACKUP AUTOMÁTICO ---
def backup_job():
    """Función que se ejecuta en el scheduler de backup automático."""
    try:
        if 'data' not in st.session_state:
            print("[BACKUP AUTOMÁTICO] No hay datos en st.session_state")
            return

        success, result, upload_success, upload_error = backup_to_dropbox(st.session_state.data)
        if success and upload_success:
            print(f"[BACKUP AUTOMÁTICO] Éxito: {result}")
        else:
            print(f"[BACKUP AUTOMÁTICO] Error: {result or upload_error}")
    except Exception as e:
        print(f"[BACKUP AUTOMÁTICO] Excepción: {e}")

# --- INICIAR SCHEDULER EN BACKGROUND ---
def start_scheduler():
    if 'apscheduler_started' not in st.session_state:
        st.session_state.apscheduler_started = True
        scheduler = BackgroundScheduler()
        
        # Programar backup según configuración
        if st.session_state.backup_config["enabled"]:
            day = st.session_state.backup_config["day"].lower()
            time_str = st.session_state.backup_config["time"]
            hour, minute = time_str.split(":")
            
            # Mapeo de días para APScheduler
            day_map = {
                "monday": "mon",
                "tuesday": "tue",
                "wednesday": "wed",
                "thursday": "thu",
                "friday": "fri",
                "saturday": "sat",
                "sunday": "sun"
            }
            
            cron_day = day_map.get(day, "sun")
            trigger = CronTrigger(day_of_week=cron_day, hour=int(hour), minute=int(minute))
            scheduler.add_job(backup_job, trigger, id='backup_job', replace_existing=True)
            print(f"[SCHEDULER] Backup programado para {day} a las {time_str}")

        scheduler.start()
        st.session_state.scheduler = scheduler
        print("[SCHEDULER] Iniciado correctamente")

# --- LÓGICA PRINCIPAL DE LA APLICACIÓN ---
if check_password():
    init_session_state()
    start_scheduler()

    # --- CARGA Y CORRECCIÓN DE DATOS ---
    if not st.session_state.get('data_loaded', False):
        try:
            data = load_dataframes_firestore()
            if data is None:
                st.error("No se pudieron cargar los datos. Verifica la conexión a Firestore.")
                st.stop()

            st.session_state.data = data

            # ✅ AÑADIR CAMPO 'AÑO' SI NO EXISTE
            if 'df_pedidos' in st.session_state.data:
                df = st.session_state.data['df_pedidos']
                if 'Año' not in df.columns:
                    df['Año'] = 2025
                    df['Año'] = pd.to_numeric(df['Año'], errors='coerce').fillna(2025).astype('int64')
                    st.session_state.data['df_pedidos'] = df
                    if save_dataframe_firestore(df, 'pedidos'):
                        st.success("✅ Campo 'Año' añadido a los pedidos existentes.")
                    else:
                        st.error("❌ Error al guardar el campo 'Año' en Firestore.")

                st.session_state.data['df_pedidos'] = unificar_columnas(st.session_state.data['df_pedidos'])

            st.session_state.data_loaded = True
        except Exception as e:
            st.error(f"Error al cargar datos: {e}")
            st.stop()

    if 'data' not in st.session_state or st.session_state.data is None:
        st.error("No se cargaron los datos correctamente.")
        st.stop()

    # --- ✅ VALIDACIÓN CORREGIDA ---
    required_dfs = ['df_pedidos', 'df_gastos', 'df_totales', 'df_listas', 'df_trabajos']
    for df_name in required_dfs:
        if df_name not in st.session_state.data:
            st.error(f"Error: No se encontró el DataFrame '{df_name}' en los datos cargados.")
            st.write("🔍 Claves disponibles:", list(st.session_state.data.keys()))
            st.stop()

    # --- ASIGNAR DATAFRAMES ---
    df_pedidos = st.session_state.data['df_pedidos']
    df_gastos = st.session_state.data['df_gastos']
    df_totales = st.session_state.data['df_totales']
    df_listas = st.session_state.data['df_listas']
    df_trabajos = st.session_state.data['df_trabajos']

    # --- BOTÓN DE CERRAR SESIÓN MEJORADO ---
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Cerrar Sesión", type="primary", use_container_width=True):
        keys_to_clear = ["authenticated", "data_loaded", "login_attempted", "username_input", "password_input", "selected_year"]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        if 'data' in st.session_state:
            del st.session_state['data']
        if 'scheduler' in st.session_state:
            st.session_state.scheduler.shutdown()
            del st.session_state['scheduler']
        st.rerun()

    # --- NAVEGACIÓN MEJORADA ---
    st.sidebar.title("🧭 Navegación Principal")
    page = st.sidebar.radio(
        "Selecciona una sección:",
        ["Inicio", "Pedidos", "Gastos", "Resumen", "Ver Datos", "Configuración"],
        key="main_page_radio",
        index=0,
        help="Navega entre las diferentes secciones del sistema"
    )

    if 'current_summary_view' not in st.session_state:
        st.session_state.current_summary_view = "Todos los Pedidos"

    if page == "Resumen":
        with st.sidebar.expander("📊 Filtrar Resumen", expanded=True):
            selected_summary_view_in_expander = st.radio(
                "Ver por estado:",
                ["Todos los Pedidos", "Trabajos Empezados", "Trabajos Terminados", "Pedidos Pendientes", "Nuevos Pedidos"],
                key="summary_view_radio"
            )
            st.session_state.current_summary_view = selected_summary_view_in_expander

    # --- CONTENIDO DE LAS PÁGINAS ---
    if page == "Inicio":
        st.header("📊 Dashboard Ejecutivo - Imperyo Sport")
        st.write("---")

        # --- Selector de año ---
        if 'Año' in df_pedidos.columns:
            años_disponibles = sorted(df_pedidos['Año'].dropna().unique(), reverse=True)
            if not años_disponibles:
                años_disponibles = [2025]  # fallback
        else:
            años_disponibles = [2025]

        selected_year = st.selectbox(
            "📅 Selecciona el año para ver estadísticas:",
            options=años_disponibles,
            index=años_disponibles.index(st.session_state.selected_year) if st.session_state.selected_year in años_disponibles else 0,
            key="year_selector"
        )

        st.session_state.selected_year = selected_year

        # --- Filtrar pedidos por año seleccionado ---
        if 'Año' in df_pedidos.columns:
            df_filtrado = df_pedidos[df_pedidos['Año'] == selected_year].copy()
        else:
            df_filtrado = df_pedidos.copy()

        # --- Asegurar columnas necesarias ---
        if 'Estado' not in df_filtrado.columns:
            df_filtrado['Estado'] = 'Pendiente'
        if 'Precio' not in df_filtrado.columns:
            df_filtrado['Precio'] = 0
        if 'Fecha entrada' not in df_filtrado.columns:
              st.warning("⚠️ No se encontró la columna 'Fecha entrada'. Los gráficos de tendencias no estarán disponibles.")
            df_filtrado['Fecha entrada'] = pd.NaT

        # --- Contar por estados ---
        total_año = len(df_filtrado)
        total_nuevos = len(df_filtrado[df_filtrado['Estado'] == 'Nuevo'])
        total_empezados = len(df_filtrado[df_filtrado['Estado'] == 'Empezado'])
        total_pendientes = len(df_filtrado[df_filtrado['Estado'] == 'Pendiente'])
        total_terminados = len(df_filtrado[df_filtrado['Estado'] == 'Terminado'])

        # --- Mostrar KPIs en columnas ---
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: st.metric(f"📆 {selected_year} Total", total_año)
        with col2: st.metric("🆕 Nuevos", total_nuevos)
        with col3: st.metric("🔄 Empezados", total_empezados)
        with col4: st.metric("⏳ Pendientes", total_pendientes)
        with col5: st.metric("✅ Terminados", total_terminados)

        st.write("---")

        # --- GRÁFICOS DE TENDENCIAS ---
        st.subheader("📈 Tendencias Mensuales")

        if pd.api.types.is_datetime64_any_dtype(df_filtrado['Fecha entrada']):
            df_filtrado['Mes'] = df_filtrado['Fecha entrada'].dt.month
            df_filtrado['MesNombre'] = df_filtrado['Fecha entrada'].dt.strftime('%B')

            # Pedidos por mes
            pedidos_por_mes = df_filtrado.groupby('MesNombre').size().reindex([
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ], fill_value=0)

            # Ingresos por mes
            df_filtrado['Precio'] = pd.to_numeric(df_filtrado['Precio'], errors='coerce').fillna(0)
            ingresos_por_mes = df_filtrado.groupby('MesNombre')['Precio'].sum().reindex([
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ], fill_value=0)

            # Convertir índices a español
            meses_es = {
                'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo', 'April': 'Abril',
                'May': 'Mayo', 'June': 'Junio', 'July': 'Julio', 'August': 'Agosto',
                'September': 'Septiembre', 'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
            }
            pedidos_por_mes.index = pedidos_por_mes.index.map(meses_es)
            ingresos_por_mes.index = ingresos_por_mes.index.map(meses_es)

            # Mostrar gráficos con Plotly
            import plotly.express as px

            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                fig1 = px.bar(
                    x=pedidos_por_mes.index,
                    y=pedidos_por_mes.values,
                    labels={'x': 'Mes', 'y': 'Cantidad de Pedidos'},
                    title="📦 Pedidos por Mes",
                    color_discrete_sequence=['#2c3e50']
                )
                fig1.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig1, use_container_width=True)

            with col_chart2:
                fig2 = px.bar(
                    x=ingresos_por_mes.index,
                    y=ingresos_por_mes.values,
                    labels={'x': 'Mes', 'y': 'Ingresos ($)'}, 
                    title="💰 Ingresos por Mes",
                    color_discrete_sequence=['#27ae60']
                )
                fig2.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig2, use_container_width=True)

        else:
            st.warning("⚠️ Las fechas no están en formato válido. No se pueden mostrar gráficos de tendencias.")

        st.write("---")
        st.subheader(f"📅 Últimos 5 Pedidos ({selected_year})")
        if not df_filtrado.empty:
            df_ultimos = df_filtrado.sort_values('ID', ascending=False).head(5)
            for _, row in df_ultimos.iterrows():
                cliente = row.get('Cliente', 'N/A')
                producto = row.get('Producto', 'N/A')
                fecha_entrada = row.get('Fecha entrada', 'N/A')
                estado = row.get('Estado', 'N/A')
                st.markdown(f"**ID {row['ID']}** — {cliente} — {producto} — 📅 {fecha_entrada} — 🏷️ *{estado}*")
        else:
            st.info(f"No hay pedidos registrados en {selected_year} aún.")

    elif page == "Ver Datos":
        st.header("🗃️ Datos Cargados de Firestore")
        st.subheader("Colección 'pedidos'")
        if not df_pedidos.empty:
            df_pedidos_sorted = df_pedidos.sort_values(by='ID', ascending=False)
            new_column_order = [
                'ID', 'Producto', 'Cliente', 'Club', 'Telefono', 'Breve Descripción',
                'Fecha entrada', 'Fecha Salida', 'Precio', 'Precio Factura',
                'Tipo de pago', 'Adelanto', 'Observaciones', 'Año', 'Estado'
            ]
            existing_columns = [col for col in new_column_order if col in df_pedidos_sorted.columns]
            remaining_columns = [col for col in df_pedidos_sorted.columns if col not in existing_columns]
            final_column_order = existing_columns + remaining_columns
            df_pedidos_reordered = df_pedidos_sorted[final_column_order]
            st.dataframe(df_pedidos_reordered, use_container_width=True)
        else:
            st.info("No hay datos en la colección 'pedidos'.")
        
        st.subheader("Colección 'gastos'")
        st.dataframe(df_gastos, use_container_width=True)
        st.subheader("Colección 'totales'")
        st.dataframe(df_totales, use_container_width=True)
        st.subheader("Colección 'listas'")
        st.dataframe(df_listas, use_container_width=True)
        st.subheader("Colección 'trabajos'")
        st.dataframe(df_trabajos, use_container_width=True)

    elif page == "Pedidos":
        show_pedidos_page(df_pedidos, df_listas)

    elif page == "Gastos":
        show_gastos_page(df_gastos)

    elif page == "Resumen":
        show_resumen_page(df_pedidos, st.session_state.current_summary_view)

    elif page == "Configuración":
        show_config_page()