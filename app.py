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
    
    # --- NUEVA CORRECCIÓN: Unificar columnas para mantener 'Telefono' y 'Fecha entrada' ---
    # Lógica de unificación para la columna 'Telefono'
    if 'Teléfono' in df_pedidos.columns and 'Telefono' in df_pedidos.columns:
        df_pedidos['Telefono'] = df_pedidos['Telefono'].fillna(df_pedidos['Teléfono'])
        df_pedidos = df_pedidos.drop(columns=['Teléfono'])
    elif 'Teléfono' in df_pedidos.columns and 'Telefono' not in df_pedidos.columns:
        df_pedidos = df_pedidos.rename(columns={'Teléfono': 'Telefono'})
    
    # Lógica de unificación para la columna 'Fecha entrada'
    if 'Fecha Entrada' in df_pedidos.columns and 'Fecha entrada' in df_pedidos.columns:
        df_pedidos['Fecha entrada'] = df_pedidos['Fecha entrada'].fillna(df_pedidos['Fecha Entrada'])
        df_pedidos = df_pedidos.drop(columns=['Fecha Entrada'])
    elif 'Fecha Entrada' in df_pedidos.columns and 'Fecha entrada' not in df_pedidos.columns:
        df_pedidos = df_pedidos.rename(columns={'Fecha Entrada': 'Fecha entrada'})

    # Actualizar el DataFrame en el estado de sesión después de las correcciones
    st.session_state.data['df_pedidos'] = df_pedidos
        
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
                'ID', 'Producto', 'Cliente', 'Club', 'Telefono', 'Breve Descripción',
                'Fecha entrada', 'Fecha Salida', 'Precio', 'Precio Factura',
                'Tipo de pago', 'Adelanto', 'Observaciones'
            ]
            # Obtener las columnas restantes para añadirlas al final
            # Asegurarse de que no haya duplicados en la lista final
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
                    telefono = st.text_input("Telefono", key="new_telefono")
                    club = st.text_input("Club", key="new_club")
                    
                    # Obtener opciones únicas para 'Talla' del DataFrame 'Listas'
                    talla_options = [""] + df_listas['Talla'].dropna().unique().tolist() # Añadir cadena vacía
                    talla = st.selectbox("Talla", options=talla_options, key="new_talla", index=0) # Por defecto a vacío
                    
                    # Obtener opciones únicas para 'Tela' del DataFrame 'Listas'
                    tela_options = [""] + df_listas['Tela'].dropna().unique().tolist() # Añadir cadena vacía
                    tela = st.selectbox("Tela", options=tela_options, key="new_tela", index=0) # Por defecto a vacío
                    
                    breve_descripcion = st.text_area("Breve Descripción", key="new_breve_descripcion")

                with col2:
                    # --- Fecha entrada ---
                    fecha_entrada = st.date_input("Fecha entrada", key="new_fecha_entrada")

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
                    ch_cobrado = st.checkbox("Cobrado", key="new_ch_cobrado") # 3º Cobrado
                with col_chk4:
                    ch_retirado = st.checkbox("Retirado", key="new_ch_retirado") # 4º Retirado
                with col_chk5:
                    ch_pendiente = st.checkbox("Pendiente", key="new_ch_pendiente") # 5º Pendiente
                # --- Fin Checkboxes ---

                # Botón de envío del formulario
                submitted = st.form_submit_button("Guardar Pedido")

                if submitted:
                    # --- VALIDACIÓN: Empezado y Trabajo Terminado no pueden estar marcados a la vez ---
                    if ch_empezado and ch_trabajo_terminado:
                        st.error("Error: Un pedido no puede estar 'Empezado' y 'Trabajo Terminado' al mismo tiempo. Por favor, corrige los checkboxes.")
                        st.stop() # Detiene la ejecución para que el usuario corrija
                    # --- FIN VALIDACIÓN ---

                    # --- Conversión de Adelanto de string a float o None ---
                    adelanto = None
                    if adelanto_str: # Si el campo no está vacío
                        try:
                            adelanto = float(adelanto_str)
                        except ValueError:
                            st.error("Por favor, introduce un número válido para 'Adelanto' o déjalo vacío.")
                            st.stop() # Detener la ejecución si hay un error de conversión
                    # --- Fin Conversión Adelanto ---

                    # Crear un nuevo registro (fila) como un diccionario
                    new_record = {
                        'ID': next_pedido_id,
                        'Producto': producto if producto != "" else None, # Guardar None si se selecciona cadena vacía
                        'Cliente': cliente,
                        'Telefono': telefono,
                        'Club': club,
                        'Talla': talla if talla != "" else None, # Guardar None si se selecciona cadena vacía
                        'Tela': tela if tela != "" else None, # Guardar None si se selecciona cadena vacía
                        'Breve Descripción': breve_descripcion,
                        'Fecha entrada': fecha_entrada,
                        'Fecha Salida': fecha_salida, # Siempre se guarda el valor seleccionado (o None)
                        'Precio': precio,
                        'Precio Factura': precio_factura,
                        'Tipo de pago': tipo_pago if tipo_pago != "" else None, # Nombre de columna para guardar
                        'Adelanto': adelanto, # Puede ser None
                        'Observaciones': observaciones,
                        'Inicio Trabajo': ch_empezado, # Nombre de columna para guardar
                        'Cobrado': ch_cobrado,
                        'Retirado': ch_retirado,
                        'Pendiente': ch_pendiente,
                        'Trabajo Terminado': ch_trabajo_terminado
                    }

                    # Convertir el diccionario del nuevo registro a un DataFrame de una sola fila
                    new_df_row = pd.DataFrame([new_record])

                    # Añadir la nueva fila al DataFrame 'pedidos' existente en el estado de sesión
                    st.session_state.data['df_pedidos'] = pd.concat([df_pedidos, new_df_row], ignore_index=True)

                    # Guardar el DataFrame 'pedidos' actualizado de vuelta a Firestore
                    if save_dataframe_firestore(st.session_state.data['df_pedidos'], 'pedidos'): # Usar la función de guardado de Firestore
                        st.success(f"Pedido {next_pedido_id} guardado con éxito!")
                        st.rerun()
                    else:
                        st.error("Error al guardar el pedido.")

        with tab_buscar:
            st.subheader("Buscar Pedido") # Título más conciso
            search_id = st.number_input("Introduce el ID del pedido:", min_value=1, value=1, key="search_id_input_tab")
            if st.button("Buscar", key="search_button_tab"):
                found_pedido = df_pedidos[df_pedidos['ID'] == search_id]
                if not found_pedido.empty:
                    st.success(f"Pedido {search_id} encontrado:")
                    # Definir el nuevo orden de columnas solicitado
                    new_column_order = [
                        'ID', 'Producto', 'Cliente', 'Club', 'Telefono', 'Breve Descripción',
                        'Fecha entrada', 'Fecha Salida', 'Precio', 'Precio Factura',
                        'Tipo de pago', 'Adelanto', 'Observaciones'
                    ]
                    # Obtener las columnas restantes para añadirlas al final
                    remaining_columns = [col for col in found_pedido.columns if col not in new_column_order]
                    # Combinar las listas para el orden final
                    final_column_order = new_column_order + remaining_columns
                    found_pedido_reordered = found_pedido[final_column_order]
                    st.dataframe(found_pedido_reordered.style.apply(highlight_pedidos_rows, axis=1))
                else:
                    st.warning(f"No se encontró ningún pedido con el ID {search_id}.")

        with tab_modificar:
            st.subheader("Modificar Pedido") # Título más conciso

            # Campo de entrada para el ID a buscar
            modify_search_id = st.number_input("Introduce el ID del pedido a modificar:", min_value=1, value=st.session_state.get('last_searched_modify_id', 1), key="modify_search_id_input")
            
            # Botón para buscar el pedido
            if st.button("Buscar para Modificar", key="modify_search_button"): # Texto del botón más conciso
                found_pedido_row = df_pedidos[df_pedidos['ID'] == modify_search_id]
                if not found_pedido_row.empty:
                    st.session_state.modifying_pedido = found_pedido_row.iloc[0].to_dict() # Almacenar como diccionario para fácil acceso
                    st.session_state.last_searched_modify_id = modify_search_id # Almacenar para persistencia
                    st.success(f"Pedido {modify_search_id} encontrado. Modifica a continuación.") # Mensaje más conciso
                else:
                    st.session_state.modifying_pedido = None
                    st.session_state.last_searched_modify_id = modify_search_id
                    st.warning(f"No se encontró ningún pedido con el ID {modify_search_id}.")
            
            # Mostrar el formulario solo si se selecciona un pedido para modificar
            if st.session_state.get('modifying_pedido'):
                current_pedido = st.session_state.modifying_pedido
                st.write(f"Modificando Pedido ID: **{current_pedido['ID']}**") # Mantener este mensaje claro

                with st.form("form_modificar_pedido", clear_on_submit=False): # No limpiar al enviar para modificación
                    col1_mod, col2_mod = st.columns(2)

                    with col1_mod:
                        st.text_input("ID", value=current_pedido['ID'], key="mod_id", disabled=True)
                        
                        producto_options = [""] + df_listas['Producto'].dropna().unique().tolist() # Añadir cadena vacía
                        # Encontrar el índice del producto actual en la lista de opciones, o por defecto al índice de cadena vacía
                        current_producto_val = current_pedido['Producto'] if pd.notna(current_pedido['Producto']) else ""
                        current_producto_idx = producto_options.index(current_producto_val) if current_producto_val in producto_options else 0
                        producto_mod = st.selectbox("Producto", options=producto_options, index=current_producto_idx, key="mod_producto")
                        
                        cliente_mod = st.text_input("Cliente", value=current_pedido['Cliente'], key="mod_cliente")
                        telefono_mod = st.text_input("Telefono", value=current_pedido['Telefono'] if 'Telefono' in current_pedido else "", key="mod_telefono")
                        club_mod = st.text_input("Club", value=current_pedido['Club'], key="mod_club")
                        
                        talla_options = [""] + df_listas['Talla'].dropna().unique().tolist() # Añadir cadena vacía
                        current_talla_val = current_pedido['Talla'] if pd.notna(current_pedido['Talla']) else ""
                        current_talla_idx = talla_options.index(current_talla_val) if current_talla_val in talla_options else 0
                        talla_mod = st.selectbox("Talla", options=talla_options, index=current_talla_idx, key="mod_talla")
                        
                        tela_options = [""] + df_listas['Tela'].dropna().unique().tolist() # Añadir cadena vacía
                        current_tela_val = current_pedido['Tela'] if pd.notna(current_pedido['Tela']) else ""
                        current_tela_idx = tela_options.index(current_tela_val) if current_tela_val in tela_options else 0
                        tela_mod = st.selectbox("Tela", options=tela_options, index=current_tela_idx, key="mod_tela")
                        
                        breve_descripcion_mod = st.text_area("Breve Descripción", value=current_pedido['Breve Descripción'], key="mod_breve_descripcion")

                    with col2_mod:
                        # Fecha entrada
                        # Convertir Timestamp de pandas a datetime.date si no es NaT
                        current_fecha_entrada = current_pedido['Fecha entrada'].date() if pd.notna(current_pedido['Fecha entrada']) else None
                        fecha_entrada_mod = st.date_input("Fecha entrada", value=current_fecha_entrada, key="mod_fecha_entrada")

                        # --- Fecha Salida: Siempre habilitada (sin restricciones) ---
                        current_fecha_salida = current_pedido['Fecha Salida'].date() if pd.notna(current_pedido['Fecha Salida']) else None
                        fecha_salida_mod = st.date_input(
                            "Fecha Salida",
                            key="mod_fecha_salida",
                            value=current_fecha_salida # Pre-llenar con el valor actual
                        )
                        # --- Fin Fecha Salida ---
                        
                        precio_mod = st.number_input("Precio", min_value=0.0, format="%.2f", value=float(current_pedido['Precio']) if pd.notna(current_pedido['Precio']) else 0.0, key="mod_precio")
                        precio_factura_mod = st.number_input("Precio Factura", min_value=0.0, format="%.2f", value=float(current_pedido['Precio Factura']) if pd.notna(current_pedido['Precio Factura']) else 0.0, key="mod_precio_factura")
                        
                        tipo_pago_options = [""] + df_listas['Tipo de pago'].dropna().unique().tolist() # Añadir cadena vacía
                        current_tipo_pago_val = current_pedido['Tipo de pago'] if pd.notna(current_pedido['Tipo de pago']) else ""
                        current_tipo_pago_idx = tipo_pago_options.index(current_tipo_pago_val) if current_tipo_pago_val in tipo_pago_options else 0
                        tipo_pago_mod = st.selectbox("Tipo de Pago", options=tipo_pago_options, index=current_tipo_pago_idx, key="mod_tipo_pago")
                        
                        adelanto_mod_str = st.text_input("Adelanto (opcional)", value=str(current_pedido['Adelanto']) if pd.notna(current_pedido['Adelanto']) else "", key="mod_adelanto_str")

                        observaciones_mod = st.text_area("Observaciones", value=current_pedido['Observaciones'], key="mod_observaciones")

                    st.write("---") # Separador visual antes de los checkboxes

                    # Checkboxes para el estado del pedido (movidos al final del formulario y ordenados)
                    st.write("**Estado del Pedido:**")
                    col_chk1_mod, col_chk2_mod, col_chk3_mod, col_chk4_mod, col_chk5_mod = st.columns(5)
                    with col_chk1_mod:
                        ch_empezado_mod = st.checkbox("Empezado", value=current_pedido['Inicio Trabajo'], key="mod_ch_empezado") # 1º Empezado
                    with col_chk2_mod:
                        ch_trabajo_terminado_mod = st.checkbox("Trabajo Terminado", value=current_pedido['Trabajo Terminado'], key="mod_ch_trabajo_terminado") # 2º Trabajo Terminado
                    with col_chk3_mod:
                        ch_cobrado_mod = st.checkbox("Cobrado", value=current_pedido['Cobrado'], key="mod_ch_cobrado") # 3º Cobrado
                    with col_chk4_mod:
                        ch_retirado_mod = st.checkbox("Retirado", value=current_pedido['Retirado'], key="mod_ch_retirado") # 4º Retirado
                    with col_chk5_mod:
                        ch_pendiente_mod = st.checkbox("Pendiente", value=current_pedido['Pendiente'], key="mod_ch_pendiente") # 5º Pendiente
                    
                    submitted_mod = st.form_submit_button("Guardar Cambios")

                    if submitted_mod:
                        # --- VALIDACIÓN: Empezado y Trabajo Terminado no pueden estar marcados a la vez ---
                        if ch_empezado_mod and ch_trabajo_terminado_mod:
                            st.error("Error: Un pedido no puede estar 'Empezado' y 'Trabajo Terminado' al mismo tiempo. Por favor, corrige los checkboxes.")
                            st.stop() # Detiene la ejecución para que el usuario corrija
                        # --- FIN VALIDACIÓN ---

                        # Convertir Adelanto de string a float o None
                        adelanto_mod = None
                        if adelanto_mod_str:
                            try:
                                adelanto_mod = float(adelanto_mod_str)
                            except ValueError:
                                st.error("Por favor, introduce un número válido para 'Adelanto' o déjalo vacío.")
                                st.stop()
                        
                        # Encontrar el índice de la fila a modificar
                        row_index = df_pedidos[df_pedidos['ID'] == current_pedido['ID']].index[0]

                        # Actualizar el DataFrame usando .loc para modificación directa de fila
                        st.session_state.data['df_pedidos'].loc[row_index] = {
                            'ID': current_pedido['ID'], # El ID permanece igual
                            'Producto': producto_mod if producto_mod != "" else None, # Guardar None si se selecciona cadena vacía
                            'Cliente': cliente_mod,
                            'Telefono': telefono_mod,
                            'Club': club_mod,
                            'Talla': talla_mod if talla_mod != "" else None, # Guardar None si se selecciona cadena vacía
                            'Tela': tela_mod if tela_mod != "" else None, # Guardar None si se selecciona cadena vacía
                            'Breve Descripción': breve_descripcion_mod,
                            'Fecha entrada': fecha_entrada_mod,
                            'Fecha Salida': fecha_salida_mod,
                            'Precio': precio_mod,
                            'Precio Factura': precio_factura_mod,
                            'Tipo de pago': tipo_pago_mod if tipo_pago_mod != "" else None, # Guardar None si se selecciona cadena vacía
                            'Adelanto': adelanto_mod,
                            'Observaciones': observaciones_mod,
                            'Inicio Trabajo': ch_empezado_mod,
                            'Cobrado': ch_cobrado_mod,
                            'Retirado': ch_retirado_mod,
                            'Pendiente': ch_pendiente_mod,
                            'Trabajo Terminado': ch_trabajo_terminado_mod
                        }

                        # Guardar el DataFrame actualizado de vuelta a Firestore
                        if save_dataframe_firestore(st.session_state.data['df_pedidos'], 'pedidos'): # Usar la función de guardado de Firestore
                            st.success(f"Pedido {current_pedido['ID']} modificado con éxito!")
                            st.session_state.modifying_pedido = None # Limpiar el pedido seleccionado después de la modificación
                            st.rerun()
                        else:
                            st.error("Error al modificar el pedido.")

        with tab_eliminar:
            st.subheader("Eliminar Pedido")
            st.write("Introduce el ID del pedido a eliminar:") # Mensaje más conciso

            # ID del Pedido a Eliminar: Ahora se inicializa vacío
            delete_id = st.number_input("ID del Pedido a Eliminar:", min_value=1, value=None, key="delete_id_input")

            # Verificar si el pedido existe antes de ofrecer la confirmación
            # Solo busca si se ha introducido un ID válido (no None y mayor que 0)
            pedido_a_eliminar = pd.DataFrame() # Inicializar como DataFrame vacío
            if delete_id is not None and delete_id > 0:
                pedido_a_eliminar = df_pedidos[df_pedidos['ID'] == delete_id]

            if not pedido_a_eliminar.empty:
                st.warning(f"¿Seguro que quieres eliminar el pedido con ID **{delete_id}**?") # Mensaje más conciso
                # Definir el nuevo orden de columnas solicitado
                new_column_order = [
                    'ID', 'Producto', 'Cliente', 'Club', 'Telefono', 'Breve Descripción',
                    'Fecha entrada', 'Fecha Salida', 'Precio', 'Precio Factura',
                    'Tipo de pago', 'Adelanto', 'Observaciones'
                ]
                # Obtener las columnas restantes para añadirlas al final
                remaining_columns = [col for col in pedido_a_eliminar.columns if col not in new_column_order]
                # Combinar las listas para el orden final
                final_column_order = new_column_order + remaining_columns
                pedido_a_eliminar_reordered = pedido_a_eliminar[final_column_order]
                # Mostrar el DataFrame reordenado
                st.dataframe(pedido_a_eliminar_reordered.style.apply(highlight_pedidos_rows, axis=1))

                col_confirm1, col_confirm2 = st.columns(2)
                with col_confirm1:
                    if st.button("Confirmar Eliminación", key="confirm_delete_button"):
                        # Realizar la eliminación
                        # Para Firestore, necesitamos el 'id_documento_firestore' real, no el 'ID' de tu tabla.
                        # Primero, obtenemos el 'id_documento_firestore' del pedido a eliminar
                        doc_id_to_delete = pedido_a_eliminar['id_documento_firestore'].iloc[0]
                        
                        if delete_document_firestore('pedidos', doc_id_to_delete): # Usar la función de eliminación de Firestore
                            st.success(f"Pedido {delete_id} eliminado con éxito de Firestore.")
                            st.rerun() # Actualizar la aplicación para mostrar el DataFrame actualizado
                        else:
                            st.error("Error al eliminar el pedido de Firestore.")
                with col_confirm2:
                    if st.button("Cancelar Eliminación", key="cancel_delete_button"):
                        st.info("Eliminación cancelada.")
                        st.rerun() # Recargar para limpiar la advertencia y el botón de confirmación
            elif delete_id is not None and delete_id > 0:
                st.info(f"No se encontró ningún pedido con el ID {delete_id} para eliminar.")

    elif page == "Gastos": # Cambiado de "Gestión de Gastos"
        st.header("Gestión de Gastos")
        st.write("Aquí puedes gestionar tus gastos.") # Mantenido este mensaje corto
        # Ejemplo: Mostrar el DataFrame de gastos
        st.subheader("Gastos Registrados")
        st.dataframe(df_gastos)

        # --- Formulario para añadir nuevo gasto ---
        st.subheader("Añadir Gasto") # Título más conciso
        with st.form("form_nuevo_gasto", clear_on_submit=True):
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                gasto_fecha = st.date_input("Fecha Gasto", key="gasto_fecha") # Texto más conciso
                gasto_concepto = st.text_input("Concepto", key="gasto_concepto")
            with col_g2:
                g