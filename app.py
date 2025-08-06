import streamlit as st
import pandas as pd
import os
import hashlib
import re
from utils.firestore_utils import load_dataframes_firestore, save_dataframe_firestore, delete_document_firestore, get_next_id

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
.telefono-input {
    font-family: monospace;
    letter-spacing: 0.1em;
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
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
col_logo, col_title = st.columns([0.1, 0.9])
with col_logo:
    st.image("https://www.dropbox.com/scl/fi/opp61pwyq2lxleaj3hxs3/Logo-Movil-e-instagran.png?rlkey=4cruzlufwlz9vfr2myezjkz1d&dl=1", width=80)
with col_title:
    st.header("Imperyo Sport - Gestión de Pedidos y Gastos")

# --- FUNCIÓN DE COLOREADO DE FILAS ---
def highlight_pedidos_rows(row):
    styles = [''] * len(row)
    trabajo_terminado = row.get('Trabajo Terminado', False)
    cobrado = row.get('Cobrado', False)
    retirado = row.get('Retirado', False)
    pendiente = row.get('Pendiente', False)
    empezado = row.get('Inicio Trabajo', False)

    if trabajo_terminado and cobrado and retirado and not pendiente:
        styles = ['background-color: #00B050'] * len(row)
    elif empezado and not pendiente:
        styles = ['background-color: #0070C0'] * len(row)
    elif trabajo_terminado and not pendiente:
        styles = ['background-color: #FFC000'] * len(row)
    elif pendiente:
        styles = ['background-color: #FF00FF'] * len(row)

    return styles

# --- FUNCIONES PARA TELÉFONOS ---
def limpiar_telefono(numero):
    """Convierte a string, elimina no-dígitos y devuelve 9 dígitos o None"""
    if pd.isna(numero) or numero == "":
        return None
    digitos = re.sub(r'[^0-9]', '', str(numero))
    return digitos[:9] if len(digitos) >= 9 else None

def validar_telefono(numero):
    """Valida que tenga exactamente 9 dígitos"""
    return bool(re.fullmatch(r'^[0-9]{9}$', str(numero)))

# --- FUNCIÓN PARA UNIFICAR COLUMNAS ---
def unificar_columnas(df):
    # Eliminar columnas problemáticas de teléfono
    for col in ['Teléfono', 'Telefono ']:
        if col in df.columns:
            df = df.drop(columns=[col])
    
    # Limpieza de teléfonos si existe la columna
    if 'Telefono' in df.columns:
        df['Telefono'] = df['Telefono'].apply(limpiar_telefono)
    
    # Unificación de otras columnas
    columnas_a_unificar = {
        'Fecha Entreda': 'Fecha entrada',
        'Precio factura': 'Precio Factura',
        'Obserbaciones': 'Observaciones',
        'Fecha salida': 'Fecha Salida',
        'Descripcion del Articulo': 'Breve Descripción'
    }
    
    for col_vieja, col_nueva in columnas_a_unificar.items():
        if col_vieja in df.columns:
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

# --- LÓGICA PRINCIPAL DE LA APLICACIÓN ---
if check_password():
    # --- CARGA Y CORRECCIÓN DE DATOS ---
    if 'data_loaded' not in st.session_state:
        st.session_state.data = load_dataframes_firestore()
        
        if 'df_pedidos' in st.session_state.data:
            st.session_state.data['df_pedidos'] = unificar_columnas(st.session_state.data['df_pedidos'])
        
        st.session_state.data_loaded = True

    if st.session_state.data is None:
        st.stop()
    
    # Asignar DataFrames
    df_pedidos = st.session_state.data['df_pedidos']
    df_gastos = st.session_state.data['df_gastos']
    df_totales = st.session_state.data['df_totales']
    df_listas = st.session_state.data['df_listas']
    df_trabajos = st.session_state.data['df_trabajos']
    
    # --- BOTÓN DE CERRAR SESIÓN ---
    st.sidebar.markdown("---")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["authenticated"] = False
        st.session_state["data_loaded"] = False
        st.session_state["login_attempted"] = False
        st.session_state["username_input"] = ""
        st.session_state["password_input"] = ""
        st.rerun()

    # --- NAVEGACIÓN ---
    st.sidebar.title("Navegación")
    page = st.sidebar.radio("Ir a:", ["Inicio", "Pedidos", "Gastos", "Resumen", "Ver Datos"], key="main_page_radio")

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
            remaining_columns = [col for col in df_pedidos_sorted.columns if col not in new_column_order]
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

    elif page == "Pedidos":
        st.header("Gestión de Pedidos")
        tab_guardar, tab_buscar, tab_modificar, tab_eliminar = st.tabs(["Guardar Nuevo", "Buscar Pedido", "Modificar Pedido", "Eliminar Pedido"])

        with tab_guardar:
            st.subheader("Guardar Nuevo Pedido")
            next_pedido_id = get_next_id(df_pedidos, 'ID')
            st.write(f"ID del Nuevo Pedido: **{next_pedido_id}**")

            with st.form("form_guardar_pedido", clear_on_submit=True):
                col1, col2 = st.columns(2)

                with col1:
                    st.text_input("ID", value=next_pedido_id, key="new_id", disabled=True)
                    producto_options = [""] + df_listas['Producto'].dropna().unique().tolist()
                    producto = st.selectbox("Producto", options=producto_options, key="new_producto", index=0)
                    cliente = st.text_input("Cliente", key="new_cliente")
                    
                    # Campo de teléfono con validación
                    telefono = st.text_input("Teléfono (9 dígitos)", 
                                           key="new_telefono",
                                           max_chars=9,
                                           help="Ejemplo: 622019738 (solo números, sin espacios ni guiones)")
                    
                    club = st.text_input("Club", key="new_club")
                    talla_options = [""] + df_listas['Talla'].dropna().unique().tolist()
                    talla = st.selectbox("Talla", options=talla_options, key="new_talla", index=0)
                    tela_options = [""] + df_listas['Tela'].dropna().unique().tolist()
                    tela = st.selectbox("Tela", options=tela_options, key="new_tela", index=0)
                    breve_descripcion = st.text_area("Breve Descripción", key="new_breve_descripcion")

                with col2:
                    fecha_entrada = st.date_input("Fecha entrada", key="new_fecha_entrada")
                    fecha_salida = st.date_input("Fecha Salida", key="new_fecha_salida", value=None)
                    precio = st.number_input("Precio", min_value=0.0, format="%.2f", key="new_precio")
                    precio_factura = st.number_input("Precio Factura", min_value=0.0, format="%.2f", key="new_precio_factura")
                    tipo_pago_options = [""] + df_listas['Tipo de pago'].dropna().unique().tolist()
                    tipo_pago = st.selectbox("Tipo de Pago", options=tipo_pago_options, key="new_tipo_pago", index=0)
                    adelanto_str = st.text_input("Adelanto (opcional)", key="new_adelanto_str")
                    observaciones = st.text_area("Observaciones", key="new_observaciones")

                st.write("---")
                st.write("**Estado del Pedido:**")
                col_chk1, col_chk2, col_chk3, col_chk4, col_chk5 = st.columns(5)
                with col_chk1:
                    ch_empezado = st.checkbox("Empezado", key="new_ch_empezado")
                with col_chk2:
                    ch_trabajo_terminado = st.checkbox("Trabajo Terminado", key="new_ch_trabajo_terminado")
                with col_chk3:
                    ch_cobrado = st.checkbox("Cobrado", key="new_ch_cobrado")
                with col_chk4:
                    ch_retirado = st.checkbox("Retirado", key="new_ch_retirado")
                with col_chk5:
                    ch_pendiente = st.checkbox("Pendiente", key="new_ch_pendiente")

                submitted = st.form_submit_button("Guardar Pedido")

                if submitted:
                    # Validar teléfono
                    telefono_ingresado = st.session_state.new_telefono.strip()
                    if telefono_ingresado:  # Solo validar si no está vacío
                        if not validar_telefono(telefono_ingresado):
                            st.error("ERROR: El teléfono debe contener exactamente 9 dígitos numéricos")
                            st.stop()
                        telefono_limpio = limpiar_telefono(telefono_ingresado)
                    else:
                        telefono_limpio = None

                    if ch_empezado and ch_trabajo_terminado:
                        st.error("Error: Un pedido no puede estar 'Empezado' y 'Trabajo Terminado' al mismo tiempo.")
                        st.stop()

                    adelanto = None
                    if adelanto_str:
                        try:
                            adelanto = float(adelanto_str)
                        except ValueError:
                            st.error("Por favor, introduce un número válido para 'Adelanto' o déjalo vacío.")
                            st.stop()

                    new_record = {
                        'ID': next_pedido_id,
                        'Producto': producto if producto != "" else None,
                        'Cliente': cliente,
                        'Telefono': telefono_limpio,
                        'Club': club,
                        'Talla': talla if talla != "" else None,
                        'Tela': tela if tela != "" else None,
                        'Breve Descripción': breve_descripcion,
                        'Fecha entrada': fecha_entrada,
                        'Fecha Salida': fecha_salida,
                        'Precio': precio,
                        'Precio Factura': precio_factura,
                        'Tipo de pago': tipo_pago if tipo_pago != "" else None,
                        'Adelanto': adelanto,
                        'Observaciones': observaciones,
                        'Inicio Trabajo': ch_empezado,
                        'Cobrado': ch_cobrado,
                        'Retirado': ch_retirado,
                        'Pendiente': ch_pendiente,
                        'Trabajo Terminado': ch_trabajo_terminado
                    }

                    new_df_row = pd.DataFrame([new_record])
                    st.session_state.data['df_pedidos'] = pd.concat([df_pedidos, new_df_row], ignore_index=True)

                    if save_dataframe_firestore(st.session_state.data['df_pedidos'], 'pedidos'):
                        st.success(f"Pedido {next_pedido_id} guardado con éxito!")
                        st.rerun()
                    else:
                        st.error("Error al guardar el pedido.")

        with tab_buscar:
            st.subheader("Buscar Pedido")
            search_id = st.number_input("Introduce el ID del pedido:", min_value=1, value=1, key="search_id_input_tab")
            if st.button("Buscar", key="search_button_tab"):
                found_pedido = df_pedidos[df_pedidos['ID'] == search_id]
                if not found_pedido.empty:
                    st.success(f"Pedido {search_id} encontrado:")
                    new_column_order = [
                        'ID', 'Producto', 'Cliente', 'Club', 'Telefono', 'Breve Descripción',
                        'Fecha entrada', 'Fecha Salida', 'Precio', 'Precio Factura',
                        'Tipo de pago', 'Adelanto', 'Observaciones'
                    ]
                    remaining_columns = [col for col in found_pedido.columns if col not in new_column_order]
                    final_column_order = new_column_order + remaining_columns
                    found_pedido_reordered = found_pedido[final_column_order]
                    st.dataframe(found_pedido_reordered.style.apply(highlight_pedidos_rows, axis=1))
                else:
                    st.warning(f"No se encontró ningún pedido con el ID {search_id}.")

        with tab_modificar:
            st.subheader("Modificar Pedido")
            modify_search_id = st.number_input("Introduce el ID del pedido a modificar:", min_value=1, value=st.session_state.get('last_searched_modify_id', 1), key="modify_search_id_input")
            
            if st.button("Buscar para Modificar", key="modify_search_button"):
                found_pedido_row = df_pedidos[df_pedidos['ID'] == modify_search_id]
                if not found_pedido_row.empty:
                    st.session_state.modifying_pedido = found_pedido_row.iloc[0].to_dict()
                    st.session_state.last_searched_modify_id = modify_search_id
                    st.success(f"Pedido {modify_search_id} encontrado. Modifica a continuación.")
                else:
                    st.session_state.modifying_pedido = None
                    st.session_state.last_searched_modify_id = modify_search_id
                    st.warning(f"No se encontró ningún pedido con el ID {modify_search_id}.")
            
            if st.session_state.get('modifying_pedido'):
                current_pedido = st.session_state.modifying_pedido
                st.write(f"Modificando Pedido ID: **{current_pedido['ID']}**")

                with st.form("form_modificar_pedido", clear_on_submit=False):
                    col1_mod, col2_mod = st.columns(2)

                    with col1_mod:
                        st.text_input("ID", value=current_pedido['ID'], key="mod_id", disabled=True)
                        producto_options = [""] + df_listas['Producto'].dropna().unique().tolist()
                        current_producto_val = current_pedido['Producto'] if pd.notna(current_pedido['Producto']) else ""
                        current_producto_idx = producto_options.index(current_producto_val) if current_producto_val in producto_options else 0
                        producto_mod = st.selectbox("Producto", options=producto_options, index=current_producto_idx, key="mod_producto")
                        cliente_mod = st.text_input("Cliente", value=current_pedido['Cliente'], key="mod_cliente")
                        
                        # Campo de teléfono con validación
                        telefono_actual = str(current_pedido.get('Telefono', '')).strip()
                        telefono_mod = st.text_input("Teléfono (9 dígitos)", 
                                                   value=telefono_actual,
                                                   key="mod_telefono",
                                                   max_chars=9,
                                                   help="Ejemplo: 622019738 (solo números)")
                        
                        club_mod = st.text_input("Club", value=current_pedido['Club'], key="mod_club")
                        talla_options = [""] + df_listas['Talla'].dropna().unique().tolist()
                        current_talla_val = current_pedido['Talla'] if pd.notna(current_pedido['Talla']) else ""
                        current_talla_idx = talla_options.index(current_talla_val) if current_talla_val in talla_options else 0
                        talla_mod = st.selectbox("Talla", options=talla_options, index=current_talla_idx, key="mod_talla")
                        tela_options = [""] + df_listas['Tela'].dropna().unique().tolist()
                        current_tela_val = current_pedido['Tela'] if pd.notna(current_pedido['Tela']) else ""
                        current_tela_idx = tela_options.index(current_tela_val) if current_tela_val in tela_options else 0
                        tela_mod = st.selectbox("Tela", options=tela_options, index=current_tela_idx, key="mod_tela")
                        breve_descripcion_mod = st.text_area("Breve Descripción", value=current_pedido['Breve Descripción'], key="mod_breve_descripcion")

                    with col2_mod:
                        current_fecha_entrada = current_pedido['Fecha entrada'].date() if pd.notna(current_pedido['Fecha entrada']) else None
                        fecha_entrada_mod = st.date_input("Fecha entrada", value=current_fecha_entrada, key="mod_fecha_entrada")
                        current_fecha_salida = current_pedido['Fecha Salida'].date() if pd.notna(current_pedido['Fecha Salida']) else None
                        fecha_salida_mod = st.date_input("Fecha Salida", key="mod_fecha_salida", value=current_fecha_salida)
                        precio_mod = st.number_input("Precio", min_value=0.0, format="%.2f", value=float(current_pedido['Precio']) if pd.notna(current_pedido['Precio']) else 0.0, key="mod_precio")
                        precio_factura_mod = st.number_input("Precio Factura", min_value=0.0, format="%.2f", value=float(current_pedido['Precio Factura']) if pd.notna(current_pedido['Precio Factura']) else 0.0, key="mod_precio_factura")
                        tipo_pago_options = [""] + df_listas['Tipo de pago'].dropna().unique().tolist()
                        current_tipo_pago_val = current_pedido['Tipo de pago'] if pd.notna(current_pedido['Tipo de pago']) else ""
                        current_tipo_pago_idx = tipo_pago_options.index(current_tipo_pago_val) if current_tipo_pago_val in tipo_pago_options else 0
                        tipo_pago_mod = st.selectbox("Tipo de Pago", options=tipo_pago_options, index=current_tipo_pago_idx, key="mod_tipo_pago")
                        adelanto_mod_str = st.text_input("Adelanto (opcional)", value=str(current_pedido['Adelanto']) if pd.notna(current_pedido['Adelanto']) else "", key="mod_adelanto_str")
                        observaciones_mod = st.text_area("Observaciones", value=current_pedido['Observaciones'], key="mod_observaciones")

                    st.write("---")
                    st.write("**Estado del Pedido:**")
                    col_chk1_mod, col_chk2_mod, col_chk3_mod, col_chk4_mod, col_chk5_mod = st.columns(5)
                    with col_chk1_mod:
                        ch_empezado_mod = st.checkbox("Empezado", value=current_pedido['Inicio Trabajo'], key="mod_ch_empezado")
                    with col_chk2_mod:
                        ch_trabajo_terminado_mod = st.checkbox("Trabajo Terminado", value=current_pedido['Trabajo Terminado'], key="mod_ch_trabajo_terminado")
                    with col_chk3_mod:
                        ch_cobrado_mod = st.checkbox("Cobrado", value=current_pedido['Cobrado'], key="mod_ch_cobrado")
                    with col_chk4_mod:
                        ch_retirado_mod = st.checkbox("Retirado", value=current_pedido['Retirado'], key="mod_ch_retirado")
                    with col_chk5_mod:
                        ch_pendiente_mod = st.checkbox("Pendiente", value=current_pedido['Pendiente'], key="mod_ch_pendiente")
                    
                    submitted_mod = st.form_submit_button("Guardar Cambios")

                    if submitted_mod:
                        # Validar teléfono
                        telefono_mod_ingresado = st.session_state.mod_telefono.strip()
                        if telefono_mod_ingresado:  # Solo validar si no está vacío
                            if not validar_telefono(telefono_mod_ingresado):
                                st.error("ERROR: El teléfono debe contener exactamente 9 dígitos numéricos")
                                st.stop()
                            telefono_limpio = limpiar_telefono(telefono_mod_ingresado)
                        else:
                            telefono_limpio = None

                        if ch_empezado_mod and ch_trabajo_terminado_mod:
                            st.error("Error: Un pedido no puede estar 'Empezado' y 'Trabajo Terminado' al mismo tiempo.")
                            st.stop()

                        adelanto_mod = None
                        if adelanto_mod_str:
                            try:
                                adelanto_mod = float(adelanto_mod_str)
                            except ValueError:
                                st.error("Por favor, introduce un número válido para 'Adelanto' o déjalo vacío.")
                                st.stop()
                        
                        row_index = df_pedidos[df_pedidos['ID'] == current_pedido['ID']].index[0]

                        st.session_state.data['df_pedidos'].loc[row_index] = {
                            'ID': current_pedido['ID'],
                            'Producto': producto_mod if producto_mod != "" else None,
                            'Cliente': cliente_mod,
                            'Telefono': telefono_limpio,
                            'Club': club_mod,
                            'Talla': talla_mod if talla_mod != "" else None,
                            'Tela': tela_mod if tela_mod != "" else None,
                            'Breve Descripción': breve_descripcion_mod,
                            'Fecha entrada': fecha_entrada_mod,
                            'Fecha Salida': fecha_salida_mod,
                            'Precio': precio_mod,
                            'Precio Factura': precio_factura_mod,
                            'Tipo de pago': tipo_pago_mod if tipo_pago_mod != "" else None,
                            'Adelanto': adelanto_mod,
                            'Observaciones': observaciones_mod,
                            'Inicio Trabajo': ch_empezado_mod,
                            'Cobrado': ch_cobrado_mod,
                            'Retirado': ch_retirado_mod,
                            'Pendiente': ch_pendiente_mod,
                            'Trabajo Terminado': ch_trabajo_terminado_mod
                        }

                        if save_dataframe_firestore(st.session_state.data['df_pedidos'], 'pedidos'):
                            st.success(f"Pedido {current_pedido['ID']} modificado con éxito!")
                            st.session_state.modifying_pedido = None
                            st.rerun()
                        else:
                            st.error("Error al modificar el pedido.")

        with tab_eliminar:
            st.subheader("Eliminar Pedido")
            st.write("Introduce el ID del pedido a eliminar:")
            delete_id = st.number_input("ID del Pedido a Eliminar:", min_value=1, value=None, key="delete_id_input")

            pedido_a_eliminar = pd.DataFrame()
            if delete_id is not None and delete_id > 0:
                pedido_a_eliminar = df_pedidos[df_pedidos['ID'] == delete_id]

            if not pedido_a_eliminar.empty:
                st.warning(f"¿Seguro que quieres eliminar el pedido con ID **{delete_id}**?")
                new_column_order = [
                    'ID', 'Producto', 'Cliente', 'Club', 'Telefono', 'Breve Descripción',
                    'Fecha entrada', 'Fecha Salida', 'Precio', 'Precio Factura',
                    'Tipo de pago', 'Adelanto', 'Observaciones'
                ]
                remaining_columns = [col for col in pedido_a_eliminar.columns if col not in new_column_order]
                final_column_order = new_column_order + remaining_columns
                pedido_a_eliminar_reordered = pedido_a_eliminar[final_column_order]
                st.dataframe(pedido_a_eliminar_reordered.style.apply(highlight_pedidos_rows, axis=1))

                col_confirm1, col_confirm2 = st.columns(2)
                with col_confirm1:
                    if st.button("Confirmar Eliminación", key="confirm_delete_button"):
                        doc_id_to_delete = pedido_a_eliminar['id_documento_firestore'].iloc[0]
                        if delete_document_firestore('pedidos', doc_id_to_delete):
                            st.success(f"Pedido {delete_id} eliminado con éxito de Firestore.")
                            st.rerun()
                        else:
                            st.error("Error al eliminar el pedido de Firestore.")
                with col_confirm2:
                    if st.button("Cancelar Eliminación", key="cancel_delete_button"):
                        st.info("Eliminación cancelada.")
                        st.rerun()
            elif delete_id is not None and delete_id > 0:
                st.info(f"No se encontró ningún pedido con el ID {delete_id} para eliminar.")

    elif page == "Gastos":
        st.header("Gestión de Gastos")
        st.write("Aquí puedes gestionar tus gastos.")
        st.subheader("Gastos Registrados")
        st.dataframe(df_gastos)

        st.subheader("Añadir Gasto")
        with st.form("form_nuevo_gasto", clear_on_submit=True):
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                gasto_fecha = st.date_input("Fecha Gasto", key="gasto_fecha")
                gasto_concepto = st.text_input("Concepto", key="gasto_concepto")
            with col_g2:
                gasto_importe = st.number_input("Importe", min_value=0.0, format="%.2f", key="gasto_importe")
                gasto_tipo = st.selectbox("Tipo Gasto", options=["", "Fijo", "Variable"], key="gasto_tipo")
            
            submitted_gasto = st.form_submit_button("Guardar Gasto")

            if submitted_gasto:
                next_gasto_id = get_next_id(df_gastos, 'ID')
                new_gasto_record = {
                    'ID': next_gasto_id,
                    'Fecha': gasto_fecha,
                    'Concepto': gasto_concepto,
                    'Importe': gasto_importe,
                    'Tipo': gasto_tipo if gasto_tipo != "" else None
                }
                new_gasto_df_row = pd.DataFrame([new_gasto_record])
                st.session_state.data['df_gastos'] = pd.concat([df_gastos, new_gasto_df_row], ignore_index=True)
                
                if save_dataframe_firestore(st.session_state.data['df_gastos'], 'gastos'):
                    st.success(f"Gasto {next_gasto_id} guardado con éxito!")
                    st.rerun()
                else:
                    st.error("Error al guardar el gasto.")

        st.subheader("Eliminar Gasto")
        delete_gasto_id = st.number_input("ID del Gasto a Eliminar:", min_value=1, value=None, key="delete_gasto_id_input")

        gasto_a_eliminar = pd.DataFrame()
        if delete_gasto_id is not None and delete_gasto_id > 0:
            gasto_a_eliminar = df_gastos[df_gastos['ID'] == delete_gasto_id]

        if not gasto_a_eliminar.empty:
            st.warning(f"¿Seguro que quieres eliminar el gasto con ID **{delete_gasto_id}**?")
            st.dataframe(gasto_a_eliminar)

            col_g_confirm1, col_g_confirm2 = st.columns(2)
            with col_g_confirm1:
                if st.button("Confirmar Eliminación Gasto", key="confirm_delete_gasto_button"):
                    doc_id_to_delete_gasto = gasto_a_eliminar['id_documento_firestore'].iloc[0]
                    if delete_document_firestore('gastos', doc_id_to_delete_gasto):
                        st.success(f"Gasto {delete_gasto_id} eliminado con éxito de Firestore.")
                        st.rerun()
                    else:
                        st.error("Error al eliminar el gasto de Firestore.")
            with col_g_confirm2:
                if st.button("Cancelar Eliminación Gasto", key="cancel_delete_gasto_button"):
                    st.info("Eliminación de gasto cancelada.")
                    st.rerun()
        elif delete_gasto_id is not None and delete_gasto_id > 0:
            st.info(f"No se encontró ningún gasto con el ID {delete_gasto_id} para eliminar.")

    elif page == "Resumen":
        st.header("Resumen de Pedidos")
        filtered_df = pd.DataFrame()

        if st.session_state.current_summary_view == "Todos los Pedidos":
            filtered_df = df_pedidos
            st.subheader("Todos los Pedidos")
        elif st.session_state.current_summary_view == "Trabajos Empezados":
            filtered_df = df_pedidos[df_pedidos['Inicio Trabajo'] == True]
            st.subheader("Pedidos con 'Inicio Trabajo'")
        elif st.session_state.current_summary_view == "Trabajos Terminados":
            filtered_df = df_pedidos[df_pedidos['Trabajo Terminado'] == True]
            st.subheader("Pedidos con 'Trabajo Terminado'")
        elif st.session_state.current_summary_view == "Pedidos Pendientes":
            filtered_df = df_pedidos[df_pedidos['Pendiente'] == True]
            st.subheader("Pedidos con 'Pendiente'")
        elif st.session_state.current_summary_view == "Pedidos sin estado específico":
            filtered_df = df_pedidos[
                (df_pedidos['Inicio Trabajo'] == False) &
                (df_pedidos['Trabajo Terminado'] == False) &
                (df_pedidos['Pendiente'] == False)
            ]
            st.subheader("Pedidos sin Estado Específico")

        if not filtered_df.empty:
            filtered_df_sorted = filtered_df.sort_values(by='ID', ascending=False)
            new_column_order = [
                'ID', 'Producto', 'Cliente', 'Club', 'Telefono', 'Breve Descripción',
                'Fecha entrada', 'Fecha Salida', 'Precio', 'Precio Factura',
                'Tipo de pago', 'Adelanto', 'Observaciones'
            ]
            remaining_columns = [col for col in filtered_df_sorted.columns if col not in new_column_order]
            final_column_order = new_column_order + remaining_columns
            filtered_df_reordered = filtered_df_sorted[final_column_order]
            st.dataframe(filtered_df_reordered.style.apply(highlight_pedidos_rows, axis=1))
        else:
            st.info(f"No hay pedidos en la categoría: {st.session_state.current_summary_view}")