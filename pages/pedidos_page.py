# Archivo: pages/pedidos_page.py

import streamlit as st
import pandas as pd
from datetime import date
from utils.firestore_utils import save_dataframe_firestore, delete_document_firestore, get_next_id
import re

def limpiar_telefono(telefono):
    """Limpia y valida un número de teléfono."""
    if pd.isna(telefono):
        return None
    telefono_str = str(telefono).strip()
    telefono_limpio = re.sub(r'\D', '', telefono_str)
    if len(telefono_limpio) == 9:
        return telefono_limpio
    return None

def highlight_pedidos_rows(row):
    """Estiliza las filas del DataFrame de pedidos según su estado."""
    color = ''
    if row['Retirado'] == True:
        color = 'background-color: #d4edda;'
    elif row['Cobrado'] == True:
        color = 'background-color: #cce5ff;'
    elif row['Trabajo Terminado'] == True:
        color = 'background-color: #fff3cd;'
    elif row['Inicio Trabajo'] == True:
        color = 'background-color: #d1ecf1;'
    return [color] * len(row)

def pedidos_page_content(df_pedidos, df_listas):
    """
    Función principal que renderiza la interfaz completa de la sección de Pedidos.
    """
    st.header("Gestión de Pedidos")
    tab_home, tab_pedidos_add, tab_modificar, tab_eliminar = st.tabs(["Ver Pedidos", "Añadir Pedido", "Modificar Pedido", "Eliminar Pedido"])
    
    with tab_home:
        st.subheader("Resumen de Pedidos")
        st.session_state.current_summary_view = st.radio(
            "Filtrar por estado:",
            ["Todos los pedidos", "Pedidos Empezados", "Pedidos Terminados", "Pedidos Cobrados", "Pedidos Retirados", "Pedidos Pendientes", "Pedidos sin estado específico"],
            key="summary_radio_buttons"
        )
        
        filtered_df = pd.DataFrame()
        if st.session_state.current_summary_view == "Todos los pedidos":
            filtered_df = df_pedidos
        elif st.session_state.current_summary_view == "Pedidos Empezados":
            filtered_df = df_pedidos[df_pedidos['Inicio Trabajo'] == True]
        elif st.session_state.current_summary_view == "Pedidos Terminados":
            filtered_df = df_pedidos[df_pedidos['Trabajo Terminado'] == True]
        elif st.session_state.current_summary_view == "Pedidos Cobrados":
            filtered_df = df_pedidos[df_pedidos['Cobrado'] == True]
        elif st.session_state.current_summary_view == "Pedidos Retirados":
            filtered_df = df_pedidos[df_pedidos['Retirado'] == True]
        elif st.session_state.current_summary_view == "Pedidos Pendientes":
            filtered_df = df_pedidos[df_pedidos['Pendiente'] == True]
        elif st.session_state.current_summary_view == "Pedidos sin estado específico":
            filtered_df = df_pedidos[
                (df_pedidos['Inicio Trabajo'] == False) &
                (df_pedidos['Trabajo Terminado'] == False) &
                (df_pedidos['Pendiente'] == False)
            ]
        
        if not filtered_df.empty:
            filtered_df_sorted = filtered_df.sort_values(by='ID', ascending=False)
            new_column_order = [
                'ID', 'Producto', 'Cliente', 'Club', 'Telefono', 'Breve Descripción',
                'Fecha entrada', 'Fecha Salida', 'Precio', 'Precio Factura',
                'Tipo de pago', 'Adelanto', 'Observaciones'
            ]
            remaining_columns = [col for col in filtered_df_sorted.columns if col not in new_column_order and col != 'id_documento_firestore']
            final_column_order = new_column_order + remaining_columns
            filtered_df_reordered = filtered_df_sorted[final_column_order]
            st.dataframe(
                filtered_df_reordered.style.apply(highlight_pedidos_rows, axis=1), 
                use_container_width=True, 
                height=500,
                hide_index=True
            )
        else:
            st.info("No hay pedidos para esta vista.")
            
    with tab_pedidos_add:
        st.subheader("Añadir Nuevo Pedido")
        with st.form("form_add_pedido", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                producto_options = [""] + df_listas['Producto'].dropna().unique().tolist()
                producto_add = st.selectbox("Producto", options=producto_options, key="add_producto")
                cliente_add = st.text_input("Cliente", key="add_cliente")
                telefono_add = st.text_input("Teléfono (9 dígitos)", help="Debe contener exactamente 9 dígitos numéricos", key="add_telefono")
                club_add = st.text_input("Club", key="add_club")
                talla_options = [""] + df_listas['Talla'].dropna().unique().tolist()
                talla_add = st.selectbox("Talla", options=talla_options, key="add_talla")
                tela_options = [""] + df_listas['Tela'].dropna().unique().tolist()
                tela_add = st.selectbox("Tela", options=tela_options, key="add_tela")
                breve_descripcion_add = st.text_area("Breve Descripción", key="add_breve_descripcion")
            with col2:
                fecha_entrada_add = st.date_input("Fecha entrada", value=date.today(), key="add_fecha_entrada")
                fecha_salida_add = st.date_input("Fecha Salida", value=None, key="add_fecha_salida")
                precio_add = st.number_input("Precio", min_value=0.0, format="%.2f", key="add_precio")
                precio_factura_add = st.number_input("Precio Factura", min_value=0.0, format="%.2f", key="add_precio_factura")
                tipo_pago_options = [""] + df_listas['Tipo de pago'].dropna().unique().tolist()
                tipo_pago_add = st.selectbox("Tipo de Pago", options=tipo_pago_options, key="add_tipo_pago")
                adelanto_add_str = st.text_input("Adelanto (opcional)", key="add_adelanto_str")
                observaciones_add = st.text_area("Observaciones", key="add_observaciones")
            
            st.write("---")
            st.write("**Estado del Pedido:**")
            col_chk1, col_chk2, col_chk3, col_chk4, col_chk5 = st.columns(5)
            with col_chk1:
                ch_empezado_add = st.checkbox("Empezado", key="add_ch_empezado")
            with col_chk2:
                ch_trabajo_terminado_add = st.checkbox("Trabajo Terminado", key="add_ch_trabajo_terminado")
            with col_chk3:
                ch_cobrado_add = st.checkbox("Cobrado", key="add_ch_cobrado")
            with col_chk4:
                ch_retirado_add = st.checkbox("Retirado", key="add_ch_retirado")
            with col_chk5:
                ch_pendiente_add = st.checkbox("Pendiente", key="add_ch_pendiente")

            submitted = st.form_submit_button("Añadir Pedido")
            if submitted:
                telefono_ingresado = st.session_state.add_telefono.strip()
                telefono_limpio = limpiar_telefono(telefono_ingresado) if telefono_ingresado else None
                
                if telefono_ingresado and not telefono_limpio:
                    st.error("El teléfono debe contener exactamente 9 dígitos numéricos")
                    st.stop()

                if ch_empezado_add and ch_trabajo_terminado_add:
                    st.error("Error: Un pedido no puede estar 'Empezado' y 'Trabajo Terminado' al mismo tiempo.")
                    st.stop()

                adelanto_add = None
                if adelanto_add_str:
                    try:
                        adelanto_add = float(adelanto_add_str)
                    except ValueError:
                        st.error("Por favor, introduce un número válido para 'Adelanto' o déjalo vacío.")
                        st.stop()
                
                new_row = pd.DataFrame([{
                    'ID': get_next_id(df_pedidos, 'ID'),
                    'Producto': st.session_state.add_producto if st.session_state.add_producto != "" else None,
                    'Cliente': st.session_state.add_cliente,
                    'Telefono': telefono_limpio,
                    'Club': st.session_state.add_club,
                    'Talla': st.session_state.add_talla if st.session_state.add_talla != "" else None,
                    'Tela': st.session_state.add_tela if st.session_state.add_tela != "" else None,
                    'Breve Descripción': st.session_state.add_breve_descripcion,
                    'Fecha entrada': st.session_state.add_fecha_entrada,
                    'Fecha Salida': st.session_state.add_fecha_salida,
                    'Precio': precio_add,
                    'Precio Factura': precio_factura_add,
                    'Tipo de pago': tipo_pago_add if tipo_pago_add != "" else None,
                    'Adelanto': adelanto_add,
                    'Observaciones': observaciones_add,
                    'Inicio Trabajo': ch_empezado_add,
                    'Cobrado': ch_cobrado_add,
                    'Retirado': ch_retirado_add,
                    'Pendiente': ch_pendiente_add,
                    'Trabajo Terminado': ch_trabajo_terminado_add
                }])
                st.session_state.data['df_pedidos'] = pd.concat([st.session_state.data['df_pedidos'], new_row], ignore_index=True)
                if save_dataframe_firestore(st.session_state.data['df_pedidos'], 'pedidos'):
                    st.success(f"Pedido añadido con éxito! ID: {new_row.iloc[0]['ID']}")
                    st.session_state.modifying_pedido = None
                    st.rerun()
                else:
                    st.error("Error al añadir el pedido.")
    
    with tab_modificar:
        st.subheader("Modificar Pedido")
        modify_search_id = st.number_input("Introduce el ID del pedido a modificar:", min_value=1, value=st.session_state.get('last_searched_modify_id', 1), key="modify_search_id_input")
        if st.button("Buscar para Modificar", key="modify_search_button"):
            found_pedido_row = df_pedidos[df_pedidos['ID'] == modify_search_id]
            if not found_pedido_row.empty:
                st.session_state.modifying_pedido = found_pedido_row.iloc[0].to_dict()
                st.session_state.last_searched_modify_id = modify_search_id
                st.success(f"Pedido {modify_search_id} encontrado. Modifica a continuación.")
            else:
                st.session_state.modifying_pedido = None
                st.session_state.last_searched_modify_id = modify_search_id
                st.warning(f"No se encontró ningún pedido con el ID {modify_search_id}.")
        
        if st.session_state.get('modifying_pedido'):
            current_pedido = st.session_state.modifying_pedido
            st.write(f"Modificando Pedido ID: **{current_pedido['ID']}**")
            with st.form("form_modificar_pedido", clear_on_submit=False):
                col1_mod, col2_mod = st.columns(2)
                with col1_mod:
                    st.text_input("ID", value=current_pedido['ID'], key="mod_id", disabled=True)
                    producto_options = [""] + df_listas['Producto'].dropna().unique().tolist()
                    current_producto_val = current_pedido['Producto'] if pd.notna(current_pedido['Producto']) else ""
                    current_producto_idx = producto_options.index(current_producto_val) if current_producto_val in producto_options else 0
                    producto_mod = st.selectbox("Producto", options=producto_options, index=current_producto_idx, key="mod_producto")
                    cliente_mod = st.text_input("Cliente", value=current_pedido['Cliente'], key="mod_cliente")
                    telefono_actual = str(current_pedido.get('Telefono', '')).strip()
                    telefono_mod = st.text_input("Teléfono (9 dígitos)", value=telefono_actual, key="mod_telefono",
                                                help="Debe contener exactamente 9 dígitos numéricos",
                                                max_chars=9)
                    club_mod = st.text_input("Club", value=current_pedido['Club'], key="mod_club")
                    talla_options = [""] + df_listas['Talla'].dropna().unique().tolist()
                    current_talla_val = current_pedido['Talla'] if pd.notna(current_pedido['Talla']) else ""
                    current_talla_idx = talla_options.index(current_talla_val) if current_talla_val in talla_options else 0
                    talla_mod = st.selectbox("Talla", options=talla_options, index=current_talla_idx, key="mod_talla")
                    tela_options = [""] + df_listas['Tela'].dropna().unique().tolist()
                    current_tela_val = current_pedido['Tela'] if pd.notna(current_pedido['Tela']) else ""
                    current_tela_idx = tela_options.index(current_tela_val) if current_tela_val in tela_options else 0
                    tela_mod = st.selectbox("Tela", options=tela_options, index=current_tela_idx, key="mod_tela")
                    breve_descripcion_mod = st.text_area("Breve Descripción", value=current_pedido['Breve Descripción'], key="mod_breve_descripcion")
                with col2_mod:
                    current_fecha_entrada = current_pedido.get('Fecha entrada')
                    fecha_entrada_valor = current_fecha_entrada if pd.notna(current_fecha_entrada) and isinstance(current_fecha_entrada, date) else None
                    fecha_entrada_mod = st.date_input("Fecha entrada", value=fecha_entrada_valor, key="mod_fecha_entrada")
                    current_fecha_salida = current_pedido.get('Fecha Salida')
                    fecha_salida_valor = current_fecha_salida if pd.notna(current_fecha_salida) and isinstance(current_fecha_salida, date) else None
                    fecha_salida_mod = st.date_input("Fecha Salida", value=fecha_salida_valor, key="mod_fecha_salida")
                    precio_mod = st.number_input("Precio", min_value=0.0, format="%.2f", value=float(current_pedido['Precio']) if pd.notna(current_pedido['Precio']) else 0.0, key="mod_precio")
                    precio_factura_mod = st.number_input("Precio Factura", min_value=0.0, format="%.2f", value=float(current_pedido['Precio Factura']) if pd.notna(current_pedido['Precio Factura']) else 0.0, key="mod_precio_factura")
                    tipo_pago_options = [""] + df_listas['Tipo de pago'].dropna().unique().tolist()
                    current_tipo_pago_val = current_pedido['Tipo de pago'] if pd.notna(current_pedido['Tipo de pago']) else ""
                    current_tipo_pago_idx = tipo_pago_options.index(current_tipo_pago_val) if current_tipo_pago_val in tipo_pago_options else 0
                    tipo_pago_mod = st.selectbox("Tipo de Pago", options=tipo_pago_options, index=current_tipo_pago_idx, key="mod_tipo_pago")
                    adelanto_mod_str = st.text_input("Adelanto (opcional)", value=str(current_pedido['Adelanto']) if pd.notna(current_pedido['Adelanto']) else "", key="mod_adelanto_str")
                    observaciones_mod = st.text_area("Observaciones", value=current_pedido['Observaciones'], key="mod_observaciones")

                st.write("---")
                st.write("**Estado del Pedido:**")
                col_chk1_mod, col_chk2_mod, col_chk3_mod, col_chk4_mod, col_chk5_mod = st.columns(5)
                with col_chk1_mod:
                    ch_empezado_mod = st.checkbox("Empezado", value=current_pedido['Inicio Trabajo'], key="mod_ch_empezado")
                with col_chk2_mod:
                    ch_trabajo_terminado_mod = st.checkbox("Trabajo Terminado", value=current_pedido['Trabajo Terminado'], key="mod_ch_trabajo_terminado")
                with col_chk3_mod:
                    ch_cobrado_mod = st.checkbox("Cobrado", value=current_pedido['Cobrado'], key="mod_ch_cobrado")
                with col_chk4_mod:
                    ch_retirado_mod = st.checkbox("Retirado", value=current_pedido['Retirado'], key="mod_ch_retirado")
                with col_chk5_mod:
                    ch_pendiente_mod = st.checkbox("Pendiente", value=current_pedido['Pendiente'], key="mod_ch_pendiente")
                submitted_mod = st.form_submit_button("Guardar Cambios")

                if submitted_mod:
                    telefono_mod_ingresado = st.session_state.mod_telefono.strip()
                    telefono_mod_limpio = limpiar_telefono(telefono_mod_ingresado) if telefono_mod_ingresado else None

                    if telefono_mod_ingresado and not telefono_mod_limpio:
                        st.error("El teléfono debe contener exactamente 9 dígitos numéricos")
                        st.stop()
                    if ch_empezado_mod and ch_trabajo_terminado_mod:
                        st.error("Error: Un pedido no puede estar 'Empezado' y 'Trabajo Terminado' al mismo tiempo.")
                        st.stop()
                    adelanto_mod = None
                    if adelanto_mod_str:
                        try:
                            adelanto_mod = float(adelanto_mod_str)
                        except ValueError:
                            st.error("Por favor, introduce un número válido para 'Adelanto' o déjalo vacío.")
                            st.stop()
                    
                    row_index = df_pedidos[df_pedidos['ID'] == current_pedido['ID']].index[0]
                    st.session_state.data['df_pedidos'].loc[row_index] = {
                        'ID': current_pedido['ID'],
                        'Producto': producto_mod if producto_mod != "" else None,
                        'Cliente': cliente_mod,
                        'Telefono': telefono_mod_limpio,
                        'Club': club_mod,
                        'Talla': talla_mod if talla_mod != "" else None,
                        'Tela': tela_mod if tela_mod != "" else None,
                        'Breve Descripción': breve_descripcion_mod,
                        'Fecha entrada': st.session_state.mod_fecha_entrada,
                        'Fecha Salida': st.session_state.mod_fecha_salida,
                        'Precio': precio_mod,
                        'Precio Factura': precio_factura_mod,
                        'Tipo de pago': tipo_pago_mod if tipo_pago_mod != "" else None,
                        'Adelanto': adelanto_mod,
                        'Observaciones': observaciones_mod,
                        'Inicio Trabajo': ch_empezado_mod,
                        'Cobrado': ch_cobrado_mod,
                        'Retirado': ch_retirado_mod,
                        'Pendiente': ch_pendiente_mod,
                        'Trabajo Terminado': ch_trabajo_terminado_mod
                    }
                    if save_dataframe_firestore(st.session_state.data['df_pedidos'], 'pedidos'):
                        st.success(f"Pedido {current_pedido['ID']} modificado con éxito!")
                        st.session_state.modifying_pedido = None
                        st.session_state.last_searched_modify_id = 1
                        st.rerun()
                    else:
                        st.error("Error al modificar el pedido.")
    
    with tab_eliminar:
        st.subheader("Eliminar Pedido")
        delete_id = st.number_input("Introduce el ID del pedido a eliminar:", min_value=1, key="delete_id")

        if st.button("Buscar para Eliminar"):
            found_pedido = df_pedidos[df_pedidos['ID'] == delete_id]
            if not found_pedido.empty:
                st.session_state.pedido_a_eliminar = found_pedido.iloc[0].to_dict()
                st.warning(f"Se va a eliminar el pedido con ID {delete_id} de '{st.session_state.pedido_a_eliminar.get('Cliente', 'N/A')}'")
                st.dataframe(found_pedido)
            else:
                st.error("No se encontró un pedido con ese ID.")
                st.session_state.pedido_a_eliminar = None
        
        if st.session_state.get('pedido_a_eliminar'):
            if st.button("Confirmar Eliminación", key="confirmar_eliminar_pedido"):
                try:
                    doc_id_firestore = st.session_state.pedido_a_eliminar.get('id_documento_firestore')
                    if delete_document_firestore('pedidos', doc_id_firestore):
                        st.success(f"Pedido {delete_id} eliminado con éxito!")
                        st.session_state.pedido_a_eliminar = None
                        st.rerun()
                    else:
                        st.error("Error al eliminar el pedido de Firestore.")
                except Exception as e:
                    st.error(f"Ocurrió un error inesperado al eliminar el pedido: {e}")
                    st.session_state.pedido_a_eliminar = None