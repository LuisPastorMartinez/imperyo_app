import streamlit as st
import pandas as pd
import json
from datetime import datetime

def show_consult(df_pedidos):
    st.subheader("Consultar Pedido por ID")

    consult_id = st.number_input("ID del pedido a consultar:", min_value=1, key="consult_id_input")
    if st.button("Buscar Pedido", key="consult_pedido_button"):
        pedido = df_pedidos[df_pedidos['ID'] == consult_id]
        if not pedido.empty:
            pedido = pedido.iloc[0].to_dict()

            st.markdown(f"### 📦 Pedido {consult_id}")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Cliente:** {pedido.get('Cliente', '')}")
                st.write(f"**Teléfono:** {pedido.get('Telefono', '')}")
                st.write(f"**Club:** {pedido.get('Club', '')}")
                st.write(f"**Descripción:** {pedido.get('Breve Descripción', '')}")
            with col2:
                st.write(f"**Fecha Entrada:** {pedido.get('Fecha entrada', '')}")
                st.write(f"**Fecha Salida:** {pedido.get('Fecha Salida', '')}")
                st.write(f"**Precio Total:** {pedido.get('Precio', 0)} €")
                st.write(f"**Precio Factura:** {pedido.get('Precio Factura', 0)} €")
                st.write(f"**Tipo de pago:** {pedido.get('Tipo de pago', '')}")
                st.write(f"**Adelanto:** {pedido.get('Adelanto', 0)} €")

            st.write(f"**Observaciones:** {pedido.get('Observaciones', '')}")

            # --- PRODUCTOS ---
            st.markdown("### 🛍️ Productos")
            productos_data = []
            if "Productos" in pedido:
                productos_raw = pedido["Productos"]
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

            # --- ESTADOS ---
            st.markdown("### 📊 Estado del pedido")
            estado_cols = st.columns(5)
            with estado_cols[0]:
                st.checkbox("Empezado", value=bool(pedido.get('Inicio Trabajo', False)), disabled=True)
            with estado_cols[1]:
                st.checkbox("Terminado", value=bool(pedido.get('Trabajo Terminado', False)), disabled=True)
            with estado_cols[2]:
                st.checkbox("Cobrado", value=bool(pedido.get('Cobrado', False)), disabled=True)
            with estado_cols[3]:
                st.checkbox("Retirado", value=bool(pedido.get('Retirado', False)), disabled=True)
            with estado_cols[4]:
                st.checkbox("Pendiente", value=bool(pedido.get('Pendiente', False)), disabled=True)

        else:
            st.warning(f"No se encontró un pedido con ID {consult_id}")
