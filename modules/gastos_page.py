import streamlit as st
import pandas as pd
from datetime import datetime
import io

from utils.firestore_utils import save_dataframe_firestore, delete_document_firestore


# ---------- HELPERS ----------

def get_next_gasto_id_por_año(df, año):
    if df is None or df.empty:
        return 1

    if "Año" not in df.columns or "ID" not in df.columns:
        return 1

    df_año = df[df["Año"] == año]
    if df_año.empty:
        return 1

    ids = pd.to_numeric(df_año["ID"], errors="coerce").dropna()
    return int(ids.max()) + 1 if not ids.empty else 1


def reindexar_gastos_por_año(df, año):
    df_otros = df[df["Año"] != año]
    df_año = df[df["Año"] == año].sort_values("ID").reset_index(drop=True)
    df_año["ID"] = range(1, len(df_año) + 1)
    return pd.concat([df_año, df_otros], ignore_index=True)


# ---------- MAIN ----------

def show_gastos_page(df_gastos):
    st.header("💰 Gestión de Gastos")
    st.write("---")

    # ---------- ASEGURAR DATAFRAME ----------
    if df_gastos is None:
        df_gastos = pd.DataFrame()

    if "Año" not in df_gastos.columns:
        df_gastos["Año"] = datetime.now().year

    df_gastos["Año"] = pd.to_numeric(
        df_gastos["Año"], errors="coerce"
    ).fillna(datetime.now().year).astype("int64")

    # ---------- SELECTOR DE AÑO ----------
    años_disponibles = (
        sorted(df_gastos["Año"].unique(), reverse=True)
        if not df_gastos.empty
        else [datetime.now().year]
    )

    año_seleccionado = st.selectbox(
        "📅 Año",
        años_disponibles,
        index=0
    )

    df_año = df_gastos[df_gastos["Año"] == año_seleccionado].copy()

    # ---------- RESUMEN ----------
    if not df_año.empty:
        total = df_año["Importe"].sum()
        fijos = df_año[df_año["Tipo"] == "Fijo"]["Importe"].sum()
        variables = df_año[df_año["Tipo"] == "Variable"]["Importe"].sum()

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("📊 Total", f"{total:.2f} €")
        with c2:
            st.metric("📌 Fijos", f"{fijos:.2f} €")
        with c3:
            st.metric("📈 Variables", f"{variables:.2f} €")
    else:
        st.info(f"📭 No hay gastos en {año_seleccionado}")

    st.write("---")

    # ---------- MOSTRAR GASTOS ----------
    st.subheader(f"📋 Gastos registrados ({len(df_año)})")

    if not df_año.empty:
        df_show = df_año.copy()

        if "Fecha" in df_show.columns:
            df_show["Fecha"] = pd.to_datetime(
                df_show["Fecha"], errors="coerce"
            ).dt.strftime("%Y-%m-%d")

        df_show = df_show.sort_values("ID", ascending=False)

        st.dataframe(
            df_show,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay gastos para mostrar.")

    # ---------- EXPORTAR ----------
    if not df_año.empty:
        buffer = io.BytesIO()
        try:
            df_export = df_año.copy()
            if "Fecha" in df_export.columns:
                df_export["Fecha"] = pd.to_datetime(
                    df_export["Fecha"], errors="coerce"
                )

            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df_export.to_excel(writer, index=False, sheet_name="Gastos")

            st.download_button(
                "📥 Descargar Excel",
                buffer.getvalue(),
                file_name=f"gastos_{año_seleccionado}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        except Exception as e:
            st.error(f"❌ Error al generar el Excel: {e}")

    st.write("---")

    # ---------- CREAR GASTO ----------
    st.subheader("➕ Añadir Gasto")

    with st.form("crear_gasto_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            fecha = st.date_input("📅 Fecha", datetime.now().date())
            concepto = st.text_input("📝 Concepto*")

        with col2:
            importe = st.number_input(
                "💰 Importe (€)*",
                min_value=0.0,
                step=0.01,
                format="%.2f"
            )
            tipo = st.selectbox("🏷️ Tipo", ["Fijo", "Variable"])

        guardar = st.form_submit_button("✅ Guardar Gasto", type="primary")

    if guardar:
        if not concepto.strip() or importe <= 0:
            st.error("❌ Concepto e importe son obligatorios.")
            return

        next_id = get_next_gasto_id_por_año(df_gastos, año_seleccionado)

        new_gasto = {
            "ID": next_id,
            "Año": año_seleccionado,
            "Fecha": fecha,
            "Concepto": concepto.strip(),
            "Importe": importe,
            "Tipo": tipo,
            "id_documento_firestore": None
        }

        df_gastos = pd.concat(
            [df_gastos, pd.DataFrame([new_gasto])],
            ignore_index=True
        )

        if save_dataframe_firestore(df_gastos, "gastos"):
            st.session_state.data["df_gastos"] = df_gastos
            st.success(f"✅ Gasto {next_id} / {año_seleccionado} creado")
            st.balloons()
            st.rerun()
        else:
            st.error("❌ Error al guardar el gasto")

    st.write("---")

    # ---------- ELIMINAR GASTO ----------
    st.subheader("🗑️ Eliminar Gasto")

    delete_id = st.number_input(
        "🆔 ID del gasto (del año seleccionado)",
        min_value=1,
        step=1
    )

    gasto = df_año[df_año["ID"] == delete_id]

    if not gasto.empty:
        gasto = gasto.iloc[0]
        st.warning(f"⚠️ Vas a eliminar el gasto {delete_id} / {año_seleccionado}")

        if st.button("🗑️ ELIMINAR DEFINITIVAMENTE", type="primary"):
            doc_id = gasto.get("id_documento_firestore")

            if not doc_id:
                st.error("❌ Gasto sin ID de Firestore.")
                return

            if delete_document_firestore("gastos", doc_id):
                df_gastos = df_gastos[
                    ~((df_gastos["ID"] == delete_id) & (df_gastos["Año"] == año_seleccionado))
                ]

                df_gastos = reindexar_gastos_por_año(df_gastos, año_seleccionado)

                if save_dataframe_firestore(df_gastos, "gastos"):
                    st.session_state.data["df_gastos"] = df_gastos
                    st.success("✅ Gasto eliminado y IDs reorganizados")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Error al guardar cambios")
    elif delete_id:
        st.error("❌ No existe ese gasto en el año seleccionado.")
