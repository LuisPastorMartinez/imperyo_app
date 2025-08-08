# Archivo: app.py (versión refactorizada)
import streamlit as st
import pandas as pd
import os
import hashlib
import re
from datetime import datetime, date
from utils.firestore_utils import load_dataframes_firestore

# Importa la nueva función desde el archivo pages/pedidos_page.py
from pages.pedidos_page import pedidos_page_content

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
</style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN DE LA BASE DE DATOS Y DATAFRAMES ---
@st.cache_data(ttl=600)
def get_data_from_firestore():
    data = load_dataframes_firestore()
    df_pedidos = data['df_pedidos']
    df_gastos = data['df_gastos']
    df_listas = data['df_listas']
    df_trabajos = data['df_trabajos']
    df_totales = data['df_totales']
    
    if df_pedidos.empty:
        df_pedidos = pd.DataFrame(columns=['ID', 'Producto', 'Cliente', 'Club', 'Telefono', 'Breve Descripción',
                                           'Fecha entrada', 'Fecha Salida', 'Precio', 'Precio Factura',
                                           'Tipo de pago', 'Adelanto', 'Observaciones', 'Inicio Trabajo',
                                           'Trabajo Terminado', 'Cobrado', 'Retirado', 'Pendiente', 'id_documento_firestore'])
    if df_gastos.empty:
        df_gastos = pd.DataFrame(columns=['ID', 'Concepto', 'Descripción', 'Cantidad', 'Fecha', 'id_documento_firestore'])
    if df_listas.empty:
        df_listas = pd.DataFrame(columns=['Producto', 'Talla', 'Tela', 'Tipo de pago'])
    if df_trabajos.empty:
        df_trabajos = pd.DataFrame(columns=['ID', 'Producto', 'Descripción', 'id_documento_firestore'])
    if df_totales.empty:
        df_totales = pd.DataFrame(columns=['id', 'total_adelanto', 'total_gastos', 'total_precio_factura'])

    df_pedidos['ID'] = pd.to_numeric(df_pedidos['ID'], errors='coerce').fillna(0).astype(int)
    df_pedidos['Fecha entrada'] = pd.to_datetime(df_pedidos['Fecha entrada'], errors='coerce').dt.date
    df_pedidos['Fecha Salida'] = pd.to_datetime(df_pedidos['Fecha Salida'], errors='coerce').dt.date
    
    df_gastos['ID'] = pd.to_numeric(df_gastos['ID'], errors='coerce').fillna(0).astype(int)
    df_gastos['Fecha'] = pd.to_datetime(df_gastos['Fecha'], errors='coerce').dt.date
    df_gastos['Cantidad'] = pd.to_numeric(df_gastos['Cantidad'], errors='coerce').fillna(0).astype(float)
    
    return {
        'df_pedidos': df_pedidos,
        'df_gastos': df_gastos,
        'df_listas': df_listas,
        'df_trabajos': df_trabajos,
        'df_totales': df_totales
    }

