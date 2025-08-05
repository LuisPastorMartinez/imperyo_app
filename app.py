import streamlit as st
import pandas as pd
import hashlib
from utils.firestore_utils import (
    load_dataframes_firestore,
    save_dataframe_firestore,
    delete_document_firestore,
    get_next_id
)

# =============================================
# CONFIGURACIÓN INICIAL
# =============================================
st.set_page_config(
    page_title="ImperYo App",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# ESTILOS CSS
# =============================================
st.markdown("""
<style>
    .green-bg { background-color: #00B050 !important; }
    .blue-bg { background-color: #0070C0 !important; }
    .yellow-bg { background-color: #FFC000 !important; }
    .pink-bg { background-color: #FF00FF !important; }
    .stDataFrame { font-size: 14px; }
    .stAlert { padding: 20px; }
</style>
""", unsafe_allow_html=True)

# =============================================
# FUNCIONES AUXILIARES
# =============================================
def apply_row_colors(df):
    """Aplica colores a las filas según estados"""
    styled_df = df.copy()
    for idx, row in df.iterrows():
        color = ''
        try:
            if all([row['Trabajo Terminado'], row['Cobrado'], row['Retirado']]) and not row['Pendiente']:
                color = 'green-bg'
            elif row['Inicio Trabajo'] and not row['Pendiente']:
                color = 'blue-bg'
            elif row['Trabajo Terminado'] and not row['Pendiente']:
                color = 'yellow-bg'
            elif row['Pendiente']:
                color = 'pink-bg'
        except KeyError:
            continue
        
        if color:
            styled_df.loc[idx] = [f'<div class="{color}">{x}</div>' if pd.notna(x) else '' for x in row]
    
    return styled_df

def check_password():
    """Autenticación segura"""
    if "auth" not in st.session_state:
        st.session_state.auth = False
        
    if not st.session_state.auth:
        with st.form("login"):
            user = st.text_input("Usuario")
            pwd = st.text_input("Contraseña", type="password")
            
            if st.form_submit_button("Ingresar"):
                try:
                    if (user == st.secrets["auth"]["username"] and 
                        hashlib.sha256(pwd.encode()).hexdigest() == st.secrets["auth"]["password_hash"]):
                        st.session_state.auth = True
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas")
                except Exception:
                    st.error("Error de configuración")
        return False
    return True

# =============================================
# VISTAS PRINCIPALES
# =============================================
def view_home():
    st.header("🏠 Panel Principal")
    st.metric("Total Pedidos", len(st.session_state.data['df_pedidos']))

def view_pedidos():
    st.header("📦 Gestión de Pedidos")
    tab1, tab2, tab3 = st.tabs(["Nuevo", "Editar", "Eliminar"])
    
    with tab1:
        with st.form("nuevo_pedido"):
            # Formulario de creación
            next_id = get_next_id(st.session_state.data['df_pedidos'], 'ID')
            st.write(f"ID del Pedido: **{next_id}**")
            
            # Campos del formulario...
            submitted = st.form_submit_button("Guardar")
            if submitted:
                # Lógica para guardar
                pass

def view_resumen():
    st.header("📊 Resumen de Pedidos")
    
    view_options = {
        "Todos": None,
        "En Progreso": "Inicio Trabajo",
        "Terminados": "Trabajo Terminado",
        "Pendientes": "Pendiente"
    }
    
    selected = st.selectbox("Filtrar por:", list(view_options.keys()))
    
    if view_options[selected]:
        filtered = st.session_state.data['df_pedidos'][st.session_state.data['df_pedidos'][view_options[selected]]]
    else:
        filtered = st.session_state.data['df_pedidos']
    
    if not filtered.empty:
        st.write(apply_row_colors(filtered).to_html(escape=False), unsafe_allow_html=True)
    else:
        st.warning(f"No hay pedidos {selected.lower()}")

# =============================================
# ESTRUCTURA PRINCIPAL
# =============================================
if check_password():
    # Carga de datos
    if 'data' not in st.session_state:
        with st.spinner("Cargando datos..."):
            st.session_state.data = load_dataframes_firestore()
            if st.session_state.data is None:
                st.error("Error al cargar datos")
                st.stop()
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150", width=100)
        st.title("ImperYo App")
        
        page = st.radio("Navegación", ["Inicio", "Pedidos", "Gastos", "Resumen"])
        
        if st.button("🔒 Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()
    
    # Router de páginas
    if page == "Inicio":
        view_home()
    elif page == "Pedidos":
        view_pedidos()
    elif page == "Resumen":
        view_resumen()
