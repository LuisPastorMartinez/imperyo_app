# pages/pedido/crear_pedido.py
import streamlit as st
import pandas as pd
import time
from datetime import datetime
from utils import save_dataframe_firestore


def init_create_state():
    """Inicializa claves para crear pedido si no existen"""
    defaults = {
        "new_cliente": "",
        "new_producto": "",
        "new_telefono": "",
        "new_club": "",
        "new_talla": "",
        "new_tela": "",
        "new_descripcion": "",
        "new_fecha_entrada": datetime.now().date(),
        "new_tiene_fecha_salida": False,
        "new_fecha_salida": datetime.now().date(),
        "new_precio": 0.0,
        "new_precio_factura": 0.0,
        "new_tipo_pago": "",
        "new_adelanto": 0.0,
        "new_observaciones": "",
        "new_empezado": False,
        "new_terminado": False,
        "new_cobrado": False,
        "new_retirado": False,
        "new_pendiente": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def show_create(df_pedidos, df_listas):
    st.subheader("➕ Crear Pedido")

    # Inicializar estado
    init_create_state()

    with st.form("crear_pedido_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Cliente*", key="new_cliente")
            st.text_input("Teléfono*", key="new_telefono")
            st.text_input("Club*", key="new_club")
            st.text_input("Producto*", key="new_producto")
            st.text_input("Talla", key="new_talla")
            st.text_input("Tela", key="new_tela")
            st.text_area("Descripción", key="new_descripcion")

        with col2:
            st.date_input("Fecha entrada*", key="new_fecha_entrada")
            if st.checkbox("¿Tiene fecha de salida?", key="new_tiene_fecha_salida"):
                st.date_input("Fecha salida", key="new_fecha_salida")
            st.number_input("Precio*", min_value=0.0, key="new_precio")
            st.number_input("Precio factura", min_value=0.0, key="new_precio_factura")
            st.text_input("Tipo de pago", key="new_tipo_pago")
            st.number_input("Adelanto", min_value=0.0, key="new_adelanto")
            st.text_area("Observaciones", key="new_observaciones")

        st.write("**Estado del pedido:**")
        estado_cols = st.columns(5)
        with estado_cols[0]:
            st.checkbox("Empezado", key="new_empezado")
        with estado_cols[1]:
            st.checkbox("Terminado", key="new_terminado")
        with estado_cols[2]:
            st.checkbox("Cobrado", key="new_cobrado")
        with estado_cols[3]:
            st.checkbox("Retirado", key="new_retirado")
        with estado_cols[4]:
            st.checkbox("Pendiente", key="new_pendiente")

        guardar = st.form_submit_button("💾 Guardar Pedido", type="primary")

        if guardar:
            if not st.session_state.new_cliente or not st.session_state.new_telefono or not st.session_state.new_producto or not st.session_state.new_club:
                st.error("Por favor completa todos los campos obligatorios (*)")
                return

            if not st.session_state.new_telefono.isdigit() or len(st.session_state.new_telefono) != 9:
                st.error("El teléfono debe contener exactamente 9 dígitos numéricos")
                return

            nuevo_pedido = {
                "ID": int(df_pedidos["ID"].max() + 1) if not df_pedidos.empty else 1,
                "Cliente": st.session_state.new_cliente,
                "Telefono": st.session_state.new_telefono,
                "Club": st.session_state.new_club,
                "Producto": st.session_state.new_producto,
                "Talla": st.session_state.new_talla,
                "Tela": st.session_state.new_tela,
                "Breve Descripción": st.session_state.new_descripcion,
                "Fecha entrada": st.session_state.new_fecha_entrada,
                "Fecha Salida": st.session_state.new_fecha_salida if st.session_state.new_tiene_fecha_salida else None,
                "Precio": st.session_state.new_precio,
                "Precio Factura": st.session_state.new_precio_factura,
                "Tipo de pago": st.session_state.new_tipo_pago,
                "Adelanto": st.session_state.new_adelanto,
                "Observaciones": st.session_state.new_observaciones,
                "Inicio Trabajo": st.session_state.new_empezado,
                "Trabajo Terminado": st.session_state.new_terminado,
                "Cobrado": st.session_state.new_cobrado,
                "Retirado": st.session_state.new_retirado,
                "Pendiente": st.session_state.new_pendiente,
            }

            df_pedidos = pd.concat([df_pedidos, pd.DataFrame([nuevo_pedido])], ignore_index=True)

            if save_dataframe_firestore(df_pedidos, "pedidos"):
                success_placeholder = st.empty()
                success_placeholder.success("Pedido guardado correctamente ✅")
                time.sleep(5)
                success_placeholder.empty()

                # Limpiar estado
                keys_to_delete = [k for k in st.session_state.keys() if k.startswith("new_")]
                for k in keys_to_delete:
                    del st.session_state[k]

                st.session_state.data["df_pedidos"] = df_pedidos
                st.session_state.active_pedido_tab = "Consultar Pedidos"
                st.rerun()
            else:
                st.error("❌ Error al guardar el pedido en Firestore")
