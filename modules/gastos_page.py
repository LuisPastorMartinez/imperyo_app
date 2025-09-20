import streamlit as st
import pandas as pd
from datetime import datetime
import io
from utils.firestore_utils import get_next_id, save_dataframe_firestore, delete_document_firestore

def highlight_gastos_rows(row):
    """Función para resaltar filas en la tabla de gastos"""
    styles = [''] * len(row)
    if row.get('Tipo') == 'Fijo':
        styles = ['background-color: #FFF2CC'] * len(row)  # Amarillo suave
    elif row.get('Tipo') == 'Variable':
        styles = ['background-color: #E2F0D9'] * len(row)  # Verde suave
    return styles

def show_gastos_page(df_gastos):
    st.header("💰 Gestión de Gastos")
    st.write("---")

    # --- RESUMEN RÁPIDO ---
    if not df_gastos.empty:
        total_gastos = df_gastos['Importe'].sum()
        gastos_fijos = df_gastos[df_gastos['Tipo'] == 'Fijo']['Importe'].sum()
        gastos_variables = df_gastos[df_gastos['Tipo'] == 'Variable']['Importe'].sum()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Total Gastos", f"{total_gastos:,.2f} €")
        with col2:
            st.metric("📌 Gastos Fijos", f"{gastos_fijos:,.2f} €")
        with col3:
            st.metric("📈 Gastos Variables", f"{gastos_variables:,.2f} €")

        # Gráfico de distribución
        st.bar_chart(df_gastos.groupby('Tipo')['Importe'].sum())
    else:
        st.info("📭 No hay gastos registrados aún.")
        st.write("---")

    # --- FILTROS Y BÚSQUEDA ---
    st.subheader("🔍 Filtrar y Buscar Gastos")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        tipo_filtro = st.multiselect(
            "Tipo de Gasto",
            options=["Fijo", "Variable"],
            default=["Fijo", "Variable"],
            key="gastos_tipo_filtro"
        )
    
    with col_f2:
        fecha_inicio = st.date_input("Fecha Inicio", value=None, key="gastos_fecha_inicio")
        fecha_fin = st.date_input("Fecha Fin", value=None, key="gastos_fecha_fin")
    
    with col_f3:
        search_term = st.text_input("Buscar por Concepto o ID", placeholder="Escribe para filtrar...", key="gastos_search")

    # Aplicar filtros
    df_filtrado = df_gastos.copy()
    
    if tipo_filtro:
        df_filtrado = df_filtrado[df_filtrado['Tipo'].isin(tipo_filtro)]
    
    if fecha_inicio:
        df_filtrado = df_filtrado[pd.to_datetime(df_filtrado['Fecha']) >= pd.Timestamp(fecha_inicio)]
    
    if fecha_fin:
        df_filtrado = df_filtrado[pd.to_datetime(df_filtrado['Fecha']) <= pd.Timestamp(fecha_fin)]
    
    if search_term:
        mask = df_filtrado.apply(lambda row: search_term.lower() in str(row).lower(), axis=1)
        df_filtrado = df_filtrado[mask]

    # --- MOSTRAR GASTOS FILTRADOS ---
    st.subheader(f"📋 Gastos Registrados ({len(df_filtrado)} de {len(df_gastos)})")
    
    if not df_filtrado.empty:
        # Preparar DataFrame para mostrar
        df_display = df_filtrado.copy()
        
        # Formatear fechas
        if 'Fecha' in df_display.columns:
            df_display['Fecha'] = pd.to_datetime(df_display['Fecha'], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # Ordenar por ID descendente
        df_display = df_display.sort_values('ID', ascending=False)
        
        # Mostrar tabla con estilo
        st.dataframe(
            df_display.style.apply(highlight_gastos_rows, axis=1),
            column_config={
                "ID": st.column_config.NumberColumn("🆔 ID", format="%d"),
                "Fecha": st.column_config.TextColumn("📅 Fecha"),
                "Concepto": st.column_config.TextColumn("📝 Concepto", width="medium"),
                "Importe": st.column_config.NumberColumn("💰 Importe (€)", format="%.2f €"),
                "Tipo": st.column_config.TextColumn("🏷️ Tipo", width="small"),
            },
            use_container_width=True,
            hide_index=True
        )
        
        # --- BOTÓN DE EXPORTACIÓN ---
        st.write("---")
        st.markdown("### 📥 Exportar Datos")
        
        # Preparar DataFrame para exportar
        df_export = df_filtrado.copy()
        if 'Fecha' in df_export.columns:
            df_export['Fecha'] = pd.to_datetime(df_export['Fecha'], errors='coerce')
        
        buffer = io.BytesIO()
        try:
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Gastos')
            
            st.download_button(
                label="📥 Descargar como Excel",
                data=buffer.getvalue(),
                file_name=f"gastos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        except Exception as e:
            st.error(f"❌ Error al generar el archivo Excel: {e}")
    else:
        st.info("📭 No se encontraron gastos con los filtros aplicados.")

    st.write("---")

    # --- SECCIÓN PARA AÑADIR NUEVO GASTO ---
    st.subheader("➕ Añadir Nuevo Gasto")
    
    with st.form("form_nuevo_gasto", clear_on_submit=True):
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            gasto_fecha = st.date_input(
                "📅 Fecha del Gasto", 
                value=datetime.now().date(),
                key="gasto_fecha"
            )
            gasto_concepto = st.text_input(
                "📝 Concepto*", 
                placeholder="Ej: Material, Alquiler, Servicios...",
                key="gasto_concepto"
            )
        
        with col_g2:
            gasto_importe = st.number_input(
                "💰 Importe (€)*", 
                min_value=0.0, 
                step=0.01,
                format="%.2f",
                key="gasto_importe"
            )
            gasto_tipo = st.selectbox(
                "🏷️ Tipo de Gasto*", 
                options=["Fijo", "Variable"],
                index=0,
                key="gasto_tipo"
            )
        
        submitted_gasto = st.form_submit_button("✅ Guardar Gasto", type="primary")

        if submitted_gasto:
            if not gasto_concepto.strip() or gasto_importe <= 0:
                st.error("❌ Por favor complete todos los campos obligatorios (Concepto e Importe deben ser válidos)")
                return

            next_gasto_id = get_next_id(df_gastos, 'ID')
            new_gasto_record = {
                'ID': next_gasto_id,
                'Fecha': gasto_fecha,
                'Concepto': gasto_concepto.strip(),
                'Importe': gasto_importe,
                'Tipo': gasto_tipo
            }
            new_gasto_df_row = pd.DataFrame([new_gasto_record])
            
            # Actualiza el DataFrame en session_state
            df_gastos_actualizado = pd.concat([df_gastos, new_gasto_df_row], ignore_index=True)
            st.session_state.data['df_gastos'] = df_gastos_actualizado
            
            if save_dataframe_firestore(df_gastos_actualizado, 'gastos'):
                st.success(f"🎉 ¡Gasto **{next_gasto_id}** guardado con éxito!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Error al guardar el gasto. Por favor, inténtelo de nuevo.")

    st.write("---")

    # --- SECCIÓN PARA ELIMINAR GASTOS ---
    st.subheader("🗑️ Eliminar Gasto")
    
    col_del1, col_del2 = st.columns([2, 1])
    
    with col_del1:
        delete_gasto_id = st.number_input(
            "🆔 ID del Gasto a Eliminar:", 
            min_value=1, 
            value=None, 
            step=1,
            key="delete_gasto_id_input",
            placeholder="Ej: 42"
        )

    gasto_a_eliminar = pd.DataFrame()
    if delete_gasto_id is not None and delete_gasto_id > 0:
        gasto_a_eliminar = df_gastos[df_gastos['ID'] == delete_gasto_id]

    if not gasto_a_eliminar.empty:
        st.warning(f"⚠️ ¿Seguro que quieres eliminar el gasto con ID **{delete_gasto_id}**?")
        st.markdown("**Detalles del gasto a eliminar:**")
        
        # Mostrar detalles del gasto
        gasto_detalle = gasto_a_eliminar.iloc[0]
        st.markdown(f"""
        - **Concepto:** {gasto_detalle['Concepto']}
        - **Fecha:** {gasto_detalle['Fecha']}
        - **Importe:** {gasto_detalle['Importe']:,.2f} €
        - **Tipo:** {gasto_detalle['Tipo']}
        """)
        
        col_g_confirm1, col_g_confirm2 = st.columns(2)
        with col_g_confirm1:
            if st.button("✅ Confirmar Eliminación", type="primary", key="confirm_delete_gasto_button"):
                doc_id_to_delete = gasto_a_eliminar['id_documento_firestore'].iloc[0] if 'id_documento_firestore' in gasto_a_eliminar.columns else None
                if doc_id_to_delete:
                    if delete_document_firestore('gastos', doc_id_to_delete):
                        st.success(f"🗑️ ¡Gasto **{delete_gasto_id}** eliminado con éxito!")
                        st.rerun()
                    else:
                        st.error("❌ Error al eliminar el gasto en Firestore.")
                else:
                    st.error("❌ No se encontró el ID del documento en Firestore.")
        with col_g_confirm2:
            if st.button("❌ Cancelar", key="cancel_delete_gasto_button"):
                st.info("ℹ️ Eliminación cancelada.")
                st.rerun()
    elif delete_gasto_id is not None and delete_gasto_id > 0:
        st.error(f"❌ No se encontró ningún gasto con el ID **{delete_gasto_id}**.")