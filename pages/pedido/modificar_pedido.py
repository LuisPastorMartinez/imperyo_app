import streamlit as st
import pandas as pd
import time
from datetime import datetime, date
from utils import save_dataframe_firestore
from .helpers import convert_to_firestore_type, safe_select_index

def safe_to_date(value):
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value.strip() != "":
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except Exception:
            return datetime.now().date()
    return datetime.now().date()

def show_modify(df_pedidos, df_listas):
    st.subheader("Modificar Pedido Existente")

    # Mostrar mensaje de éxito si existe
    if "pedido_guardado_ok" in st.session_state:
        if time.time() - st.session_state["pedido_guardado_ok"]["timestamp"] < 5:
            st.success(st.session_state["pedido_guardado_ok"]["mensaje"])
        else:
            del st.session_state["pedido_guardado_ok"]

    mod_id = st.number_input("ID del pedido a modificar:", min_value=1, key="modify_id_input")
    if st.button("Cargar Pedido", key="load_pedido_button"):
        pedido = df_pedidos[df_pedidos['ID'] == mod_id]
        if not pedido.empty:
            st.session_state.pedido_a_modificar = pedido.iloc[0].to_dict()
            st.success(f"Pedido {mod_id} cargado para modificación")
        else:
            st.warning(f"No existe un pedido con ID {mod_id}")
            st.session_state.pedido_a_modificar = None

    if 'pedido_a_modificar' in st.session_state and st.session_state.pedido_a_modificar:
        pedido = st.session_state.pedido_a_modificar

        productos = [""] + df_listas['Producto'].dropna().unique().tolist() if 'Producto' in df_listas.columns else [""]
        tallas = [""] + df_listas['Talla'].dropna().unique().tolist() if 'Talla' in df_listas.columns else [""]
        telas = [""] + df_listas['Tela'].dropna().unique().tolist() if 'Tela' in df_listas.columns else [""]
        tipos_pago = [""] + df_listas['Tipo de pago'].dropna().unique().tolist() if 'Tipo de pago' in df_listas.columns else [""]

        with st.form("modificar_pedido_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("ID", value=pedido['ID'], disabled=True, key="mod_id")
                producto = st.selectbox("Producto*", productos, index=safe_select_index(productos, pedido.get('Producto','')), key="mod_producto")
                cliente = st.text_input("Cliente*", value=pedido.get('Cliente',''), key="mod_cliente")
                telefono = st.text_input("Teléfono*", value=pedido.get('Telefono',''), key="mod_telefono")
                club = st.text_input("Club*", value=pedido.get('Club',''), key="mod_club")
                talla = st.selectbox("Talla", tallas, index=safe_select_index(tallas, pedido.get('Talla','')), key="mod_talla")
                tela = st.selectbox("Tela", telas, index=safe_select_index(telas, pedido.get('Tela','')), key="mod_tela")
                descripcion = st.text_area("Descripción", value=pedido.get('Breve Descripción',''), key="mod_descripcion")

            with col2:
                fecha_entrada = st.date_input("Fecha entrada*", value=safe_to_date(pedido.get('Fecha entrada')), key="mod_fecha_entrada")
                tiene_fecha_salida = st.checkbox("Establecer fecha de salida", value=bool(pedido.get('Fecha Salida')), key="mod_tiene_fecha_salida")
                if tiene_fecha_salida:
                    fecha_salida = st.date_input("Fecha salida", value=safe_to_date(pedido.get('Fecha Salida')), key="mod_fecha_salida")
                else:
                    fecha_salida = None
                precio = st.number_input("Precio*", min_value=0.0, value=float(pedido.get('Precio',0) or 0), key="mod_precio")
                precio_factura = st.number_input("Precio factura", min_value=0.0, value=float(pedido.get('Precio Factura',0) or 0), key="mod_precio_factura")
                tipo_pago = st.selectbox("Tipo de pago", tipos_pago, index=safe_select_index(tipos_pago, pedido.get('Tipo de pago','')), key="mod_tipo_pago")
                adelanto = st.number_input("Adelanto", min_value=0.0, value=float(pedido.get('Adelanto',0) or 0), key="mod_adelanto")
                observaciones = st.text_area("Observaciones", value=pedido.get('Observaciones',''), key="mod_observaciones")

            st.write("**Estado del pedido:**")
            estado_cols = st.columns(5)
            with estado_cols[0]:
                empezado = st.checkbox("Empezado", value=bool(pedido.get('Inicio Trabajo', False)), key="mod_empezado")
            with estado_cols[1]:
                terminado = st.checkbox("Terminado", value=bool(pedido.get('Trabajo Terminado', False)), key="mod_terminado")
            with estado_cols[2]:
                cobrado = st.checkbox("Cobrado", value=bool(pedido.get('Cobrado', False)), key="mod_cobrado")
            with estado_cols[3]:
                retirado = st.checkbox("Retirado", value=bool(pedido.get('Retirado', False)), key="mod_retirado")
            with estado_cols[4]:
                pendiente = st.checkbox("Pendiente", value=bool(pedido.get('Pendiente', False)), key="mod_pendiente")

            if st.form_submit_button("Guardar Cambios"):
                if not cliente or not telefono or not producto or not club:
                    st.error("Por favor complete los campos obligatorios (*)")
                    return

                # ✅ Validación de teléfono
                if not telefono.isdigit() or len(telefono) != 9:
                    st.error("El teléfono debe contener exactamente 9 dígitos numéricos")
                    return

                updated_pedido = {
                    'ID': mod_id,
                    'Producto': convert_to_firestore_type(producto),
                    'Cliente': convert_to_firestore_type(cliente),
                    'Telefono': convert_to_firestore_type(telefono),
                    'Club': convert_to_firestore_type(club),
                    'Talla': convert_to_firestore_type(talla),
                    'Tela': convert_to_firestore_type(tela),
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
                    'id_documento_firestore': pedido['id_documento_firestore']
                }

                idx_list = df_pedidos.index[df_pedidos['ID'] == mod_id].tolist()
                if idx_list:
                    df_pedidos.loc[idx_list[0]] = updated_pedido
                    df_pedidos = df_pedidos.where(pd.notna(df_pedidos), None)
                    for c in df_pedidos.columns:
                        df_pedidos[c] = df_pedidos[c].apply(lambda x: None if x is pd.NaT else x)

                    if save_dataframe_firestore(df_pedidos, 'pedidos'):
                        st.session_state["pedido_guardado_ok"] = {
                            "mensaje": f"Pedido {mod_id} actualizado correctamente!",
                            "timestamp": time.time()
                        }
                        st.session_state["active_tab"] = "Consultar"
                        st.rerun()
                    else:
                        st.error("Error al actualizar el pedido")
                else:
                    st.error("No se encontró el índice del pedido para actualizar.")
