# pages/pedido/eliminar_pedido.py
import streamlit as st
import pandas as pd
import time
import json
from utils.firestore_utils import delete_document_firestore, save_dataframe_firestore
from .helpers import convert_to_firestore_type, safe_select_index

def reindexar_ids_visibles(df_pedidos):
    """
    Reasigna el campo 'ID' (número visible) para que sea consecutivo desde 1,
    SIN TOCAR el id_documento_firestore (ID técnico inmutable).
    """
    if df_pedidos.empty:
        return df_pedidos
    df_pedidos = df_pedidos.sort_values(by="ID").reset_index(drop=True)
    df_pedidos["ID"] = range(1, len(df_pedidos) + 1)
    return df_pedidos

def show_delete(df_pedidos, df_listas):
    st.subheader("Eliminar Pedido")

    del_id = st.number_input("ID del pedido a eliminar:", min_value=1, value=1, key="delete_id_input")
    if st.button("Cargar Pedido", key="load_pedido_delete_button"):
        pedido = df_pedidos[df_pedidos['ID'] == del_id]
        if not pedido.empty:
            st.session_state.pedido_a_eliminar = pedido.iloc[0].to_dict()
            st.success(f"Pedido {del_id} cargado para eliminación")
        else:
            st.warning(f"No existe un pedido con ID {del_id}")
            st.session_state.pedido_a_eliminar = None

    if 'pedido_a_eliminar' in st.session_state and st.session_state.pedido_a_eliminar:
        pedido = st.session_state.pedido_a_eliminar

        # ✅ Inicializar productos desde JSON
        if "Productos" in pedido:
            try:
                productos = (
                    json.loads(pedido["Productos"]) if isinstance(pedido["Productos"], str) and pedido["Productos"].strip()
                    else pedido["Productos"] if isinstance(pedido["Productos"], list)
                    else [{"Producto": "", "Tela": "", "PrecioUnitario": 0.0, "Cantidad": 1}]
                )
            except json.JSONDecodeError:
                productos = [{"Producto": "", "Tela": "", "PrecioUnitario": 0.0, "Cantidad": 1}]
        else:
            productos = [{"Producto": "", "Tela": "", "PrecioUnitario": 0.0, "Cantidad": 1}]

        # --- BLOQUE DE PRODUCTOS (SOLO LECTURA) ---
        st.markdown("### Productos del pedido")
        total_productos = 0.0
        for i, p in enumerate(productos):
            cols = st.columns([3, 3, 2, 2])
            with cols[0]:
                st.text_input(f"Producto {i+1}", value=p.get("Producto", ""), disabled=True, key=f"del_producto_{i}")
            with cols[1]:
                st.text_input(f"Tela {i+1}", value=p.get("Tela", ""), disabled=True, key=f"del_tela_{i}")
            with cols[2]:
                st.number_input(f"Precio {i+1}", value=float(p.get("PrecioUnitario", 0.0)), disabled=True, key=f"del_precio_unit_{i}")
            with cols[3]:
                st.number_input(f"Cantidad {i+1}", value=int(p.get("Cantidad", 1)), disabled=True, key=f"del_cantidad_{i}")

            total_productos += float(p.get("PrecioUnitario", 0.0)) * int(p.get("Cantidad", 1))

        st.markdown(f"**💰 Total productos: {total_productos:.2f} €**")

        # --- FORMULARIO PRINCIPAL (SOLO LECTURA) ---
        with st.form("eliminar_pedido_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("ID", value=pedido['ID'], disabled=True, key="del_id")
                st.text_input("Cliente*", value=pedido.get('Cliente',''), disabled=True, key="del_cliente")
                st.text_input("Teléfono*", value=pedido.get('Telefono',''), disabled=True, key="del_telefono")
                st.text_input("Club*", value=pedido.get('Club',''), disabled=True, key="del_club")
                st.text_area("Descripción", value=pedido.get('Breve Descripción',''), disabled=True, key="del_descripcion")

            with col2:
                st.text_input("Fecha entrada*", value=str(pedido.get('Fecha entrada','')), disabled=True, key="del_fecha_entrada")
                tiene_fecha_salida = bool(pedido.get('Fecha Salida'))
                st.checkbox("Establecer fecha de salida", value=tiene_fecha_salida, disabled=True, key="del_tiene_fecha_salida")
                st.text_input("Fecha salida", value=str(pedido.get('Fecha Salida','')), disabled=True, key="del_fecha_salida")
                st.number_input("Precio total", value=float(pedido.get('Precio', 0.0)), disabled=True, key="del_precio")
                st.number_input("Precio factura", value=float(pedido.get('Precio Factura', 0.0)), disabled=True, key="del_precio_factura")
                
                tipos_pago = [""] + df_listas['Tipo de pago'].dropna().unique().tolist() if 'Tipo de pago' in df_listas.columns else [""]
                tipo_pago_actual = pedido.get('Tipo de pago','')
                st.selectbox("Tipo de pago", tipos_pago, index=tipos_pago.index(tipo_pago_actual) if tipo_pago_actual in tipos_pago else 0, disabled=True, key="del_tipo_pago")
                
                st.number_input("Adelanto", value=float(pedido.get('Adelanto', 0.0)), disabled=True, key="del_adelanto")
                st.text_area("Observaciones", value=pedido.get('Observaciones',''), disabled=True, key="del_observaciones")

            st.write("**Estado del pedido:**")
            estado_cols = st.columns(5)
            with estado_cols[0]:
                st.checkbox("Empezado", value=bool(pedido.get('Inicio Trabajo', False)), disabled=True, key="del_empezado")
            with estado_cols[1]:
                st.checkbox("Terminado", value=bool(pedido.get('Trabajo Terminado', False)), disabled=True, key="del_terminado")
            with estado_cols[2]:
                st.checkbox("Cobrado", value=bool(pedido.get('Cobrado', False)), disabled=True, key="del_cobrado")
            with estado_cols[3]:
                st.checkbox("Retirado", value=bool(pedido.get('Retirado', False)), disabled=True, key="del_retirado")
            with estado_cols[4]:
                st.checkbox("Pendiente", value=bool(pedido.get('Pendiente', False)), disabled=True, key="del_pendiente")

            # ✅ BOTONES
            submit_col, cancel_col = st.columns([1, 1])
            with submit_col:
                eliminar = st.form_submit_button("🗑️ Eliminar Definitivamente", type="primary")
            with cancel_col:
                if st.form_submit_button("🚪 Cancelar"):
                    # Limpiar estado
                    keys_to_delete = [k for k in st.session_state.keys() if k.startswith("del_") or k.startswith("delete_")]
                    for k in keys_to_delete:
                        if k in st.session_state:
                            del st.session_state[k]
                    if 'pedido_a_eliminar' in st.session_state:
                        del st.session_state['pedido_a_eliminar']
                    st.rerun()

        # ✅ PROCESAR ELIMINACIÓN
        if eliminar:
            if not st.session_state.get('confirm_delete_step', False):
                st.session_state.confirm_delete_step = True
                st.warning("⚠️ ¿Estás seguro? Pulsa de nuevo 'Eliminar Definitivamente' para confirmar.")
            else:
                try:
                    doc_id = pedido.get('id_documento_firestore')
                    if not doc_id:
                        st.error("Error: El pedido no tiene ID de documento en Firestore.")
                        return

                    if not delete_document_firestore('pedidos', doc_id):
                        st.error("Error al eliminar el pedido de Firestore.")
                        return

                    # Eliminar del DataFrame
                    df_pedidos = df_pedidos[df_pedidos['ID'] != del_id].reset_index(drop=True)

                    # 🔁 Reindexar IDs
                    df_pedidos = reindexar_ids_visibles(df_pedidos)

                    if not save_dataframe_firestore(df_pedidos, 'pedidos'):
                        st.error("Error al guardar los cambios en Firestore.")
                        return

                    st.success(f"✅ Pedido {del_id} eliminado y lista reindexada correctamente!")
                    st.balloons()
                    time.sleep(2)

                    # Limpiar estado
                    keys_to_delete = [k for k in st.session_state.keys() if k.startswith("del_") or k.startswith("delete_") or k == 'pedido_a_eliminar' or k == 'confirm_delete_step']
                    for k in keys_to_delete:
                        if k in st.session_state:
                            del st.session_state[k]

                    if 'data' not in st.session_state:
                        st.session_state['data'] = {}
                    st.session_state.data['df_pedidos'] = df_pedidos
                    st.rerun()

                except Exception as e:
                    st.error(f"Error al eliminar el pedido: {str(e)}")