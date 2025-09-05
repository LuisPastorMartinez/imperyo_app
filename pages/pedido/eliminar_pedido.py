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
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Cliente:** {pedido_data.get('Cliente', '')}")
        st.write(f"**Teléfono:** {pedido_data.get('Telefono', '')}")
        st.write(f"**Club:** {pedido_data.get('Club', '')}")
        st.write(f"**Descripción:** {pedido_data.get('Breve Descripción', '')}")
    with col2:
        st.write(f"**Fecha Entrada:** {pedido_data.get('Fecha entrada', '')}")
        st.write(f"**Fecha Salida:** {pedido_data.get('Fecha Salida', '')}")
        st.write(f"**Precio Total:** {pedido_data.get('Precio', 0)} €")
        st.write(f"**Precio Factura:** {pedido_data.get('Precio Factura', 0)} €")
        st.write(f"**Tipo de pago:** {pedido_data.get('Tipo de pago', '')}")
        st.write(f"**Adelanto:** {pedido_data.get('Adelanto', 0)} €")

    st.write(f"**Observaciones:** {pedido_data.get('Observaciones', '')}")

    # --- Mostrar productos ---
    st.markdown("### 🛍️ Productos del pedido")
    productos_data = []
    if "Productos" in pedido_data:
        productos_raw = pedido_data["Productos"]
        if isinstance(productos_raw, list):
            productos_data = productos_raw
        elif isinstance(productos_raw, str) and productos_raw.strip():
            try:
                productos_data = json.loads(productos_raw)
            except json.JSONDecodeError:
                productos_data = []

    if productos_data:
        total = 0.0
        for i, prod in enumerate(productos_data, start=1):
            producto = prod.get("Producto", "")
            tela = prod.get("Tela", "")
            precio = float(prod.get("PrecioUnitario", 0))
            cantidad = int(prod.get("Cantidad", 1))
            subtotal = precio * cantidad
            total += subtotal

            st.write(f"**Producto {i}:** {producto}")
            st.write(f"• Tela: {tela}")
            st.write(f"• Precio Unitario: {precio:.2f} €")
            st.write(f"• Cantidad: {cantidad}")
            st.write(f"• Subtotal: {subtotal:.2f} €")
            st.markdown("---")

        st.markdown(f"**💰 Total Productos: {total:.2f} €**")
    else:
        st.info("Este pedido no tiene productos registrados.")

    # --- Botón de eliminación en dos pasos ---
    if st.session_state.delete_step == 0:
        if st.button("🟢 Eliminar Pedido", key="delete_step_1"):
            st.session_state.delete_step = 1
            st.rerun()

    elif st.session_state.delete_step == 1:
        if st.button(f"🔴 Confirmar eliminación del pedido N°{delete_id}", key="delete_step_2"):
            # Eliminar pedido
            df_pedidos = df_pedidos[df_pedidos['ID'] != delete_id]
            df_pedidos.reset_index(drop=True, inplace=True)

            if save_dataframe_firestore(df_pedidos, 'pedidos'):
                st.session_state.delete_step = 0
                st.success(f"✅ Pedido {delete_id} eliminado correctamente.")
                st.rerun()
            else:
                st.error("❌ Error al eliminar el pedido.")
