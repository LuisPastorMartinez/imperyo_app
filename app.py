import streamlit as st
import pandas as pd
import os
import hashlib # Para el hash de la contraseña

# Importar las funciones desde nuestro módulo de utilidades para Firestore
from utils.firestore_utils import load_dataframes_firestore, save_dataframe_firestore, delete_document_firestore, get_next_id

# --- CONFIGURACIÓN BÁSICA DE LA PÁGINA ---
# Configura el nombre de la página y el logo
st.set_page_config(
    page_title="ImperYo",  # El nombre que quieres para tu app en la pestaña del navegador/icono
    page_icon="https://www.dropbox.com/scl/fi/opp61pwyq2lxleaj3hxs3/Logo-Movil-e-instagran.png?rlkey=4cruzlufwlz9vfr2myezjkz1d&dl=1", # Tu logo de Dropbox
    layout="wide"
)

# --- CSS PERSONALIZADO PARA RESPONSIVIDAD ---
# Usamos st.markdown con unsafe_allow_html=True para inyectar estilos CSS
st.markdown("""
<style>
/* Estilos por defecto para pantallas grandes (PC) */
.stImage > img {
    max-width: 100px; /* Tamaño del logo en PC */
    height: auto;
}
h1 {
    font-size: 3em; /* Tamaño del título principal en PC */
}
h2 {
    font-size: 2.5em; /* Tamaño de los headers en PC */
}
/* Clases para mostrar/ocultar contenido */
.mobile-only {
    display: none; /* Oculto por defecto en PC */
}
.pc-only {
    display: block; /* Visible por defecto en PC */
}

/* Media Query para pantallas más pequeñas (móviles y tablets pequeñas) */
@media (max-width: 768px) { /* Se aplica cuando el ancho de la pantalla es 768px o menos */
    .stImage > img {
        max-width: 60px; /* Logo más pequeño en móvil */
    }
    h1 {
        font-size: 2em; /* Título principal más pequeño en móvil */
    }
    h2 {
        font-size: 1.5em; /* Headers más pequeños en móvil */
    }
    .mobile-only {
        display: block; /* Visible en móvil */
    }
    .pc-only {
        display: none; /* Oculto en móvil */
    }
}
</style>
""", unsafe_allow_html=True)

# --- HEADER CON LOGO Y TÍTULO ---
col_logo, col_title = st.columns([0.1, 0.9]) # Ajusta la proporción según sea necesario
with col_logo:
    # Tu logo de Dropbox con dl=1 para acceso directo
    st.image("https://www.dropbox.com/scl/fi/opp61pwyq2lxleaj3hxs3/Logo-Movil-e-instagran.png?rlkey=4cruzlufwlz9vfr2myezjkz1d&dl=1", width=80)
with col_title:
    st.header("Imperyo Sport - Gestión de Pedidos y Gastos")
# --- FIN HEADER ---

# --- FUNCIÓN DE COLOREADO DE FILAS ---
# Esta función aplica colores de fondo a las filas según el estado del pedido
def highlight_pedidos_rows(row):
    # Estilo por defecto (sin color)
    styles = [''] * len(row)

    # Obtener valores booleanos de la fila para mayor claridad.
    # IMPORTANTE: Estos nombres de columna deben coincidir EXACTAMENTE con los encabezados de tu colección 'pedidos' en Firestore.
    trabajo_terminado = row.get('Trabajo Terminado', False) # Usa .get() para evitar KeyError si la columna falta
    cobrado = row.get('Cobrado', False)
    retirado = row.get('Retirado', False)
    pendiente = row.get('Pendiente', False)
    empezado = row.get('Inicio Trabajo', False) # 'Inicio Trabajo' con I mayúscula

    # Aplicar condiciones en el mismo orden que tu código VBA
    # 1. Verde: Trabajo Terminado Y Cobrado Y Retirado Y NO Pendiente
    if trabajo_terminado and cobrado and retirado and not pendiente:
        styles = ['background-color: #00B050'] * len(row) # Verde (Excel ColorIndex 10)
    # 2. Azul: Empezado (Inicio Trabajo) Y NO Pendiente
    elif empezado and not pendiente:
        styles = ['background-color: #0070C0'] * len(row) # Azul (Excel ColorIndex 23)
    # 3. Amarillo: Trabajo Terminado Y NO Pendiente
    elif trabajo_terminado and not pendiente:
        styles = ['background-color: #FFC000'] * len(row) # Amarillo (Excel ColorIndex 6)
    # 4. Rosa: Pendiente
    elif pendiente:
        styles = ['background-color: #FF00FF'] * len(row) # Magenta (Excel ColorIndex 22, a menudo percibido como rosa)

    return styles

