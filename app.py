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
    /* Estilo para campos obligatorios */
    .required-field label:after { content: " *"; color: red; }
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
    df_pedidos = st.session_state.data['df_pedidos'].sort_values('ID', ascending=False)
    st.metric("Total Pedidos", len(df_pedidos))
    st.write("Últimos 5 pedidos:")
    st.dataframe(df_pedidos.head()[['ID', 'Cliente', 'Producto', 'Fecha Entrada']])

def view_pedidos():
    st.header("📦 Gestión de Pedidos")
    tab1, tab2, tab3 = st.tabs(["Nuevo Pedido", "Editar", "Buscar"])
    
    with tab1:
        with st.form("nuevo_pedido", clear_on_submit=True):
            st.subheader("Nuevo Pedido")
            
            # Generar ID automático
            next_id = get_next_id(st.session_state.data['df_pedidos'], 'ID')
            
            # --- PRIMERA FILA ---
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.text_input("ID", value=next_id, disabled=True)
            with col2:
                cliente = st.text_input("Cliente", key="n_cliente", help="Nombre completo del cliente")
            with col3:
                telefono = st.text_input("Teléfono", key="n_telefono")
            with col4:
                producto = st.selectbox(
                    "Producto",
                    options=st.session_state.data['df_listas']['Producto'].dropna().unique(),
                    key="n_producto"
                )
            
            # --- SEGUNDA FILA ---
            col5, col6, col7, col8 = st.columns(4)
            with col5:
                club = st.text_input("Club", key="n_club")
            with col6:
                talla = st.selectbox(
                    "Talla",
                    options=st.session_state.data['df_listas']['Talla'].dropna().unique(),
                    key="n_talla"
                )
            with col7:
                tela = st.selectbox(
                    "Tela",
                    options=st.session_state.data['df_listas']['Tela'].dropna().unique(),
                    key="n_tela"
                )
            with col8:
                breve_desc = st.text_input("Descripción breve", key="n_desc")
            
            # --- TERCERA FILA ---
            col9, col10, col11, col12 = st.columns(4)
            with col9:
                fecha_entrada = st.date_input("Fecha Entrada", key="n_fecha_entrada")
            with col10:
                fecha_salida = st.date_input("Fecha Salida", key="n_fecha_salida")
            with col11:
                precio = st.number_input("Precio", min_value=0.0, format="%.2f", key="n_precio")
            with col12:
                precio_factura = st.number_input("Precio Factura", min_value=0.0, format="%.2f", key="n_precio_factura")
            
            # --- CUARTA FILA ---
            col13, col14 = st.columns([1, 3])
            with col13:
                tipo_pago = st.selectbox(
                    "Tipo de Pago",
                    options=st.session_state.data['df_listas']['Tipo de pago'].dropna().unique(),
                    key="n_tipo_pago"
                )
                adelanto = st.number_input("Adelanto", min_value=0.0, format="%.2f", key="n_adelanto")
            with col14:
                observaciones = st.text_area("Observaciones", height=100, key="n_observaciones")
            
            # --- QUINTA FILA (Estado) ---
            st.write("**Estado del Pedido:**")
            estado_cols = st.columns(5)
            with estado_cols[0]:
                empezado = st.checkbox("Empezado", key="n_empezado")
            with estado_cols[1]:
                terminado = st.checkbox("Terminado", key="n_terminado")
            with estado_cols[2]:
                cobrado = st.checkbox("Cobrado", key="n_cobrado")
            with estado_cols[3]:
                retirado = st.checkbox("Retirado", key="n_retirado")
            with estado_cols[4]:
                pendiente = st.checkbox("Pendiente", key="n_pendiente")
            
            if st.form_submit_button("💾 Guardar Pedido"):
                nuevo_pedido = {
                    'ID': next_id,
                    'Cliente': cliente,
                    'Teléfono': telefono,
                    'Producto': producto,
                    'Club': club,
                    'Talla': talla,
                    'Tela': tela,
                    'Breve Descripción': breve_desc,
                    'Fecha Entrada': fecha_entrada,
                    'Fecha Salida': fecha_salida if fecha_salida else None,
                    'Precio': precio,
                    'Precio Factura': precio_factura if precio_factura else None,
                    'Tipo de pago': tipo_pago,
                    'Adelanto': adelanto if adelanto else None,
                    'Observaciones': observaciones,
                    'Inicio Trabajo': empezado,
                    'Trabajo Terminado': terminado,
                    'Cobrado': cobrado,
                    'Retirado': retirado,
                    'Pendiente': pendiente
                }
                
                if save_dataframe_firestore(pd.DataFrame([nuevo_pedido]), 'pedidos'):
                    st.success("Pedido guardado correctamente!")
                    st.session_state.data['df_pedidos'] = load_dataframes_firestore()['df_pedidos']
                else:
                    st.error("Error al guardar el pedido")

def view_resumen():
    st.header("📊 Resumen de Pedidos")
    
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
        
        page = st.radio("Navegación", ["Inicio", "Pedidos", "Resumen"])
        
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