# pages/gastos_page.py
import streamlit as st
import pandas as pd
from utils.firestore_utils import get_next_id, save_dataframe_firestore, delete_document_firestore

def highlight_gastos_rows(row):
    """Función para resaltar filas en la tabla de gastos"""
    styles = [''] * len(row)
    if row.get('Tipo') == 'Fijo':
        styles = ['background-color: #FFF2CC'] * len(row)
    elif row.get('Tipo') == 'Variable':
        styles = ['background-color: #E2F0D9'] * len(row)
    return styles

def show_gastos_page(df_gastos):
    st.header("Gestión de Gastos")
    st.write("Aquí puedes gestionar tus gastos.")
    
    # Mostrar gastos registrados con resaltado
    st.subheader("Gastos Registrados")
    st.dataframe(df_gastos.style.apply(highlight_gastos_rows, axis=1))
    
    # Sección para añadir nuevo gasto
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
            if not gasto_concepto or gasto_importe <= 0:
                st.error("Por favor complete todos los campos obligatorios (Concepto e Importe)")
            else:
                next_gasto_id = get_next_id(df_gastos, 'ID')
                new_gasto_record = {
                    'ID': next_gasto_id,
                    'Fecha': gasto_fecha,
                    'Concepto': gasto_concepto,
                    'Importe': gasto_importe,
                    'Tipo': gasto_tipo if gasto_tipo != "" else None
                }
                new_gasto_df_row = pd.DataFrame([new_gasto_record])
                
                # Actualiza el DataFrame en session_state
                st.session_state.data['df_gastos'] = pd.concat([df_gastos, new_gasto_df_row], ignore_index=True)
                
                if save_dataframe_firestore(st.session_state.data['df_gastos'], 'gastos'):
                    st.success(f"Gasto {next_gasto_id} guardado con éxito!")
                    st.rerun()
                else:
                    st.error("Error al guardar el gasto.")

    # Sección para eliminar gastos
    st.subheader("Eliminar Gasto")
    delete_gasto_id = st.number_input("ID del Gasto a Eliminar:", 
                                     min_value=1, 
                                     value=None, 
                                     key="delete_gasto_id_input")

    gasto_a_eliminar = pd.DataFrame()
    if delete_gasto_id is not None and delete_gasto_id > 0:
        gasto_a_eliminar = df_gastos[df_gastos['ID'] == delete_gasto_id]

    if not gasto_a_eliminar.empty:
        st.warning(f"¿Seguro que quieres eliminar el gasto con ID **{delete_gasto_id}**?")
        st.dataframe(gasto_a_eliminar.style.apply(highlight_gastos_rows, axis=1))

        col_g_confirm1, col_g_confirm2 = st.columns(2)
        with col_g_confirm1:
            if st.button("Confirmar Eliminación", key="confirm_delete_gasto_button"):
                doc_id_to_delete = gasto_a_eliminar['id_documento_firestore'].iloc[0]
                if delete_document_firestore('gastos', doc_id_to_delete):
                    st.success(f"Gasto {delete_gasto_id} eliminado con éxito!")
                    st.rerun()
                else:
                    st.error("Error al eliminar el gasto.")
        with col_g_confirm2:
            if st.button("Cancelar", key="cancel_delete_gasto_button"):
                st.info("Eliminación cancelada.")
                st.rerun()
    elif delete_gasto_id is not None and delete_gasto_id > 0:
        st.info(f"No se encontró ningún gasto con el ID {delete_gasto_id}.")

    # Resumen estadístico
    st.subheader("Resumen de Gastos")
    if not df_gastos.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Gastos", f"${df_gastos['Importe'].sum():,.2f}")
        with col2:
            st.metric("Gastos Fijos", f"${df_gastos[df_gastos['Tipo']=='Fijo']['Importe'].sum():,.2f}")
        with col3:
            st.metric("Gastos Variables", f"${df_gastos[df_gastos['Tipo']=='Variable']['Importe'].sum():,.2f}")
        
        # Gráfico simple de distribución
        st.bar_chart(df_gastos.groupby('Tipo')['Importe'].sum())
    else:
        st.info("No hay datos de gastos para mostrar.")