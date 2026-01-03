import streamlit as st
import pandas as pd
from datetime import datetime
import io
from utils.firestore_utils import get_next_id, save_dataframe_firestore, delete_document_firestore


def show_gastos_page(df_gastos):
    st.header("💰 Gestión de Gastos")
    st.write("---")

    # --- RESUMEN RÁPIDO ---
    if df_gastos is not None and not df_gastos.empty:
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

        st.bar_chart(df_gastos.groupby('Tipo')['Importe'].sum())
    else:
        st.info("📭 No hay gastos registrados aún.")
        st.write("---")

    # --- FILTROS ---
    st.subheader("🔍 Filtrar y Buscar Gastos")

    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        tipo_filtro = st.multiselect(
            "Tipo de Gasto",
            options=["Fijo", "Variable"],
            default=["Fijo", "Variable"]
        )

    with col_f2:
        fecha_inicio = st.date_input("Fecha Inicio", value=None)
        fecha_fin = st.date_input("Fecha Fin", value=None)

    with col_f3:
        search_term = st.text_input(
            "Buscar por Concepto o ID",
            placeholder="Escribe para filtrar..."
        )

    df_filtrado = df_gastos.copy() if df_gastos is not None else pd.DataFrame()

    if not df_filtrado.empty:
        if tipo_filtro:
            df_filtrado = df_filtrado[df_filtrado['Tipo'].isin(tipo_filtro)]

        if fecha_inicio:
            df_filtrado = df_filtrado[pd.to_datetime(df_filtrado['Fecha']) >= pd.Timestamp(fecha_inicio)]

        if fecha_fin:
            df_filtrado = df_filtrado[pd.to_datetime(df_filtrado['Fecha']) <= pd.Timestamp(fecha_fin)]

        if search_term:
            mask = df_filtrado.apply(
                lambda row: search_term.lower() in str(row).lower(),
                axis=1
            )
            df_filtrado = df_filtrado[mask]

    # --- MOSTRAR GASTOS ---
    st.subheader(f"📋 Gastos Registrados ({len(df_filtrado)} de {len(df_gastos) if df_gastos is not None else 0})")

    if not df_filtrado.empty:
        df_display = df_filtrado.copy()

        if 'Fecha' in df_display.columns:
            df_display['Fecha'] = pd.to_datetime(
                df_display['Fecha'], errors='coerce'
            ).dt.strftime('%Y-%m-%d')

        df_display = df_display.sort_values('ID', ascending=False)

        st.dataframe(
            df_display,
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

        # --- EXPORTAR ---
        st.write("---")
        st.markdown("### 📥 Exportar Datos")

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

    # --- AÑADIR GASTO ---
    st.subheader("➕ Añadir Nuevo Gasto")

    with st.form("form_nuevo_gasto", clear_on_submit=True):
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            gasto_fecha = st.date_input("📅 Fecha del Gasto", value=datetime.now().date())
            gasto_concepto = st.text_input("📝 Concepto*")

        with col_g2:
            gasto_importe = st.number_input(
                "💰 Importe (€)*",
                min_value=0.0,
                step=0.01,
                format="%.2f"
            )
            gasto_tipo = st.selectbox("🏷️ Tipo de Gasto*", ["Fijo", "Variable"])

        submitted_gasto = st.form_submit_button("✅ Guardar Gasto", type="primary")

        if submitted_gasto:
            if not gasto_concepto.strip() or gasto_importe <= 0:
                st.error("❌ Concepto e Importe son obligatorios.")
                return

            next_gasto_id = get_next_id(df_gastos, 'ID')
            new_gasto = {
                "ID": next_gasto_id,
                "Fecha": gasto_fecha,
                "Concepto": gasto_concepto.strip(),
                "Importe": gasto_importe,
                "Tipo": gasto_tipo
            }

            df_gastos_actualizado = pd.concat(
                [df_gastos, pd.DataFrame([new_gasto])],
                ignore_index=True
            )

            st.session_state.data["df_gastos"] = df_gastos_actualizado

            if save_dataframe_firestore(df_gastos_actualizado, "gastos"):
                st.success(f"✅ Gasto {next_gasto_id} guardado correctamente")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Error al guardar el gasto")

    st.write("---")

    # --- ELIMINAR GASTO ---
    st.subheader("🗑️ Eliminar Gasto")

    delete_gasto_id = st.number_input(
        "🆔 ID del Gasto a Eliminar",
        min_value=1,
        step=1
    )

    if delete_gasto_id:
        gasto = df_gastos[df_gastos["ID"] == delete_gasto_id]

        if gasto.empty:
            st.error(f"❌ No existe el gasto {delete_gasto_id}")
            return

        gasto = gasto.iloc[0]
        st.warning(f"⚠️ Vas a eliminar el gasto {delete_gasto_id}")

        if st.button("🗑️ ELIMINAR DEFINITIVAMENTE", type="primary"):
            doc_id = gasto.get("id_documento_firestore")

            if not doc_id:
                st.error("❌ Gasto sin ID de Firestore.")
                return

            if delete_document_firestore("gastos", doc_id):
                df_gastos = df_gastos[df_gastos["ID"] != delete_gasto_id]
                st.session_state.data["df_gastos"] = df_gastos
                st.success("✅ Gasto eliminado")
                st.rerun()
            else:
                st.error("❌ Error al eliminar el gasto")
