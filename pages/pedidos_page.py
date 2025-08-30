
# pages/pedidos_page.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from utils import get_next_id, save_dataframe_firestore, delete_document_firestore

def convert_to_firestore_type(value):
    """Convierte los valores a tipos compatibles con Firestore (anti-NaT)."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    if isinstance(value, str) and value.strip() in ("", "NaT", "nan", "None"):
        return None
    if value is pd.NaT:
        return None

    if isinstance(value, pd.Timestamp):
        if pd.isna(value) or value is pd.NaT:
            return None
        try:
            return value.to_pydatetime()
        except Exception:
            return None

    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime.combine(value, datetime.min.time())

    if isinstance(value, datetime):
        return value

    if isinstance(value, (np.integer, )):
        return int(value)
    if isinstance(value, (np.floating, )):
        return float(value)

    if isinstance(value, (int, float, bool, str)):
        return value

    return str(value)

def _safe_select_index(options_list, current_value):
    """Devuelve un índice seguro para selectbox cuando el valor actual puede no estar en la lista."""
    try:
        return options_list.index(current_value)
    except Exception:
        return 0

def show_pedidos_page(df_pedidos, df_listas):
    # Definir las 4 pestañas
    tab1, tab2, tab3, tab4 = st.tabs(["Crear Pedido", "Consultar Pedidos", "Modificar Pedido", "Eliminar Pedido"])

    # ==============================================
    # Pestaña 1: Crear Pedido
    # ==============================================
    with tab1:
        st.subheader("Crear Nuevo Pedido")

        with st.form("nuevo_pedido_form"):
            col1, col2 = st.columns(2)

            with col1:
                productos = [""] + df_listas['Producto'].dropna().unique().tolist() if 'Producto' in df_listas.columns else [""]
                tallas = [""] + df_listas['Talla'].dropna().unique().tolist() if 'Talla' in df_listas.columns else [""]
                telas = [""] + df_listas['Tela'].dropna().unique().tolist() if 'Tela' in df_listas.columns else [""]
                tipos_pago = [""] + df_listas['Tipo de pago'].dropna().unique().tolist() if 'Tipo de pago' in df_listas.columns else [""]

                producto = st.selectbox("Producto*", productos, key="new_producto")
                cliente = st.text_input("Cliente*", key="new_cliente")
                telefono = st.text_input("Teléfono*", key="new_telefono", max_chars=15)
                club = st.text_input("Club*", key="new_club")
                talla = st.selectbox("Talla", tallas, key="new_talla")
                tela = st.selectbox("Tela", telas, key="new_tela")
                descripcion = st.text_area("Descripción", key="new_descripcion")

            with col2:
                fecha_entrada = st.date_input("Fecha entrada", value=datetime.now().date(), key="new_fecha_entrada")
                # Streamlit no soporta None en todas las versiones; capturamos y normalizamos luego
                fecha_salida = st.date_input("Fecha salida", value=datetime.now().date(), key="new_fecha_salida")
                precio = st.number_input("Precio", min_value=0.0, value=0.0, key="new_precio")
                precio_factura = st.number_input("Precio factura", min_value=0.0, value=0.0, key="new_precio_factura")
                tipo_pago = st.selectbox("Tipo de pago", tipos_pago, key="new_tipo_pago")
                adelanto = st.number_input("Adelanto", min_value=0.0, value=0.0, key="new_adelanto")
                observaciones = st.text_area("Observaciones", key="new_observaciones")

            st.write("**Estado del pedido:**")
            estado_cols = st.columns(5)
            with estado_cols[0]:
                empezado = st.checkbox("Empezado", value=False, key="new_empezado")
            with estado_cols[1]:
                terminado = st.checkbox("Terminado", value=False, key="new_terminado")
            with estado_cols[2]:
                cobrado = st.checkbox("Cobrado", value=False, key="new_cobrado")
            with estado_cols[3]:
                retirado = st.checkbox("Retirado", value=False, key="new_retirado")
            with estado_cols[4]:
                pendiente = st.checkbox("Pendiente", value=False, key="new_pendiente")

            if st.form_submit_button("Guardar Nuevo Pedido"):
                if not cliente or not telefono or not producto or not club:
                    st.error("Por favor complete los campos obligatorios (*)")
                else:
                    # Permitir dejar fecha_salida vacía: si iguales (default), la tratamos como None si el usuario no la tocó
                    try:
                        fecha_salida_final = None if fecha_salida == datetime.now().date() and not st.session_state.get('new_fecha_salida_touched', False) else fecha_salida
                    except Exception:
                        fecha_salida_final = None

                    new_id = get_next_id(df_pedidos, 'ID')
                    new_pedido = {
                        'ID': new_id,
                        'Producto': convert_to_firestore_type(producto),
                        'Cliente': convert_to_firestore_type(cliente),
                        'Telefono': convert_to_firestore_type(telefono),
                        'Club': convert_to_firestore_type(club),
                        'Talla': convert_to_firestore_type(talla),
                        'Tela': convert_to_firestore_type(tela),
                        'Breve Descripción': convert_to_firestore_type(descripcion),
                        'Fecha entrada': convert_to_firestore_type(fecha_entrada),
                        'Fecha Salida': convert_to_firestore_type(fecha_salida_final),
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

                    # Saneamos el DF completo antes de guardar (por si otras filas venían con NaT)
                    df_pedidos = df_pedidos.where(pd.notna(df_pedidos), None)
                    for c in df_pedidos.columns:
                        df_pedidos[c] = df_pedidos[c].apply(lambda x: None if x is pd.NaT else x)

                    if save_dataframe_firestore(df_pedidos, 'pedidos'):
                        st.success(f"Pedido {new_id} creado correctamente!")
                        st.session_state.data['df_pedidos'] = df_pedidos
                        st.rerun()
                    else:
                        st.error("Error al crear el pedido")

    # ==============================================
    # Pestaña 2: Consultar Pedidos
    # ==============================================
    with tab2:
        st.subheader("Consultar Pedidos")

        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            filtro_cliente = st.text_input("Filtrar por cliente")
        with col_f2:
            filtro_club = st.text_input("Filtrar por club")
        with col_f3:
            filtro_telefono = st.text_input("Filtrar por teléfono")
        with col_f4:
            filtro_estado = st.selectbox("Filtrar por estado", options=["", "Pendiente", "Empezado", "Terminado", "Retirado"], key="filtro_estado_consulta")

        df_filtrado = df_pedidos.copy()
        if filtro_cliente:
            df_filtrado = df_filtrado[df_filtrado['Cliente'].str.contains(filtro_cliente, case=False, na=False)]
        if filtro_club:
            df_filtrado = df_filtrado[df_filtrado['Club'].str.contains(filtro_club, case=False, na=False)]
        if filtro_telefono:
            df_filtrado = df_filtrado[df_filtrado['Telefono'].astype(str).str.contains(filtro_telefono, na=False)]
        if filtro_estado:
            if filtro_estado == "Pendiente":
                df_filtrado = df_filtrado[df_filtrado['Pendiente'] == True]
            elif filtro_estado == "Empezado":
                df_filtrado = df_filtrado[df_filtrado['Inicio Trabajo'] == True]
            elif filtro_estado == "Terminado":
                df_filtrado = df_filtrado[df_filtrado['Trabajo Terminado'] == True]
            elif filtro_estado == "Retirado":
                df_filtrado = df_filtrado[df_filtrado['Retirado'] == True]

        if not df_filtrado.empty:
            df_display = df_filtrado.copy()
            for col in ['Fecha entrada', 'Fecha Salida']:
                if col in df_display.columns:
                    df_display[col] = df_display[col].apply(lambda x: str(x)[:10] if pd.notna(x) and str(x) != 'NaT' else '')
            if 'ID' in df_display.columns:
                df_display['ID'] = pd.to_numeric(df_display['ID'], errors='coerce').fillna(0).astype('int64')
            if 'Precio' in df_display.columns:
                df_display['Precio'] = pd.to_numeric(df_display['Precio'], errors='coerce').fillna(0.0)
            for col in ['Pendiente', 'Inicio Trabajo', 'Trabajo Terminado', 'Retirado']:
                if col in df_display.columns:
                    df_display[col] = df_display[col].fillna(False).astype(bool)

            columnas_mostrar = ['ID', 'Producto', 'Cliente', 'Club', 'Telefono', 'Fecha entrada', 'Fecha Salida', 'Precio', 'Pendiente', 'Inicio Trabajo', 'Trabajo Terminado', 'Retirado']
            columnas_disponibles = [col for col in columnas_mostrar if col in df_display.columns]
            st.dataframe(df_display[columnas_disponibles].sort_values('ID', ascending=False), height=600, use_container_width=True)
            st.caption(f"Mostrando {len(df_filtrado)} de {len(df_pedidos)} pedidos")
        else:
            st.info("No se encontraron pedidos con los filtros aplicados")

    # ==============================================
    # Pestaña 3: Modificar Pedido
    # ==============================================
    with tab3:
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

            # Construir listas seguras para selects
            productos = [""] + df_listas['Producto'].dropna().unique().tolist() if 'Producto' in df_listas.columns else [""]
            tallas = [""] + df_listas['Talla'].dropna().unique().tolist() if 'Talla' in df_listas.columns else [""]
            telas = [""] + df_listas['Tela'].dropna().unique().tolist() if 'Tela' in df_listas.columns else [""]
            tipos_pago = [""] + df_listas['Tipo de pago'].dropna().unique().tolist() if 'Tipo de pago' in df_listas.columns else [""]

            with st.form("modificar_pedido_form"):
                col1, col2 = st.columns(2)

                with col1:
                    st.text_input("ID", value=pedido['ID'], disabled=True, key="mod_id")
                    producto = st.selectbox("Producto*", productos, index=_safe_select_index(productos, pedido.get('Producto', '')), key="mod_producto")
                    cliente = st.text_input("Cliente*", value=pedido.get('Cliente', ''), key="mod_cliente")
                    telefono = st.text_input("Teléfono*", value=pedido.get('Telefono', ''), key="mod_telefono")
                    club = st.text_input("Club*", value=pedido.get('Club', ''), key="mod_club")
                    talla = st.selectbox("Talla", tallas, index=_safe_select_index(tallas, pedido.get('Talla', '')), key="mod_talla")
                    tela = st.selectbox("Tela", telas, index=_safe_select_index(telas, pedido.get('Tela', '')), key="mod_tela")
                    descripcion = st.text_area("Descripción", value=pedido.get('Breve Descripción', ''), key="mod_descripcion")

                with col2:
                    fe_in = pedido.get('Fecha entrada', '')
                    fe_out = pedido.get('Fecha Salida', '')
                    fe_in_val = datetime.strptime(fe_in, '%Y-%m-%d').date() if fe_in else datetime.now().date()
                    fe_out_val = datetime.strptime(fe_out, '%Y-%m-%d').date() if fe_out else datetime.now().date()
                    fecha_entrada = st.date_input("Fecha entrada*", value=fe_in_val, key="mod_fecha_entrada")
                    fecha_salida = st.date_input("Fecha salida", value=fe_out_val, key="mod_fecha_salida")
                    precio = st.number_input("Precio*", min_value=0.0, value=float(pedido.get('Precio', 0) or 0), key="mod_precio")
                    precio_factura = st.number_input("Precio factura", min_value=0.0, value=float(pedido.get('Precio Factura', 0) or 0), key="mod_precio_factura")
                    tipo_pago = st.selectbox("Tipo de pago", tipos_pago, index=_safe_select_index(tipos_pago, pedido.get('Tipo de pago', '')), key="mod_tipo_pago")
                    adelanto = st.number_input("Adelanto", min_value=0.0, value=float(pedido.get('Adelanto', 0) or 0), key="mod_adelanto")
                    observaciones = st.text_area("Observaciones", value=pedido.get('Observaciones', ''), key="mod_observaciones")

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
                    else:
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

                            # saneo global
                            df_pedidos = df_pedidos.where(pd.notna(df_pedidos), None)
                            for c in df_pedidos.columns:
                                df_pedidos[c] = df_pedidos[c].apply(lambda x: None if x is pd.NaT else x)

                            if save_dataframe_firestore(df_pedidos, 'pedidos'):
                                st.success(f"Pedido {mod_id} actualizado correctamente!")
                                st.session_state.pedido_a_modificar = None
                                st.session_state.data['df_pedidos'] = df_pedidos
                                st.rerun()
                            else:
                                st.error("Error al actualizar el pedido")
                        else:
                            st.error("No se encontró el índice del pedido para actualizar.")

    # ==============================================
    # Pestaña 4: Eliminar Pedido
    # ==============================================
    with tab4:
        st.subheader("Eliminar Pedido")

        del_id = st.number_input("ID del pedido a eliminar:", min_value=1, key="delete_id_input")

        if st.button("Buscar Pedido", key="search_pedido_button"):
            pedido = df_pedidos[df_pedidos['ID'] == del_id]
            if not pedido.empty:
                st.session_state.pedido_a_eliminar = pedido.iloc[0].to_dict()
                st.success(f"Pedido {del_id} encontrado")
            else:
                st.warning(f"No existe un pedido con ID {del_id}")
                st.session_state.pedido_a_eliminar = None

        if 'pedido_a_eliminar' in st.session_state and st.session_state.pedido_a_eliminar:
            pedido = st.session_state.pedido_a_eliminar

            st.warning("⚠️ **Detalles del pedido a eliminar:**")
            st.json({
                "ID": pedido['ID'],
                "Cliente": pedido['Cliente'],
                "Producto": pedido['Producto'],
                "Fecha entrada": str(pedido['Fecha entrada']),
                "Precio": pedido['Precio']
            })

            confirmacion = st.checkbox("Confirmo que deseo eliminar este pedido permanentemente", key="confirm_delete")

            if confirmacion:
                if st.button("Eliminar Definitivamente", type="primary", key="confirm_delete_button"):
                    try:
                        df_pedidos = df_pedidos[df_pedidos['ID'] != del_id]
                        doc_id = pedido['id_documento_firestore']
                        if delete_document_firestore('pedidos', doc_id):
                            st.session_state.data['df_pedidos'] = df_pedidos
                            if save_dataframe_firestore(df_pedidos, 'pedidos'):
                                st.success(f"Pedido {del_id} eliminado correctamente!")
                                st.session_state.pedido_a_eliminar = None
                                st.rerun()
                            else:
                                st.error("Error al guardar los cambios en Firestore")
                        else:
                            st.error("Error al eliminar el pedido de Firestore")
                    except Exception as e:
                        st.error(f"Error al eliminar el pedido: {str(e)}")
