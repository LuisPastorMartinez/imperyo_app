import streamlit as st
import pandas as pd
import json
from utils import save_dataframe_firestore

def show_delete(df_pedidos):
    st.subheader("Eliminar Pedido por ID")

    if "delete_step" not in st.session_state:
        st.session_state.delete_step = 0

    delete_id = st.number_input("ID del pedido a eliminar:", min_value=1, key="delete_id_input")
    pedido = df_pedidos[df_pedidos['ID'] == delete_id]

    if pedido.empty:
        st.warning("No existe un pedido con ese ID.")
        return

    pedido_data = pedido.iloc[0].to_dict()

    # --- Mostrar datos del pedido ---
    st.markdown(f"### 📦 Pedido {delete_id}")
    st.write(f"**Cliente:** {pedido_data.get('Cliente', '')}")
    st.write(f"**Descripción:** {pedido_data.get('Breve Descripción', '')}")
    st.write(f"**Precio Total:** {pedido_data.get('Precio', 0)} €")
    st.write(f"**Precio Factura:** {pedido_data.get('Precio Factura', 0)} €")

    # --- Mostrar productos (si existen) ---
    if "Productos" in pedido_data:
        try:
            productos = (
                pedido_data["Productos"]
                if isinstance(pedido_data["Productos"], list)
                else json.loads(pedido_data["Productos"])
            )
        except json.JSONDecodeError:
            productos = []
    else:
        productos = []

    if productos:
        total = 0
        st.markdown("### 🛍️ Productos del pedido")
        for i, prod in enumerate(productos, start=1):
            precio = float(prod.get("PrecioUnitario", 0))
            cantidad = int(prod.get("Cantidad", 1))
            subtotal = precio * cantidad
            total += subtotal
            st.write(f"**Producto {i}:** {prod.get('Producto', '')}")
            st.write(f"• Cantidad: {cantidad}  • Precio: {precio:.2f} €  • Subtotal: {subtotal:.2f} €")
            st.markdown("---")
        st.markdown(f"**💰 Total Productos: {total:.2f} €**")

    # --- Botón de confirmación en 2 pasos ---
    if st.session_state.delete_step == 0:
        if st.button("🟢 Eliminar Pedido", key="delete_step_1"):
            st.session_state.delete_step = 1
            st.rerun()

    elif st.session_state.delete_step == 1:
        if st.button(f"🔴 Confirmar eliminación del pedido N°{delete_id}", key="delete_step_2"):
            # 1. Eliminar el pedido del DataFrame
            df_filtrado = df_pedidos[df_pedidos["ID"] != delete_id].reset_index(drop=True)

            # 2. Guardar en Firestore
            if save_dataframe_firestore(df_filtrado, "pedidos"):
                st.session_state.delete_step = 0
                st.success(f"✅ Pedido {delete_id} eliminado correctamente.")
                st.rerun()
            else:
                st.error("❌ Error al guardar los cambios.")