# --- AUTENTICACIÓN ---
def make_hashes(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- INTERFAZ PRINCIPAL DE LA APLICACIÓN ---
col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    st.image("https://www.dropbox.com/scl/fi/opp61pwyq2lxleaj3hxs3/Logo-Movil-e-instagran.png?rlkey=4cruzlufwlz9vfr2myezjkz1d&dl=1")
with col_titulo:
    st.title("ImperYo - Gestión de Pedidos y Gastos")

if not st.session_state.logged_in:
    st.subheader("Acceso a la Aplicación")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    
    try:
        users_data = st.secrets["auth"]
    except KeyError:
        st.error("Error: La configuración de autenticación no se encontró en secrets.toml. Asegúrate de que tienes una sección llamada '[auth]'")
        st.stop()
    
    if st.button("Iniciar Sesión"):
        if username in users_data:
            hashed_password = users_data[username]['password']
            if check_hashes(password, hashed_password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("¡Inicio de sesión exitoso!")
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
        else:
            st.error("Usuario no encontrado")

else:
    st.caption(f"Bienvenido, {st.session_state.username}")
    
    st.session_state.data = get_data_from_firestore()
    df_pedidos = st.session_state.data['df_pedidos']
    df_gastos = st.session_state.data['df_gastos']
    df_listas = st.session_state.data['df_listas']
    
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 'Pedidos'
    if 'current_summary_view' not in st.session_state:
        st.session_state.current_summary_view = "Todos los pedidos"
    if 'last_searched_modify_id' not in st.session_state:
        st.session_state.last_searched_modify_id = 1

    # --- NAVEGACIÓN ---
    st.sidebar.title("Menú")
    st.session_state.current_view = st.sidebar.radio("Elige una sección:", ['Pedidos', 'Gastos', 'Listas y Resumen'])

    if st.session_state.current_view == 'Pedidos':
        # Llamamos a la función de la página de pedidos
        pedidos_page_content(df_pedidos, df_listas)
    
    elif st.session_state.current_view == 'Gastos':
        st.header("Gestión de Gastos")
        tab_gastos_home, tab_gastos_add, tab_eliminar_gastos = st.tabs(["Ver Gastos", "Añadir Gasto", "Eliminar Gasto"])
        
        with tab_gastos_home:
            st.subheader("Lista de Gastos")
            if not df_gastos.empty:
                df_gastos_sorted = df_gastos.sort_values(by='ID', ascending=False)
                st.dataframe(df_gastos_sorted[['ID', 'Concepto', 'Descripción', 'Cantidad', 'Fecha']], use_container_width=True)
            else:
                st.info("No hay gastos registrados.")

        with tab_gastos_add:
            st.subheader("Añadir Nuevo Gasto")
            with st.form("form_add_gasto", clear_on_submit=True):
                concepto_add = st.text_input("Concepto del Gasto", key="add_gasto_concepto")
                descripcion_add = st.text_area("Descripción (opcional)", key="add_gasto_descripcion")
                cantidad_add = st.number_input("Cantidad", min_value=0.0, format="%.2f", key="add_gasto_cantidad")
                fecha_add = st.date_input("Fecha", value=date.today(), key="add_gasto_fecha")

                submitted_gasto = st.form_submit_button("Añadir Gasto")
                if submitted_gasto:
                    new_gasto_row = pd.DataFrame([{
                        'ID': get_next_id(df_gastos, 'ID'),
                        'Concepto': concepto_add,
                        'Descripción': descripcion_add,
                        'Cantidad': cantidad_add,
                        'Fecha': fecha_add
                    }])
                    st.session_state.data['df_gastos'] = pd.concat([st.session_state.data['df_gastos'], new_gasto_row], ignore_index=True)
                    if save_dataframe_firestore(st.session_state.data['df_gastos'], 'gastos'):
                        st.success(f"Gasto añadido con éxito!")
                        st.rerun()
                    else:
                        st.error("Error al añadir el gasto.")

        with tab_eliminar_gastos:
            st.subheader("Eliminar Gasto")
            delete_gasto_id = st.number_input("Introduce el ID del gasto a eliminar:", min_value=1, key="delete_gasto_id")
            
            if st.button("Buscar Gasto para Eliminar"):
                found_gasto = df_gastos[df_gastos['ID'] == delete_gasto_id]
                if not found_gasto.empty:
                    st.session_state.gasto_a_eliminar = found_gasto.iloc[0].to_dict()
                    st.warning(f"Se va a eliminar el gasto con ID {delete_gasto_id} de '{st.session_state.gasto_a_eliminar.get('Concepto', 'N/A')}'")
                    st.dataframe(found_gasto)
                else:
                    st.error("No se encontró un gasto con ese ID.")
                    st.session_state.gasto_a_eliminar = None
            
            if st.session_state.get('gasto_a_eliminar'):
                if st.button("Confirmar Eliminación de Gasto", key="confirmar_eliminar_gasto"):
                    try:
                        doc_id_firestore = st.session_state.gasto_a_eliminar.get('id_documento_firestore')
                        if delete_document_firestore('gastos', doc_id_firestore):
                            st.success(f"Gasto {delete_gasto_id} eliminado con éxito!")
                            st.session_state.gasto_a_eliminar = None
                            st.rerun()
                        else:
                            st.error("Error al eliminar el gasto de Firestore.")
                    except Exception as e:
                        st.error(f"Ocurrió un error inesperado al eliminar el gasto: {e}")
                        st.session_state.gasto_a_eliminar = None

    elif st.session_state.current_view == 'Listas y Resumen':
        st.header("Listas de Opciones y Resumen Financiero")
        tab_listas, tab_totales = st.tabs(["Gestionar Listas", "Resumen Financiero"])
        
        with tab_listas:
            st.subheader("Gestionar Listas de Opciones")
            st.write("Aquí puedes ver y modificar las opciones disponibles para Productos, Tallas, Telas y Tipos de Pago.")
            if not df_listas.empty:
                edited_df = st.data_editor(df_listas, num_rows="dynamic", key="data_editor_listas", use_container_width=True)
                if st.button("Guardar Listas", key="guardar_listas_button"):
                    if save_dataframe_firestore(edited_df, 'listas'):
                        st.success("Listas guardadas con éxito!")
                        st.rerun()
                    else:
                        st.error("Error al guardar las listas.")

        with tab_totales:
            st.subheader("Resumen Financiero")
            
            total_adelantos = df_pedidos['Adelanto'].sum()
            total_precio_factura = df_pedidos['Precio Factura'].sum()
            total_gastos = df_gastos['Cantidad'].sum()
            
            st.metric("Total de Precio en Factura", f"{total_precio_factura:,.2f} €")
            st.metric("Total de Adelantos", f"{total_adelantos:,.2f} €")
            st.metric("Total de Gastos", f"{total_gastos:,.2f} €")

            st.write("---")
            st.subheader("Detalles de Totales")

            col_tot1, col_tot2, col_tot3 = st.columns(3)
            with col_tot1:
                st.write("**Total Adelantos por Tipo de Pago**")
                adelantos_por_tipo = df_pedidos.groupby('Tipo de pago')['Adelanto'].sum().reset_index()
                st.bar_chart(adelantos_por_tipo.set_index('Tipo de pago'))
            with col_tot2:
                st.write("**Ingresos vs. Gastos**")
                data_chart = pd.DataFrame({
                    'Categoría': ['Ingresos Facturados', 'Gastos'],
                    'Cantidad': [total_precio_factura, total_gastos]
                }).set_index('Categoría')
                st.bar_chart(data_chart)
            with col_tot3:
                st.write("**Pedidos por Estado**")
                pedidos_por_estado = pd.DataFrame({
                    'Estado': ['Inicio Trabajo', 'Trabajo Terminado', 'Cobrado', 'Retirado', 'Pendiente'],
                    'Cantidad': [
                        df_pedidos['Inicio Trabajo'].sum(),
                        df_pedidos['Trabajo Terminado'].sum(),
                        df_pedidos['Cobrado'].sum(),
                        df_pedidos['Retirado'].sum(),
                        df_pedidos['Pendiente'].sum()
                    ]
                }).set_index('Estado')
                st.bar_chart(pedidos_por_estado)