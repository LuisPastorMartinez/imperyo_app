import streamlit as st
import pandas as pd
from datetime import datetime
from utils import get_next_id, save_dataframe_firestore
from .helpers import convert_to_firestore_type
import time

def show_create(df_pedidos, df_listas):
    st.subheader("Crear Nuevo Pedido")

    # 🔹 Inicializar estado limpio si no existe
    if "new_cliente" not in st.session_state:
        st.session_state["new_cliente"] = ""
        st.session_state["new_telefono"] = ""
        st.session_state["new_club"] = ""
        st.session_state["new_descripcion"] = ""
        st.session_state["new_fecha_entrada"] = datetime.now().date()
        st.session_state["new_tiene_fecha_salida"] = False
        st.session_state["new_fecha_salida"] = datetime.now().date()
        st.session_state["new_precio"] = 0.0
        st.session_state["new_precio_factura"] = 0.0
        st.session_state["new_tipo_pago"] = ""
        st.session_state["new_adelanto"] = 0.0
        st.session_state["new_observaciones"] = ""
        st.session_state["new_empezado"] = False
        st.session_state["new_terminado"] = False
        st.session_state["new_cobrado"] = False
        st.session_state["new_retirado"] = False
        st.session_state["new_pendiente"] = False
        st.session_state["productos"] = [{"Producto": "", "Tela": "", "PrecioUnitario": 0.0, "Cantidad": 1}]

    with st.form("nuevo_pedido_form"):
        next_id = get_next_id(df_pedidos, 'ID')
        st.info(f"El próximo ID de pedido será: **{next_id}**")

        # --- BLOQUE DINÁMICO DE PRODUCTOS ---
        st.markdown("### Productos del pedido")
        productos_lista = [""] + df_listas['Producto'].dropna().unique().tolist() if 'Producto' in df_listas.columns else [""]
        telas_lista = [""] + df_listas['Tela'].dropna().unique().tolist() if 'Tela' in df_listas.columns else [""]

        total_productos = 0.0
        for i, p in enumerate(st.session_state.productos):
            cols = st.columns([3, 3, 2, 2])
            with cols[0]:
                st.session_state.productos[i]["Producto"] = st.selectbox(
                    f"Producto {i+1}",
                    productos_lista,
                    index=productos_lista.index(p["Producto"]) if p["Producto"] in productos_lista else 0,
                    key=f"producto_{i}"
                )
            with cols[1]:
                st.session_state.productos[i]["Tela"] = st.selectbox(
                    f"Tela {i+1}",
                    telas_lista,
                    index=telas_lista.index(p["Tela"]) if p["Tela"] in telas_lista else 0,
                    key=f"tela_{i}"
                )
            with cols[2]:
                st.session_state.productos[i]["PrecioUnitario"] = st.number_input(
                    f"Precio {i+1}", min_value=0.0, value=float(p["PrecioUnitario"]), key=f"precio_unit_{i}"
                )
            with cols[3]:
                st.session_state.productos[i]["Cantidad"] = st.number_input(
                    f"Cantidad {i+1}", min_value=1, value=int(p["Cantidad"]), key=f"cantidad_{i}"
                )

            total_productos += st.session_state.productos[i]["PrecioUnitario"] * st.session_state.productos[i]["Cantidad"]

        st.markdown(f"**💰 Total productos: {total_productos:.2f} €**")

        add_col, remove_col = st.columns([1, 1])
        with add_col:
            if st.form_submit_button("➕ Añadir otro producto"):
                st.session_state.productos.append({"Producto": "", "Tela": "", "PrecioUnitario": 0.0, "Cantidad": 1})
                st.experimental_rerun()

        with remove_col:
            if len(st.session_state.productos) > 1:
                if st.form_submit_button("➖ Quitar último producto"):
                    st.session_state.productos.pop()
                    st.experimental_rerun()

        # --- RESTO DEL FORMULARIO ---
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input("Cliente*", key="new_cliente")
            telefono = st.text_input("Teléfono*", key="new_telefono", max_chars=9)
            club = st.text_input("Club*", key="new_club")
            descripcion = st.text_area("Descripción", key="new_descripcion")

        with col2:
            fecha_entrada = st.date_input("Fecha entrada", value=st.session_state["new_fecha_entrada"], key="new_fecha_entrada")
            tiene_fecha_salida = st.checkbox("Establecer fecha de salida", value=st.session_state["new_tiene_fecha_salida"], key="new_tiene_fecha_salida")
            fecha_salida = st.date_input("Fecha salida", value=st.session_state["new_fecha_salida"], key="new_fecha_salida") if tiene_fecha_salida else None
            precio = st.number_input("Precio total", min_value=0.0, value=total_productos, key="new_precio")
            precio_factura = st.number_input("Precio factura", min_value=0.0, value=st.session_state["new_precio_factura"], key="new_precio_factura")
            tipos_pago = [""] + df_listas['Tipo de pago'].dropna().unique().tolist() if 'Tipo de pago' in df_listas.columns else [""]
            tipo_pago = st.selectbox("Tipo de pago", tipos_pago, key="new_tipo_pago")
            adelanto = st.number_input("Adelanto", min_value=0.0, value=st.session_state["new_adelanto"], key="new_adelanto")
            observaciones = st.text_area("Observaciones", key="new_observaciones")

        st.write("**Estado del pedido:**")
        estado_cols = st.columns(5)
        with estado_cols[0]:
            empezado = st.checkbox("Empezado", value=st.session_state["new_empezado"], key="new_empezado")
        with estado_cols[1]:
            terminado = st.checkbox("Terminado", value=st.session_state["new_terminado"], key="new_terminado")
        with estado_cols[2]:
            cobrado = st.checkbox("Cobrado", value=st.session_state["new_cobrado"], key="new_cobrado")
        with estado_cols[3]:
            retirado = st.checkbox("Retirado", value=st.session_state["new_retirado"], key="new_retirado")
        with estado_cols[4]:
            pendiente = st.checkbox("Pendiente", value=st.session_state["new_pendiente"], key="new_pendiente")

        if st.form_submit_button("Guardar Nuevo Pedido"):
            if not cliente or not telefono or not club:
                st.error("Por favor complete los campos obligatorios (*)")
                return

            if not telefono.isdigit() or len(telefono) != 9:
                st.error("El teléfono debe contener exactamente 9 dígitos numéricos")
                return

            new_pedido = {
                'ID': next_id,
                'Productos': st.session_state.productos,
                'Cliente': convert_to_firestore_type(cliente),
                'Telefono': convert_to_firestore_type(telefono),
                'Club': convert_to_firestore_type(club),
                'Breve Descripción': convert_to_firestore_type(descripcion),
                'Fecha entrada': convert_to_firestore_type(fecha_entrada),
                'Fecha Salida': convert_to_firestore_type(fecha_salida),
                'Precio': convert_to_firestore_type(precio),
                'Precio Factura': convert_to_firestore_type(precio_factura),
                'Tipo de pago': convert_to_firestore_type(tipo_pago),
                'Adelanto': convert_to_firestore_type(adelanto),
                'Observaciones': convert_to_firestore_type(observaciones),
                'Inicio Trabajo': convert_to_firestore_type(empezado),
                'Trabajo Terminado': convert_to_firestore_type(terminado),
                'Cobrado': convert_to_firestore_type(cobrado),
                'Retirado': convert_to_firestore_type(retirado),
                'Pendiente': convert_to_firestore_type(pendiente),
                'id_documento_firestore': None
            }

            new_pedido_df = pd.DataFrame([new_pedido])
            df_pedidos = pd.concat([df_pedidos, new_pedido_df], ignore_index=True)
            df_pedidos = df_pedidos.where(pd.notna(df_pedidos), None)

            for c in df_pedidos.columns:
                df_pedidos[c] = df_pedidos[c].apply(lambda x: None if x is pd.NaT else x)

            if save_dataframe_firestore(df_pedidos, 'pedidos'):
                success_placeholder = st.empty()
                success_placeholder.success(f"Pedido {next_id} creado correctamente!")
                time.sleep(2)
                success_placeholder.empty()

                if 'data' not in st.session_state:
                    st.session_state['data'] = {}
                st.session_state.data['df_pedidos'] = df_pedidos

                # Resetear formulario
                for key in list(st.session_state.keys()):
                    if key.startswith("new_") or key.startswith("producto_") or key.startswith("tela_") or key.startswith("precio_unit_"):
                        del st.session_state[key]
                st.session_state.productos = [{"Producto": "", "Tela": "", "PrecioUnitario": 0.0, "Cantidad": 1}]
                st.rerun()
            else:
                st.error("Error al crear el pedido")
