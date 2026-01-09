import pandas as pd
import streamlit as st

from utils.firestore_utils import (
    load_dataframes_firestore,
    delete_document_firestore
)


def limpiar_pedidos_duplicados():
    st.header("🧹 Limpieza de pedidos duplicados (PRUEBAS)")
    st.warning(
        "⚠️ Esta acción eliminará pedidos duplicados.\n\n"
        "Se conservará SIEMPRE el último pedido creado/modificado.\n"
        "Solo recomendado en entorno de pruebas."
    )

    if not st.checkbox("Confirmo que quiero limpiar duplicados"):
        st.info("Marca la casilla para continuar.")
        return

    data = load_dataframes_firestore()
    df = data.get("df_pedidos")

    if df is None or df.empty:
        st.info("📭 No hay pedidos.")
        return

    # =========================
    # NORMALIZAR
    # =========================
    df = df.copy()

    df["Año"] = pd.to_numeric(
        df["Año"], errors="coerce"
    ).fillna(0).astype(int)

    df["ID"] = pd.to_numeric(
        df["ID"], errors="coerce"
    ).fillna(0).astype(int)

    if "id_documento_firestore" not in df.columns:
        st.error("❌ No se encuentra id_documento_firestore.")
        return

    # =========================
    # ORDENAR (ÚLTIMO = SE QUEDA)
    # =========================
    # Firestore IDs más recientes suelen ir al final
    df = df.sort_values("id_documento_firestore")

    # =========================
    # DETECTAR DUPLICADOS
    # =========================
    duplicados = df[df.duplicated(subset=["Año", "ID"], keep="last")]

    if duplicados.empty:
        st.success("✅ No hay pedidos duplicados.")
        return

    st.warning(f"⚠️ Se van a eliminar {len(duplicados)} pedidos duplicados")

    # =========================
    # BORRAR DUPLICADOS
    # =========================
    errores = 0

    for _, row in duplicados.iterrows():
        ok = delete_document_firestore(
            "pedidos",
            row["id_documento_firestore"]
        )
        if not ok:
            errores += 1

    # =========================
    # RESULTADO
    # =========================
    if errores == 0:
        st.success("🧹 Duplicados eliminados correctamente")
    else:
        st.error(f"❌ {errores} pedidos no se pudieron eliminar")

    st.info("🔄 Recarga la aplicación para ver los cambios")