# --- LÓGICA DE AUTENTICACIÓN ---
def check_password():
    """Retorna `True` si el usuario ingresa la contraseña correcta."""

    # Obtener credenciales de Streamlit secrets
    try:
        correct_username = st.secrets["auth"]["username"]
        correct_password_hash = st.secrets["auth"]["password_hash"]
    except KeyError:
        st.error("Error de configuración: No se encontraron las credenciales de autenticación en secrets.toml. Asegúrate de que la sección '[auth]' esté configurada correctamente.")
        st.stop()

    # Inicializar estados de sesión si no están presentes
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "login_attempted" not in st.session_state: # Esto rastreará si se ha intentado iniciar sesión
        st.session_state["login_attempted"] = False
    if "username_input" not in st.session_state: # Para almacenar el valor del campo de usuario
        st.session_state["username_input"] = ""
    if "password_input" not in st.session_state: # Para almacenar el valor del campo de contraseña
        st.session_state["password_input"] = ""

    def authenticate_user():
        """Maneja la lógica de autenticación cuando se hace clic en el botón."""
        hashed_input_password = hashlib.sha256(st.session_state["password_input"].encode()).hexdigest()
        if st.session_state["username_input"] == correct_username and \
           hashed_input_password == correct_password_hash:
            st.session_state["authenticated"] = True
            st.session_state["login_attempted"] = False # Reiniciar en inicio de sesión exitoso
            # Limpiar campos de entrada después de un inicio de sesión exitoso para evitar que se vuelvan a mostrar
            st.session_state["username_input"] = ""
            st.session_state["password_input"] = ""
        else:
            st.session_state["authenticated"] = False
            st.session_state["login_attempted"] = True # Marcar que se hizo un intento y falló

    if not st.session_state["authenticated"]:
        # Usar claves separadas para los valores de entrada para evitar conflictos con on_change
        st.text_input("Usuario", key="username_input")
        st.text_input("Contraseña", type="password", key="password_input")
        
        st.button("Iniciar Sesión", on_click=authenticate_user) # Llamar a la nueva función de autenticación al hacer clic en el botón

        if st.session_state["login_attempted"] and not st.session_state["authenticated"]:
            st.error("Usuario o contraseña incorrectos.")
        return False
    else:
        return True

