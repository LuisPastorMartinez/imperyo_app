import streamlit as st
import pandas as pd
import hashlib
from utils.firestore_utils import (
    load_dataframes_firestore,
    save_dataframe_firestore,
    delete_document_firestore,
    get_next_id
)

# Configuración inicial
st.set_page_config(
    page_title="ImperYo App",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS
st.markdown("""
<style>
    .green-bg { background-color: #00B050; }
    .blue-bg { background-color: #0070C0; }
    .yellow-bg { background-color: #FFC000; }
    .pink-bg { background-color: #FF00FF; }
    .dataframe { font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# Funciones auxiliares
def apply_row_colors(df):
    """Aplica colores a filas según estado"""
    df_sorted = df.sort_values('ID', ascending=True)  # Ordenar por ID
    styled_df = df_sorted.copy()
    
    for idx, row in df_sorted.iterrows():
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

# Vistas principales
def view_home():
    st.header("Panel Principal")
    df_pedidos = st.session_state.data['df_pedidos'].sort_values('ID', ascending=False)
    st.metric("Total Pedidos", len(df_pedidos))
    st.write("Últimos 5 pedidos:")
    st.dataframe(df_pedidos.head()[['ID', 'Cliente', 'Producto']])

def view_pedidos():
    st.header("Gestión de Pedidos")
    tab1, tab2, tab3 = st.tabs(["Nuevo Pedido", "Editar", "Buscar"])
    
    with tab1:
        with st.form("nuevo_pedido", clear_on_submit=True):
            st.subheader("Nuevo Pedido")
            
            # Generar ID automático
            next_id = get_next_id(st.session_state.data['df_pedidos'], 'ID')
            st.info(f"ID del Pedido: {next_id}")
            
            # Campos del formulario completo
            col1, col2 = st.columns(2)
            
            with col1:
                cliente = st.text_input("Cliente*", key="nuevo_cliente")
                telefono = st.text_input("Teléfono", key="nuevo_telefono")
                producto = st.selectbox(
                    "Producto*", 
                    options=st.session_state.data['df_listas']['Producto'].unique(),
                    key="nuevo_producto"
                )
                talla = st.selectbox(
                    "Talla",
                    options=st.session_state.data['df_listas']['Talla'].unique(),
                    key="nuevo_talla"
                )
                
            with col2:
                tela = st.selectbox(
                    "Tela",
                    options=st.session_state.data['df_listas']['Tela'].unique(),
                    key="nuevo_tela"
                )
                precio = st.number_input("Precio*", min_value=0.0, key="nuevo_precio")
                fecha_entrada = st.date_input("Fecha Entrada*", key="nuevo_fecha_entrada")
            
            # Campos adicionales
            observaciones = st.text_area("Observaciones", key="nuevo_observaciones")
            
            # Estado del pedido
            st.markdown("**Estado del Pedido*")
            estado_cols = st.columns(5)
            with estado_cols[0]:
                empezado = st.checkbox("Empezado", key="nuevo_empezado")
            with estado_cols[1]:
                terminado = st.checkbox("Terminado", key="nuevo_terminado")
            with estado_cols[2]:
                cobrado = st.checkbox("Cobrado", key="nuevo_cobrado")
            with estado_cols[3]:
                retirado = st.checkbox("Retirado", key="nuevo_retirado")
            with estado_cols[4]:
                pendiente = st.checkbox("Pendiente", key="nuevo_pendiente")
            
            if st.form_submit_button("Guardar Pedido"):
                if not cliente or not producto or not precio:
                    st.error("Los campos marcados con * son obligatorios")
                else:
                    # Crear nuevo registro
                    nuevo_pedido = {
                        'ID': next_id,
                        'Cliente': cliente,
                        'Teléfono': telefono,
                        'Producto': producto,
                        'Talla': talla,
                        'Tela': tela,
                        'Precio': precio,
                        'Fecha Entrada': fecha_entrada,
                        'Observaciones': observaciones,
                        'Inicio Trabajo': empezado,
                        'Trabajo Terminado': terminado,
                        'Cobrado': cobrado,
                        'Retirado': retirado,
                        'Pendiente': pendiente
                    }
                    
                    # Guardar en Firestore
                    if save_dataframe_firestore(
                        pd.DataFrame([nuevo_pedido]), 
                        'pedidos'
                    ):
                        st.success("Pedido guardado correctamente!")
                        st.session_state.data['df_pedidos'] = load_dataframes_firestore()['df_pedidos']
                    else:
                        st.error("Error al guardar el pedido")

def view_resumen():
    st.header("Resumen de Pedidos")
    
    # Ordenar siempre por ID de forma descendente
    df_pedidos = st.session_state.data['df_pedidos'].sort_values('ID', ascending=False)
    
    view_options = {
        "Todos": None,
        "En Progreso": "Inicio Trabajo",
        "Terminados": "Trabajo Terminado",
        "Pendientes": "Pendiente"
    }
    
    selected = st.selectbox("Filtrar por:", list(view_options.keys()))
    
    if view_options[selected]:
        filtered = df_pedidos[df_pedidos[view_options[selected]]]
    else:
        filtered = df_pedidos
    
    if not filtered.empty:
        st.write(
            apply_row_colors(filtered).to_html(escape=False), 
            unsafe_allow_html=True,
            height=600
        )
    else:
        st.warning(f"No hay pedidos {selected.lower()}")

# Estructura principal
if check_password():
    if 'data' not in st.session_state:
        with st.spinner("Cargando datos..."):
            st.session_state.data = load_dataframes_firestore()
            if st.session_state.data is None:
                st.error("Error al cargar datos")
                st.stop()
    
    with st.sidebar:
        st.title("Menú Principal")
        page = st.radio("Navegación", ["Inicio", "Pedidos", "Resumen"])
        
        if st.button("Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()
    
    if page == "Inicio":
        view_home()
    elif page == "Pedidos":
        view_pedidos()
    elif page == "Resumen":
        view_resumen()