import streamlit as st
import pandas as pd
import time
import json
from datetime import datetime, date
from ..utils.firestore_utils import save_dataframe_firestore
from .helpers import convert_to_firestore_type, safe_select_index

def safe_to_date(value):
    """Convierte un valor a datetime.date de forma segura."""
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

        # ✅ Cargar productos desde JSON si es necesario
        if "Productos" in pedido:
            if isinstance(pedido["Productos"], list):
                st.session_state.productos = pedido["Productos"]
            elif isinstance(pedido["Productos"], str) and pedido["Productos"].strip():
                try:
                    st.session_state.productos = json.loads(pedido["Productos"])
                except json.JSONDecodeError:
                    st.session_state.productos = [{"Producto": "", "Tela": "", "PrecioUnitario": 0.0, "Cantidad": 1}]
            else:
                st.session_state.productos = [{"Producto": "", "Tela": "", "PrecioUnitario": 0.0, "Cantidad": 1}]
        else:
            st.session_state.productos = [{"Producto": "", "Tela": "", "PrecioUnitario": 0.0, "Cantidad": 1}]

        # --- BLOQUE DE PRODUCTOS (FUERA DEL FORM) ---
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
                    key=f"mod_producto_{i}"
                )
            with cols[1]:
                st.session_state.productos[i]["Tela"] = st.selectbox(
                    f"Tela {i+1}",
                    telas_lista,
                    index=telas_lista.index(p["Tela"]) if p["Tela"] in telas_lista else 0,
                    key=f"mod_tela_{i}"
                )
            with cols[2]:
                st.session_state.productos[i]["PrecioUnitario"] = st.number_input(
                    f"Precio {i+1}", min_value=0.0, value=float(p.get("PrecioUnitario", 0.0)), key=f"mod_precio_unit_{i}"
                )
            with cols[3]:
                st.session_state.productos[i]["Cantidad"] = st.number_input(
                    f"Cantidad {i+1}", min_value=1, value=int(p.get("Cantidad", 1)), key=f"mod_cantidad_{i}"
                )

            total_productos += st.session_state.productos[i]["PrecioUnitario"] * st.session_state.productos[i]["Cantidad"]

        st.markdown(f"**💰 Total productos: {total_productos:.2f} €**")

        add_col, remove_col = st.columns([1, 1])
        with add_col:
            if st.button("➕ Añadir otro producto", key="mod_add_producto"):
                st.session_state.productos.append({"Producto": "", "Tela": "", "PrecioUnitario": 0.0, "Cantidad": 1})

        with remove_col:
            if len(st.session_state.productos) > 1:
                if st.button("➖ Quitar último producto", key="mod_remove_producto"):
                    st.session_state.productos.pop()

        # --- FORMULARIO PRINCIPAL ---
        with st.form("modificar_pedido_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("ID", value=pedido['ID'], disabled=True, key="mod_id")
                cliente = st.text_input("Cliente*", value=pedido.get('Cliente',''), key="mod_cliente")
                telefono = st.text_input("Teléfono*", value=pedido.get('Telefono',''), key="mod_telefono")
                club = st.text_input("Club*", value=pedido.get('Club',''), key="mod_club")
                descripcion = st.text_area("Descripción", value=pedido.get('Breve Descripción',''), key="mod_descripcion")

            with col2:
                fecha_entrada = st.date_input("Fecha entrada*", value=safe_to_date(pedido.get('Fecha entrada')), key="mod_fecha_entrada")
                tiene_fecha_salida = st.checkbox("Establecer fecha de salida", value=bool(pedido.get('Fecha Salida')), key="mod_tiene_fecha_salida")
                fecha_salida = st.date_input("Fecha salida", value=safe_to_date(pedido.get('Fecha Salida')), key="mod_fecha_salida") if tiene_fecha_salida else None

                precio = st.number_input("Precio total", min_value=0.0, value=total_productos, key="mod_precio")
                precio_factura = st.number_input("Precio factura", min_value=0.0, value=float(pedido.get('Precio Factura', 0) or 0), key="mod_precio_factura")
                tipos_pago = [""] + df_listas['Tipo de pago'].dropna().unique().tolist() if 'Tipo de pago' in df_listas.columns else [""]
                tipo_pago = st.selectbox("Tipo de pago", tipos_pago, index=safe_select_index(tipos_pago, pedido.get('Tipo de pago','')), key="mod_tipo_pago")
                adelanto = st.number_input("Adelanto", min_value=0.0, value=float(pedido.get('Adelanto', 0) or 0), key="mod_adelanto")
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
                if not cliente or not telefono or not club:
                    st.error("Por favor complete los campos obligatorios (*)")
                    return

                if not telefono.isdigit() or len(telefono) != 9:
                    st.error("El teléfono debe contener exactamente 9 dígitos numéricos")
                    return

                # Guardar productos como JSON
                productos_json = json.dumps(st.session_state.productos)

                updated_pedido = {
                    'ID': mod_id,
                    'Productos': productos_json,
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
                    'id_documento_firestore': pedido['id_documento_firestore']
                }

                idx_list = df_pedidos.index[df_pedidos['ID'] == mod_id].tolist()
                if idx_list:
                    df_pedidos.loc[idx_list[0]] = updated_pedido
                    df_pedidos = df_pedidos.where(pd.notna(df_pedidos), None)
                    for c in df_pedidos.columns:
                        df_pedidos[c] = df_pedidos[c].apply(lambda x: None if x is pd.NaT else x)

                    if save_dataframe_firestore(df_pedidos, 'pedidos'):
                        success_placeholder = st.empty()
                        success_placeholder.success(f"Pedido {mod_id} actualizado correctamente!")
                        time.sleep(3)
                        success_placeholder.empty()

                        keys_to_delete = [k for k in st.session_state.keys() if k.startswith("mod_") or k.startswith("modify_")]
                        for k in keys_to_delete:
                            del st.session_state[k]

                        if 'pedido_a_modificar' in st.session_state:
                            del st.session_state['pedido_a_modificar']

                        if 'data' not in st.session_state:
                            st.session_state['data'] = {}
                        st.session_state.data['df_pedidos'] = df_pedidos
                        st.rerun()
                    else:
                        st.error("Error al actualizar el pedido")
                else:
                    st.error("No se encontró el índice del pedido para actualizar.")