# --- LÓGICA PRINCIPAL DE LA APLICACIÓN (CONDICIONAL A LA AUTENTICACIÓN) ---
if check_password():
    # --- CARGA DE DATOS AL INICIO DE LA APLICACIÓN ---
    # Usamos st.session_state para almacenar los DataFrames. Esto es crucial en Streamlit
    # para que los datos persistan entre interacciones del usuario y no se recarguen de Firestore
    # en cada interacción de widget.
    if 'data_loaded' not in st.session_state:
        st.session_state.data = load_dataframes_firestore() # Usar la función de carga de Firestore
        st.session_state.data_loaded = True

    # Si la carga de datos falló (ej. conexión a Firestore o error de colección), detener la aplicación
    if st.session_state.data is None:
        st.stop()

    # Asignar DataFrames a variables más cortas para facilitar su uso
    df_pedidos = st.session_state.data['df_pedidos']
    df_gastos = st.session_state.data['df_gastos']
    df_totales = st.session_state.data['df_totales']
    df_listas = st.session_state.data['df_listas']
    df_trabajos = st.session_state.data['df_trabajos']

    # --- BOTÓN DE CERRAR SESIÓN ---
    st.sidebar.markdown("---")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["authenticated"] = False
        st.session_state["data_loaded"] = False # Reiniciar el estado de carga de datos
        st.session_state["login_attempted"] = False # Reiniciar el estado de intento de inicio de sesión al cerrar sesión
        st.session_state["username_input"] = "" # Limpiar campos de entrada al cerrar sesión
        st.session_state["password_input"] = "" # Limpiar campos de entrada al cerrar sesión
        st.rerun()

    # --- NAVEGACIÓN DE LA APLICACIÓN (BARRA LATERAL) ---
    st.sidebar.title("Navegación")
    # Usar un radio button para simular la selección de "páginas" o secciones
    page = st.sidebar.radio("Ir a:", ["Inicio", "Pedidos", "Gastos", "Resumen", "Ver Datos"], key="main_page_radio")

    # Inicializar estado de sesión para la vista de resumen si no está presente
    if 'current_summary_view' not in st.session_state:
        st.session_state.current_summary_view = "Todos los Pedidos" # Vista por defecto para el resumen

    # Sub-menú condicional para "Resumen de Pedidos por Estado" usando expander
    if page == "Resumen": # Cambiado de "Resumen de Estados de Pedidos"
        with st.sidebar.expander("Seleccionar Vista de Resumen", expanded=True): # Expandido por defecto cuando en esta página
            selected_summary_view_in_expander = st.radio(
                "Ver por categoría:",
                ["Todos los Pedidos", "Trabajos Empezados", "Trabajos Terminados", "Pedidos Pendientes", "Pedidos sin estado específico"],
                key="summary_view_radio"
            )
            st.session_state.current_summary_view = selected_summary_view_in_expander
    else:
        pass # No se necesita una acción explícita aquí para el estado del expander cuando la página cambia


    # --- CONTENIDO DE LAS PÁGINAS ---

    if page == "Inicio":
        st.header("Bienvenido a Imperyo Sport")
        # st.write("Usa la barra lateral para navegar entre las diferentes secciones de la aplicación.") # ELIMINADO
        st.write("---")
        st.subheader("Estado General de Pedidos")
        # Ejemplo: Mostrar un resumen rápido (ej. número total de pedidos)
        st.info(f"Total de Pedidos Registrados: **{len(df_pedidos)}**")
        # st.write("Para un resumen detallado por estado, ve a 'Resumen de Estados de Pedidos' en el menú lateral y selecciona una categoría.") # ELIMINADO


    elif page == "Ver Datos": # Cambiado de "Ver Todas las Hojas"
        st.header("Datos Cargados de Firestore") # Texto actualizado
        st.subheader("Colección 'pedidos'")
        # Aplicar la función de estilo al DataFrame 'Pedidos' con el nuevo orden
        if not df_pedidos.empty:
            # Ordenar primero el DataFrame por 'ID' de mayor a menor
            df_pedidos_sorted = df_pedidos.sort_values(by='ID', ascending=False)
            # Definir el nuevo orden de columnas solicitado
            new_column_order = [
                'ID', 'Producto', 'Cliente', 'Club', 'Teléfono', 'Breve Descripción',
                'Fecha Entrada', 'Fecha Salida', 'Precio', 'Precio Factura',
                'Tipo de pago', 'Adelanto', 'Observaciones'
            ]
            # Obtener las columnas restantes para añadirlas al final
            remaining_columns = [col for col in df_pedidos_sorted.columns if col not in new_column_order]
            # Combinar las listas para el orden final
            final_column_order = new_column_order + remaining_columns
            df_pedidos_reordered = df_pedidos_sorted[final_column_order]
            st.dataframe(df_pedidos_reordered.style.apply(highlight_pedidos_rows, axis=1))
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

    elif page == "Pedidos": # Cambiado de "Gestión de Pedidos"
        st.header("Gestión de Pedidos")

        # --- Pestañas para acciones (Guardar, Buscar, Modificar, Eliminar) ---
        tab_guardar, tab_buscar, tab_modificar, tab_eliminar = st.tabs(["Guardar Nuevo", "Buscar Pedido", "Modificar Pedido", "Eliminar Pedido"])

        with tab_guardar:
            st.subheader("Guardar Nuevo Pedido")
            # Generar un nuevo ID automáticamente usando la función de utilidad get_next_id
            # Asumiendo que la columna ID en tu colección 'pedidos' se llama 'ID'
            next_pedido_id = get_next_id(df_pedidos, 'ID')
            st.write(f"ID del Nuevo Pedido: **{next_pedido_id}**")

            # --- Campos del Formulario de Pedidos (replicando UserForm de VBA) ---
            # Usamos st.form para agrupar los campos de entrada y el botón de envío
            with st.form("form_guardar_pedido", clear_on_submit=True):
                col1, col2 = st.columns(2) # Dividir el formulario en dos columnas para mejor diseño

                with col1:
                    st.text_input("ID", value=next_pedido_id, key="new_id", disabled=True) # Campo ID deshabilitado
                    
                    # Obtener opciones únicas para 'Producto' del DataFrame 'Listas'
                    producto_options = [""] + df_listas['Producto'].dropna().unique().tolist() # Añadir cadena vacía
                    producto = st.selectbox("Producto", options=producto_options, key="new_producto", index=0) # Por defecto a vacío
                    
                    cliente = st.text_input("Cliente", key="new_cliente")
                    telefono = st.text_input("Teléfono", key="new_telefono")
                    club = st.text_input("Club", key="new_club")
                    
                    # Obtener opciones únicas para 'Talla' del DataFrame 'Listas'
                    talla_options = [""] + df_listas['Talla'].dropna().unique().tolist() # Añadir cadena vacía
                    talla = st.selectbox("Talla", options=talla_options, key="new_talla", index=0) # Por defecto a vacío
                    
                    # Obtener opciones únicas para 'Tela' del DataFrame 'Listas'
                    tela_options = [""] + df_listas['Tela'].dropna().unique().tolist() # Añadir cadena vacía
                    tela = st.selectbox("Tela", options=tela_options, key="new_tela", index=0) # Por defecto a vacío
                    
                    breve_descripcion = st.text_area("Breve Descripción", key="new_breve_descripcion")

                with col2:
                    # --- Fecha Entrada ---
                    fecha_entrada = st.date_input("Fecha Entrada", key="new_fecha_entrada")

                    # --- Fecha Salida: Siempre habilitada (sin restricciones) ---
                    fecha_salida = st.date_input(
                        "Fecha Salida",
                        key="new_fecha_salida",
                        value=None # Por defecto a None (vacío)
                    )
                    # --- Fin Fecha Salida ---
                    
                    precio = st.number_input("Precio", min_value=0.0, format="%.2f", key="new_precio")
                    precio_factura = st.number_input("Precio Factura", min_value=0.0, format="%.2f", key="new_precio_factura")
                    
                    # Obtener opciones únicas para 'Tipo de pago' del DataFrame 'Listas'
                    tipo_pago_options = [""] + df_listas['Tipo de pago'].dropna().unique().tolist() # Añadir cadena vacía
                    tipo_pago = st.selectbox("Tipo de Pago", options=tipo_pago_options, key="new_tipo_pago", index=0) # Por defecto a vacío
                    
                    # --- Adelanto: Ahora es un campo de texto para permitir vacío ---
                    adelanto_str = st.text_input("Adelanto (opcional)", key="new_adelanto_str")
                    # --- Fin Adelanto ---

                    observaciones = st.text_area("Observaciones", key="new_observaciones")

                st.write("---") # Separador visual antes de los checkboxes

                # --- Checkboxes para el estado del pedido (movidos al final del formulario y ordenados) ---
                st.write("**Estado del Pedido:**")
                # Usar st.columns para colocarlos en una sola fila
                col_chk1, col_chk2, col_chk3, col_chk4, col_chk5 = st.columns(5)
                with col_chk1:
                    ch_empezado = st.checkbox("Empezado", key="new_ch_empezado") # 1º Empezado
                with col_chk2:
                    ch_trabajo_terminado = st.checkbox("Trabajo Terminado", key="new_ch_trabajo_terminado") # 2º Trabajo Terminado
                with col_chk3:
                    ch