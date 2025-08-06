import streamlit as st
import pandas as pd
import os
import hashlib
from utils.firestore_utils import load_dataframes_firestore, save_dataframe_firestore, delete_document_firestore, get_next_id

# --- CONFIGURACIÓN BÁSICA DE LA PÁGINA ---
st.set_page_config(
    page_title="ImperYo",
    page_icon="https://www.dropbox.com/scl/fi/opp61pwyq2lxleaj3hxs3/Logo-Movil-e-instagran.png?rlkey=4cruzlufwlz9vfr2myezjkz1d&dl=1",
    layout="wide"
)

# --- CSS PERSONALIZADO PARA RESPONSIVIDAD ---
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
</style>
""", unsafe_allow_html=True)

# --- HEADER CON LOGO Y TÍTULO ---
col_logo, col_title = st.columns([0.1, 0.9])
with col_logo:
    st.image("https://www.dropbox.com/scl/fi/opp61pwyq2lxleaj3hxs3/Logo-Movil-e-instagran.png?rlkey=4cruzlufwlz9vfr2myezjkz1d&dl=1", width=80)
with col_title:
    st.header("Imperyo Sport - Gestión de Pedidos y Gastos")

# --- FUNCIÓN DE COLOREADO DE FILAS ---
def highlight_pedidos_rows(row):
    styles = [''] * len(row)
    # Usar .get() para evitar KeyError si la columna no existe en la fila
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

# --- LÓGICA DE AUTENTICACIÓN ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    
    try:
        correct_username = st.secrets["auth"]["username"]
        correct_password_hash = st.secrets["auth"]["password_hash"]
    except KeyError:
        st.error("Error de configuración: No se encontraron las credenciales en secrets.toml.")
        st.stop()

    if not st.session_state["authenticated"]:
        st.text_input("Usuario", key="username_input")
        st.text_input("Contraseña", type="password", key="password_input")
        
        if st.button("Iniciar Sesión"):
            hashed_input_password = hashlib.sha256(st.session_state["password_input"].encode()).hexdigest()
            if st.session_state["username_input"] == correct_username and hashed_input_password == correct_password_hash:
                st.session_state["authenticated"] = True
                st.success("Inicio de sesión exitoso!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
        return False
    else:
        return True

# --- LÓGICA PRINCIPAL DE LA APLICACIÓN ---
if check_password():
    
    if 'data_loaded' not in st.session_state or not st.session_state.data_loaded:
        with st.spinner('Cargando datos desde Firestore...'):
            try:
                data = load_dataframes_firestore()
                if data:
                    st.session_state.df_pedidos = data.get('df_pedidos', pd.DataFrame())
                    st.session_state.df_gastos = data.get('df_gastos', pd.DataFrame())
                    st.session_state.df_totales = data.get('df_totales', pd.DataFrame())
                    st.session_state.df_listas = data.get('df_listas', pd.DataFrame())
                    st.session_state.df_trabajos = data.get('df_trabajos', pd.DataFrame())
                    st.session_state.data_loaded = True
                else:
                    st.error("Error al cargar los datos desde Firestore.")
                    st.stop()
            except Exception as e:
                st.error(f"Ocurrió un error al cargar los datos: {e}")
                st.stop()

    df_pedidos = st.session_state.df_pedidos
    df_gastos = st.session_state.df_gastos
    df_totales = st.session_state.df_totales
    df_listas = st.session_state.df_listas
    df_trabajos = st.session_state.df_trabajos

    # --- FUNCIÓN PARA UNIFICAR COLUMNAS ---
    def unify_dataframe_columns(df):
        df.columns = [col.strip() for col in df.columns]
        
        telefono_cols = [col for col in df.columns if 'telefono' in col.lower()]
        if telefono_cols:
            main_telefono_col = 'Telefono'
            if main_telefono_col not in df.columns:
                df[main_telefono_col] = pd.Series(dtype=str)
            for col in telefono_cols:
                if col != main_telefono_col:
                    df[main_telefono_col] = df[main_telefono_col].fillna(df[col])
                    df = df.drop(columns=[col])
        else:
            df['Telefono'] = pd.Series(dtype=str)

        fecha_entrada_cols = [col for col in df.columns if 'fecha entrada' in col.lower()]
        if fecha_entrada_cols:
            main_fecha_entrada_col = 'Fecha entrada'
            if main_fecha_entrada_col not in df.columns:
                df[main_fecha_entrada_col] = pd.Series(dtype='datetime64[ns]')
            for col in fecha_entrada_cols:
                if col != main_fecha_entrada_col:
                    df[main_fecha_entrada_col] = df[main_fecha_entrada_col].fillna(df[col])
                    df = df.drop(columns=[col])
        else:
            df['Fecha entrada'] = pd.Series(dtype='datetime64[ns]')

        if 'id_documento_firestore' not in df.columns:
            df['id_documento_firestore'] = None
        
        return df

    st.session_state.df_pedidos = unify_dataframe_columns(st.session_state.df_pedidos.copy())
    df_pedidos = st.session_state.df_pedidos

    # --- FUNCIÓN PARA ASEGURAR COLUMNAS DE ESTADO ---
    def ensure_status_columns(df):
        status_cols = ['Inicio Trabajo', 'Trabajo Terminado', 'Cobrado', 'Retirado', 'Pendiente']
        for col in status_cols:
            if col not in df.columns:
                df[col] = False
        return df

    st.session_state.df_pedidos = ensure_status_columns(st.session_state.df_pedidos.copy())
    df_pedidos = st.session_state.df_pedidos
    
    # --- FUNCIÓN PARA EL ORDEN DE LAS COLUMNAS ---
    def get_ordered_dataframe(df_to_order, collection_name):
        default_order = {
            'pedidos': [
                'ID', 'Producto', 'Cliente', 'Club', 'Telefono', 'Breve Descripción',
                'Fecha entrada', 'Fecha Salida', 'Precio', 'Precio Factura',
                'Tipo de pago', 'Adelanto', 'Observaciones'
            ],
            'gastos': [
                'ID', 'Fecha', 'Concepto', 'Importe', 'Tipo'
            ]
        }
        status_columns = ['Inicio Trabajo', 'Trabajo Terminado', 'Cobrado', 'Retirado', 'Pendiente']

        if collection_name == 'pedidos':
            new_column_order = default_order['pedidos'] + status_columns
        else:
            new_column_order = default_order.get(collection_name, df_to_order.columns.tolist())

        final_column_order = [col for col in new_column_order if col in df_to_order.columns]
        
        return df_to_order[final_column_order]
    
    # --- FUNCIONES DE PÁGINAS ---
    def page_inicio():
        st.header("Bienvenido a Imperyo Sport")
        st.write("---")
        st.subheader("Estado General de Pedidos")
        st.info(f"Total de Pedidos Registrados: **{len(df_pedidos)}**")
    
    def page_ver_datos():
        st.header("Datos Cargados de Firestore")
        
        st.subheader("Colección 'pedidos'")
        if not df_pedidos.empty:
            df_pedidos_sorted = df_pedidos.sort_values(by='ID', ascending=False)
            df_pedidos_reordered = get_ordered_dataframe(df_pedidos_sorted, 'pedidos')
            st.dataframe(df_pedidos_reordered.style.apply(highlight_pedidos_rows, axis=1))
        else:
            st.info("No hay datos en la colección 'pedidos'.")
        
        st.subheader("Colección 'gastos'")
        if not df_gastos.empty:
            df_gastos_reordered = get_ordered_dataframe(df_gastos, 'gastos')
            st.dataframe(df_gastos_reordered)
        else:
            st.info("No hay datos en la colección 'gastos'.")
        
        st.subheader("Colección 'totales'")
        st.dataframe(df_totales)
        st.subheader("Colección 'listas'")
        st.dataframe(df_listas)
        st.subheader("Colección 'trabajos'")
        st.dataframe(df_trabajos)

    def page_pedidos():
        st.header("Gestión de Pedidos")
        tab_guardar, tab_buscar, tab_modificar, tab_eliminar = st.tabs(["Guardar Nuevo", "Buscar Pedido", "Modificar Pedido", "Eliminar Pedido"])

        with tab_guardar:
            handle_save_pedido()
        with tab_buscar:
            handle_search_pedido()
        with tab_modificar:
            handle_modify_pedido()
        with tab_eliminar:
            handle_delete_pedido()

    def page_gastos():
        st.header("Gestión de Gastos")
        st.subheader("Gastos Registrados")
        if not df_gastos.empty:
            df_gastos_sorted = df_gastos.sort_values(by='ID', ascending=False)
            st.dataframe(get_ordered_dataframe(df_gastos_sorted, 'gastos'))
        else:
            st.info("No hay datos en la colección 'gastos'.")
        
        st.subheader("Añadir Gasto")
        handle_save_gasto()
        
        st.subheader("Eliminar Gasto")
        handle_delete_gasto()
    
    def page_resumen():
        st.header("Resumen de Pedidos")
        
        if 'current_summary_view' not in st.session_state:
            st.session_state.current_summary_view = "Todos los Pedidos"

        selected_summary_view = st.radio(
            "Seleccionar Vista:",
            ["Todos los Pedidos", "Trabajos Empezados", "Trabajos Terminados", "Pedidos Pendientes", "Pedidos sin estado específico"],
            key="summary_view_radio_page"
        )
        
        filtered_df = pd.DataFrame()
        if selected_summary_view == "Todos los Pedidos":
            filtered_df = df_pedidos
        elif selected_summary_view == "Trabajos Empezados":
            filtered_df = df_pedidos[df_pedidos['Inicio Trabajo'] == True]
        elif selected_summary_view == "Trabajos Terminados":
            filtered_df = df_pedidos[df_pedidos['Trabajo Terminado'] == True]
        elif selected_summary_view == "Pedidos Pendientes":
            filtered_df = df_pedidos[df_pedidos['Pendiente'] == True]
        elif selected_summary_view == "Pedidos sin estado específico":
            filtered_df = df_pedidos[
                (df_pedidos['Inicio Trabajo'] == False) &
                (df_pedidos['Trabajo Terminado'] == False) &
                (df_pedidos['Pendiente'] == False)
            ]

        if not filtered_df.empty:
            filtered_df_sorted = filtered_df.sort_values(by='ID', ascending=False)
            filtered_df_reordered = get_ordered_dataframe(filtered_df_sorted, 'pedidos')
            st.dataframe(filtered_df_reordered.style.apply(highlight_pedidos_rows, axis=1))
        else:
            st.info(f"No hay pedidos en la categoría: {selected_summary_view}")

    def display_pedido_form(pedido_data, is_modifying=False):
        next_pedido_id = get_next_id(df_pedidos, 'ID') if not is_modifying else pedido_data['ID']
        
        producto_val = pedido_data.get('Producto', None)
        cliente_val = pedido_data.get('Cliente', "")
        telefono_val = pedido_data.get('Telefono', "")
        club_val = pedido_data.get('Club', "")
        talla_val = pedido_data.get('Talla', None)
        tela_val = pedido_data.get('Tela', None)
        descripcion_val = pedido_data.get('Breve Descripción', "")
        fecha_entrada_val = pedido_data.get('Fecha entrada', pd.NaT)
        fecha_salida_val = pedido_data.get('Fecha Salida', pd.NaT)
        precio_val = float(pedido_data.get('Precio', 0.0)) if pd.notna(pedido_data.get('Precio')) else 0.0
        precio_factura_val = float(pedido_data.get('Precio Factura', 0.0)) if pd.notna(pedido_data.get('Precio Factura')) else 0.0
        tipo_pago_val = pedido_data.get('Tipo de pago', None)
        adelanto_val_str = str(pedido_data.get('Adelanto', "")) if pd.notna(pedido_data.get('Adelanto')) else ""
        observaciones_val = pedido_data.get('Observaciones', "")
        ch_empezado_val = pedido_data.get('Inicio Trabajo', False)
        ch_trabajo_terminado_val = pedido_data.get('Trabajo Terminado', False)
        ch_cobrado_val = pedido_data.get('Cobrado', False)
        ch_retirado_val = pedido_data.get('Retirado', False)
        ch_pendiente_val = pedido_data.get('Pendiente', False)

        with st.form(f"form_{'modificar' if is_modifying else 'guardar'}_pedido", clear_on_submit=not is_modifying):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("ID", value=next_pedido_id, disabled=True)
                producto_options = [""] + df_listas['Producto'].dropna().unique().tolist()
                producto = st.selectbox("Producto", options=producto_options, index=producto_options.index(producto_val) if producto_val in producto_options else 0)
                cliente = st.text_input("Cliente", value=cliente_val)
                telefono = st.text_input("Telefono", value=telefono_val)
                club = st.text_input("Club", value=club_val)
                talla_options = [""] + df_listas['Talla'].dropna().unique().tolist()
                talla = st.selectbox("Talla", options=talla_options, index=talla_options.index(talla_val) if talla_val in talla_options else 0)
                tela_options = [""] + df_listas['Tela'].dropna().unique().tolist()
                tela = st.selectbox("Tela", options=tela_options, index=tela_options.index(tela_val) if tela_val in tela_options else 0)
                breve_descripcion = st.text_area("Breve Descripción", value=descripcion_val)
            
            with col2:
                fecha_entrada = st.date_input("Fecha entrada", value=fecha_entrada_val.date() if pd.notna(fecha_entrada_val) else None)
                fecha_salida = st.date_input("Fecha Salida", value=fecha_salida_val.date() if pd.notna(fecha_salida_val) else None)
                precio = st.number_input("Precio", min_value=0.0, format="%.2f", value=precio_val)
                precio_factura = st.number_input("Precio Factura", min_value=0.0, format="%.2f", value=precio_factura_val)
                tipo_pago_options = [""] + df_listas['Tipo de pago'].dropna().unique().tolist()
                tipo_pago = st.selectbox("Tipo de Pago", options=tipo_pago_options, index=tipo_pago_options.index(tipo_pago_val) if tipo_pago_val in tipo_pago_options else 0)
                adelanto_str = st.text_input("Adelanto (opcional)", value=adelanto_val_str)
                observaciones = st.text_area("Observaciones", value=observaciones_val)

            st.write("---")
            st.write("**Estado del Pedido:**")
            col_chk1, col_chk2, col_chk3, col_chk4, col_chk5 = st.columns(5)
            with col_chk1:
                ch_empezado = st.checkbox("Empezado", value=ch_empezado_val)
            with col_chk2:
                ch_trabajo_terminado = st.checkbox("Trabajo Terminado", value=ch_trabajo_terminado_val)
            with col_chk3:
                ch_cobrado = st.checkbox("Cobrado", value=ch_cobrado_val)
            with col_chk4:
                ch_retirado = st.checkbox("Retirado", value=ch_retirado_val)
            with col_chk5:
                ch_pendiente = st.checkbox("Pendiente", value=ch_pendiente_val)

            submitted = st.form_submit_button("Guardar Cambios" if is_modifying else "Guardar Pedido")
            
            return submitted, {
                'ID': next_pedido_id,
                'Producto': producto,
                'Cliente': cliente,
                'Telefono': telefono,
                'Club': club,
                'Talla': talla,
                'Tela': tela,
                'Breve Descripción': breve_descripcion,
                'Fecha entrada': fecha_entrada,
                'Fecha Salida': fecha_salida,
                'Precio': precio,
                'Precio Factura': precio_factura,
                'Tipo de pago': tipo_pago,
                'Adelanto_str': adelanto_str,
                'Observaciones': observaciones,
                'Inicio Trabajo': ch_empezado,
                'Cobrado': ch_cobrado,
                'Retirado': ch_retirado,
                'Pendiente': ch_pendiente,
                'Trabajo Terminado': ch_trabajo_terminado
            }

    def handle_save_pedido():
        st.subheader("Guardar Nuevo Pedido")
        st.write(f"ID del Nuevo Pedido: **{get_next_id(df_pedidos, 'ID')}**")

        submitted, form_data = display_pedido_form(pd.Series())
        
        if submitted:
            if form_data['Inicio Trabajo'] and form_data['Trabajo Terminado']:
                st.error("Error: Un pedido no puede estar 'Empezado' y 'Trabajo Terminado' al mismo tiempo.")
                st.rerun()
            else:
                adelanto = None
                if form_data['Adelanto_str']:
                    try:
                        adelanto = float(form_data['Adelanto_str'])
                    except ValueError:
                        st.error("Por favor, introduce un número válido para 'Adelanto' o déjalo vacío.")
                        st.rerun()

                new_record = {
                    'ID': form_data['ID'],
                    'Producto': form_data['Producto'] if form_data['Producto'] != "" else None,
                    'Cliente': form_data['Cliente'],
                    'Telefono': form_data['Telefono'],
                    'Club': form_data['Club'],
                    'Talla': form_data['Talla'] if form_data['Talla'] != "" else None,
                    'Tela': form_data['Tela'] if form_data['Tela'] != "" else None,
                    'Breve Descripción': form_data['Breve Descripción'],
                    'Fecha entrada': form_data['Fecha entrada'],
                    'Fecha Salida': form_data['Fecha Salida'],
                    'Precio': form_data['Precio'],
                    'Precio Factura': form_data['Precio Factura'],
                    'Tipo de pago': form_data['Tipo de pago'] if form_data['Tipo de pago'] != "" else None,
                    'Adelanto': adelanto,
                    'Observaciones': form_data['Observaciones'],
                    'Inicio Trabajo': form_data['Inicio Trabajo'],
                    'Cobrado': form_data['Cobrado'],
                    'Retirado': form_data['Retirado'],
                    'Pendiente': form_data['Pendiente'],
                    'Trabajo Terminado': form_data['Trabajo Terminado']
                }
                
                new_df_row = pd.DataFrame([new_record])
                st.session_state.df_pedidos = pd.concat([st.session_state.df_pedidos, new_df_row], ignore_index=True)

                if save_dataframe_firestore(st.session_state.df_pedidos, 'pedidos'):
                    st.success(f"Pedido {form_data['ID']} guardado con éxito!")
                    st.session_state.data_loaded = False
                    st.rerun()
                else:
                    st.error("Error al guardar el pedido.")

    def handle_search_pedido():
        st.subheader("Buscar Pedido")
        search_id = st.number_input("Introduce el ID del pedido:", min_value=1, value=None, format="%d")
        if st.button("Buscar", key="search_button_tab"):
            found_pedido = df_pedidos[df_pedidos['ID'] == search_id]
            if not found_pedido.empty:
                st.success(f"Pedido {search_id} encontrado:")
                st.dataframe(get_ordered_dataframe(found_pedido, 'pedidos').style.apply(highlight_pedidos_rows, axis=1))
            else:
                st.warning(f"No se encontró ningún pedido con el ID {search_id}.")

    def handle_modify_pedido():
        st.subheader("Modificar Pedido")
        modify_search_id = st.number_input("Introduce el ID del pedido a modificar:", min_value=1, value=None, format="%d")
        
        if modify_search_id and st.button("Buscar para Modificar", key="modify_search_button"):
            found_pedido_row = df_pedidos[df_pedidos['ID'] == modify_search_id]
            if not found_pedido_row.empty:
                st.session_state.modifying_pedido = found_pedido_row.iloc[0].to_dict()
                st.success(f"Pedido {modify_search_id} encontrado. Modifica a continuación.")
                st.rerun()
            else:
                st.session_state.modifying_pedido = None
                st.warning(f"No se encontró ningún pedido con el ID {modify_search_id}.")
        
        if st.session_state.get('modifying_pedido'):
            current_pedido = pd.Series(st.session_state.modifying_pedido)
            submitted, form_data = display_pedido_form(current_pedido, is_modifying=True)
            
            if submitted:
                if form_data['Inicio Trabajo'] and form_data['Trabajo Terminado']:
                    st.error("Error: Un pedido no puede estar 'Empezado' y 'Trabajo Terminado' al mismo tiempo.")
                    st.rerun()
                else:
                    adelanto = None
                    if form_data['Adelanto_str']:
                        try:
                            adelanto = float(form_data['Adelanto_str'])
                        except ValueError:
                            st.error("Por favor, introduce un número válido para 'Adelanto' o déjalo vacío.")
                            st.rerun()

                    row_index = st.session_state.df_pedidos[st.session_state.df_pedidos['ID'] == current_pedido['ID']].index[0]
                    
                    updated_record = {
                        'ID': current_pedido['ID'],
                        'Producto': form_data['Producto'] if form_data['Producto'] != "" else None,
                        'Cliente': form_data['Cliente'],
                        'Telefono': form_data['Telefono'],
                        'Club': form_data['Club'],
                        'Talla': form_data['Talla'] if form_data['Talla'] != "" else None,
                        'Tela': form_data['Tela'] if form_data['Tela'] != "" else None,
                        'Breve Descripción': form_data['Breve Descripción'],
                        'Fecha entrada': form_data['Fecha entrada'],
                        'Fecha Salida': form_data['Fecha Salida'],
                        'Precio': form_data['Precio'],
                        'Precio Factura': form_data['Precio Factura'],
                        'Tipo de pago': form_data['Tipo de pago'] if form_data['Tipo de pago'] != "" else None,
                        'Adelanto': adelanto,
                        'Observaciones': form_data['Observaciones'],
                        'Inicio Trabajo': form_data['Inicio Trabajo'],
                        'Cobrado': form_data['Cobrado'],
                        'Retirado': form_data['Retirado'],
                        'Pendiente': form_data['Pendiente'],
                        'Trabajo Terminado': form_data['Trabajo Terminado'],
                        'id_documento_firestore': current_pedido['id_documento_firestore']
                    }

                    st.session_state.df_pedidos.loc[row_index] = updated_record
                    
                    if save_dataframe_firestore(st.session_state.df_pedidos, 'pedidos'):
                        st.success(f"Pedido {current_pedido['ID']} modificado con éxito!")
                        st.session_state.modifying_pedido = None
                        st.session_state.data_loaded = False
                        st.rerun()
                    else:
                        st.error("Error al modificar el pedido.")
                        st.rerun()


    def handle_delete_pedido():
        st.subheader("Eliminar Pedido")
        delete_id = st.number_input("ID del Pedido a Eliminar:", min_value=1, value=None, format="%d", key="delete_id_input")
        
        if delete_id is not None and delete_id > 0:
            pedido_a_eliminar = df_pedidos[df_pedidos['ID'] == delete_id]
            if not pedido_a_eliminar.empty:
                st.warning(f"¿Seguro que quieres eliminar el pedido con ID **{delete_id}**?")
                st.dataframe(get_ordered_dataframe(pedido_a_eliminar, 'pedidos').style.apply(highlight_pedidos_rows, axis=1))

                col_confirm1, col_confirm2 = st.columns(2)
                with col_confirm1:
                    if st.button("Confirmar Eliminación", key="confirm_delete_button"):
                        doc_id_to_delete = pedido_a_eliminar['id_documento_firestore'].iloc[0]
                        if delete_document_firestore('pedidos', doc_id_to_delete):
                            st.success(f"Pedido {delete_id} eliminado con éxito de Firestore.")
                            st.session_state.data_loaded = False
                            st.rerun()
                        else:
                            st.error("Error al eliminar el pedido de Firestore.")
                            st.rerun()
                with col_confirm2:
                    if st.button("Cancelar Eliminación", key="cancel_delete_button"):
                        st.info("Eliminación cancelada.")
                        st.session_state.data_loaded = False
                        st.rerun()
            else:
                st.info(f"No se encontró ningún pedido con el ID {delete_id} para eliminar.")

    def handle_save_gasto():
        with st.form("form_nuevo_gasto", clear_on_submit=True):
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                gasto_fecha = st.date_input("Fecha Gasto")
                gasto_concepto = st.text_input("Concepto")
            with col_g2:
                gasto_importe = st.number_input("Importe", min_value=0.0, format="%.2f")
                gasto_tipo = st.selectbox("Tipo Gasto", options=["", "Fijo", "Variable"])
            
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
                
                st.session_state.df_gastos = pd.concat([df_gastos, new_gasto_df_row], ignore_index=True)
                
                if save_dataframe_firestore(st.session_state.df_gastos, 'gastos'):
                    st.success(f"Gasto {next_gasto_id} guardado con éxito!")
                    st.session_state.data_loaded = False
                    st.rerun()
                else:
                    st.error("Error al guardar el gasto.")
                    st.rerun()

    def handle_delete_gasto():
        st.subheader("Eliminar Gasto")
        delete_gasto_id = st.number_input("ID del Gasto a Eliminar:", min_value=1, value=None, format="%d", key="delete_gasto_id_input")

        if delete_gasto_id is not None and delete_gasto_id > 0:
            gasto_a_eliminar = df_gastos[df_gastos['ID'] == delete_gasto_id]
            if not gasto_a_eliminar.empty:
                st.warning(f"¿Seguro que quieres eliminar el gasto con ID **{delete_gasto_id}**?")
                st.dataframe(get_ordered_dataframe(gasto_a_eliminar, 'gastos'))

                col_g_confirm1, col_g_confirm2 = st.columns(2)
                with col_g_confirm1:
                    if st.button("Confirmar Eliminación Gasto", key="confirm_delete_gasto_button"):
                        doc_id_to_delete_gasto = gasto_a_eliminar['id_documento_firestore'].iloc[0]
                        if delete_document_firestore('gastos', doc_id_to_delete_gasto):
                            st.success(f"Gasto {delete_gasto_id} eliminado con éxito de Firestore.")
                            st.session_state.data_loaded = False
                            st.rerun()
                        else:
                            st.error("Error al eliminar el gasto de Firestore.")
                            st.rerun()
            with col_g_confirm2:
                if st.button("Cancelar Eliminación Gasto", key="cancel_delete_gasto_button"):
                    st.info("Eliminación de gasto cancelada.")
                    st.session_state.data_loaded = False
                    st.rerun()
        elif delete_gasto_id is not None and delete_gasto_id > 0:
            st.info(f"No se encontró ningún gasto con el ID {delete_gasto_id} para eliminar.")

    # --- BOTÓN DE CERRAR SESIÓN ---
    st.sidebar.markdown("---")
    def logout():
        st.session_state.clear()
        st.rerun()

    if st.sidebar.button("Cerrar Sesión"):
        logout()

    # --- NAVEGACIÓN DE LA APLICACIÓN (BARRA LATERAL) ---
    st.sidebar.title("Navegación")
    page = st.sidebar.radio("Ir a:", ["Inicio", "Pedidos", "Gastos", "Resumen", "Ver Datos"], key="main_page_radio")

    # --- CONTENIDO DE LAS PÁGINAS ---
    if page == "Inicio":
        page_inicio()
    elif page == "Pedidos":
        page_pedidos()
    elif page == "Gastos":
        page_gastos()
    elif page == "Resumen":
        page_resumen()
    elif page == "Ver Datos":
        page_ver_datos()