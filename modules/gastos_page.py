import streamlit as st
import pandas as pd
from datetime import datetime
import io

from utils.firestore_utils import (
    save_dataframe_firestore,
    delete_document_firestore,
    update_document_firestore
)

# =====================================================
# HELPERS
# =====================================================

def empty_gastos_df():
    return pd.DataFrame(columns=[
        "ID", "Año", "Fecha", "Concepto",
        "Importe", "Tipo", "id_documento_firestore"
    ])


def get_next_gasto_id_por_año(df, año):
    if df is None or df.empty:
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


def format_fecha_col(df):
    df = df.copy()
    df["Fecha"] = pd.to_datetime(
        df["Fecha"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    return df


# =====================================================
# MAIN PAGE
# =====================================================

def show_gastos_page(df_gastos):
    st.header("💰 Gestión de Gastos")
    st.write("---")

    if df_gastos is None or df_gastos.empty:
        df_gastos = empty_gastos_df()

    df_gastos = df_gastos.copy()
    df_gastos["Año"] = pd.to_numeric(
        df_gastos.get("Año", datetime.now().year),
        errors="coerce"
    ).fillna(datetime.now().year).astype(int)

    # ---------- SELECTOR AÑO ----------
    años = sorted(df_gastos["Año"].unique(), reverse=True) \
        if not df_gastos.empty else [datetime.now().year]

    año = st.selectbox("📅 Año", años)

    df_año = df_gastos[df_gastos["Año"] == año].copy()

    # =================================================
    # ➕ AÑADIR GASTO
    # =================================================
    st.subheader("➕ Añadir Gasto")

    with st.form("form_crear_gasto", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            fecha = st.date_input("Fecha", datetime.now().date())
            concepto = st.text_input("Concepto*")
        with c2:
            importe = st.number_input("Importe (€)*", min_value=0.01, step=0.01)
            tipo = st.selectbox("Tipo", ["Fijo", "Variable"])

        crear = st.form_submit_button("Guardar gasto", type="primary")

    if crear:
        if not concepto.strip():
            st.error("❌ El concepto es obligatorio")
            return

        next_id = get_next_gasto_id_por_año(df_gastos, año)

        nuevo = {
            "ID": next_id,
            "Año": año,
            "Fecha": datetime.combine(fecha, datetime.min.time()),
            "Concepto": concepto.strip(),
            "Importe": float(importe),
            "Tipo": tipo,
            "id_documento_firestore": None
        }

        df_gastos = pd.concat([df_gastos, pd.DataFrame([nuevo])], ignore_index=True)

        if save_dataframe_firestore(df_gastos, "gastos"):
            st.session_state.data["df_gastos"] = df_gastos
            st.success("✅ Gasto añadido")
            st.balloons()
            st.rerun()

    st.write("---")

    # =================================================
    # 📋 CONSULTAR GASTOS
    # =================================================
    st.subheader("📋 Gastos registrados")

    if df_año.empty:
        st.info("No hay gastos este año.")
    else:
        total = df_año["Importe"].sum()
        st.metric("Total anual", f"{total:.2f} €")

        df_show = format_fecha_col(df_año)

        st.dataframe(
            df_show.sort_values("ID", ascending=False),
            use_container_width=True,
            hide_index=True
        )

        # EXPORTAR
        df_excel = format_fecha_col(df_año)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_excel.to_excel(writer, index=False)

        st.download_button(
            "📥 Descargar Excel",
            buffer.getvalue(),
            file_name=f"gastos_{año}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.write("---")

    # =================================================
    # ✏️ MODIFICAR GASTO
    # =================================================
    st.subheader("✏️ Modificar Gasto")

    if df_año.empty:
        st.info("No hay gastos para modificar.")
    else:
        max_id = int(df_año["ID"].max())
        gasto_id = st.number_input("ID del gasto", min_value=1, max_value=max_id)

        gasto_df = df_año[df_año["ID"] == gasto_id]
        if not gasto_df.empty:
            gasto = gasto_df.iloc[0]

            with st.form("form_modificar_gasto"):
                c1, c2 = st.columns(2)
                with c1:
                    fecha_m = st.date_input(
                        "Fecha",
                        pd.to_datetime(gasto["Fecha"]).date()
                    )
                    concepto_m = st.text_input("Concepto", gasto["Concepto"])
                with c2:
                    importe_m = st.number_input(
                        "Importe (€)", min_value=0.01,
                        value=float(gasto["Importe"])
                    )
                    tipo_m = st.selectbox(
                        "Tipo", ["Fijo", "Variable"],
                        index=0 if gasto["Tipo"] == "Fijo" else 1
                    )

                guardar = st.form_submit_button("Guardar cambios", type="primary")

            if guardar:
                update_document_firestore(
                    "gastos",
                    gasto["id_documento_firestore"],
                    {
                        "Fecha": datetime.combine(fecha_m, datetime.min.time()),
                        "Concepto": concepto_m.strip(),
                        "Importe": float(importe_m),
                        "Tipo": tipo_m
                    }
                )
                st.session_state.data_loaded = False
                st.success("✅ Gasto modificado")
                st.balloons()
                st.rerun()

    st.write("---")

    # =================================================
    # 🗑️ ELIMINAR GASTO
    # =================================================
    st.subheader("🗑️ Eliminar Gasto")

    if df_año.empty:
        st.info("No hay gastos para eliminar.")
    else:
        del_id = st.number_input("ID a eliminar", min_value=1)

        gasto_df = df_año[df_año["ID"] == del_id]
        if not gasto_df.empty:
            gasto = gasto_df.iloc[0]
            st.warning(f"Vas a eliminar el gasto {del_id}: {gasto['Concepto']}")

            if st.checkbox("Confirmo eliminar este gasto"):
                if st.button("ELIMINAR DEFINITIVAMENTE", type="primary"):
                    delete_document_firestore(
                        "gastos",
                        gasto["id_documento_firestore"]
                    )

                    df_gastos = df_gastos[
                        ~((df_gastos["ID"] == del_id) & (df_gastos["Año"] == año))
                    ]

                    df_gastos = reindexar_gastos_por_año(df_gastos, año)

                    save_dataframe_firestore(df_gastos, "gastos")
                    st.session_state.data["df_gastos"] = df_gastos
                    st.success("🗑️ Gasto eliminado")
                    st.balloons()
                    st.rerun()
