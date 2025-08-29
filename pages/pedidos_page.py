# pages/pedidos_page.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils import get_next_id, save_dataframe_firestore, delete_document_firestore

def show_pedidos_page(df_pedidos, df_listas):
    tab1, tab2, tab3, tab4 = st.tabs(["Crear Pedido", "Consultar Pedidos", "Modificar Pedido", "Eliminar Pedido"])

    # ==============================================
    # Pestaña 1: Crear Pedido
    # ==============================================
    with tab1:
        st.subheader("Crear Nuevo Pedido")
        
        with st.form("nuevo_pedido_form"):
            col1, col2 = st.columns(2)
            with col1:
                producto = st.selectbox("Producto", df_listas[df_listas['Tipo'] == 'Producto']['Nombre'], key="np_producto")
                cliente = st.selectbox("Cliente", df_listas[df_listas['Tipo'] == 'Cliente']['Nombre'], key="np_cliente")
                club = st.selectbox("Club", df_listas[df_listas['Tipo'] == 'Club']['Nombre'], key="np_club")
                telefono = st.text_input("Teléfono", key="np_telefono")
                talla = st.text_input("Talla", key="np_talla")
                tela = st.text_input("Tela", key="np_tela")
                descripcion = st.text_area("Breve Descripción", key="np_descripcion")

            with col2:
                precio = st.number_input("Precio", min_value=0.0, step=1.0, key="np_precio")
                precio_factura = st.number_input("Precio Factura", min_value=0.0, step=1.0, key="np_precio_factura")
                tipo_pago = st.selectbox("Tipo de pago", ['En efectivo', 'Tarjeta'], key="np_tipo_pago")
                adelanto = st.number_input("Adelanto", min_value=0.0, step=1.0, key="np_adelanto")
                fecha_entrada = st.date_input("Fecha entrada", key="np_fecha_entrada")
                fecha_salida = st.date_input("Fecha Salida", value=None, key="np_fecha_salida")
                observaciones = st.text_area("Observaciones", key="np_observaciones")

            submitted = st.form_submit_button("Crear Pedido")
            if submitted:
                # CORRECCIÓN: Se eliminan las llamadas a la función de conversión aquí.
                # La función save_dataframe_firestore() se encarga de la conversión.
                
                next_id = get_next_id(df_pedidos, 'ID')
                new_row = pd.DataFrame([{
                    'ID': next_id,
                    'Producto': producto,
                    'Cliente': cliente,
                    'Club': club,
                    'Telefono': telefono,
                    'Talla': talla,
                    'Tela': tela,
                    'Breve Descripción': descripcion,
                    'Fecha entrada': fecha_entrada,
                    'Fecha Salida': fecha_salida,
                    'Precio': precio,
                    'Precio Factura': precio_factura,
                    'Tipo de pago': tipo_pago,
                    'Adelanto': adelanto,
                    'Observaciones': observaciones,
                    'Inicio Trabajo': False,
                    'Cobrado': False,
                    'Retirado': False,
                    'Pendiente': False,
                    'Trabajo Terminado': False
                }])
                
                df_pedidos = pd.concat([df_pedidos, new_row], ignore_index=True)
                
                if save_dataframe_firestore(df_pedidos, 'pedidos'):
                    st.success(f"Pedido {next_id} creado con éxito!")
                    st.session_state.data['df_pedidos'] = df_pedidos
                    st.rerun()
                else:
                    st.error("Error al crear el pedido.")

    # ==============================================
    # Pestaña 2: Consultar Pedidos
    # ==============================================
    with tab2:
        st.subheader("Consultar y Filtrar Pedidos")

        with st.expander("Opciones de Filtrado"):
            col_filt1, col_filt2, col_filt3 = st.columns(3)
            with col_filt1:
                filtro_id = st.text_input("Filtrar por ID")
            with col_filt2:
                filtro_cliente = st.selectbox("Filtrar por Cliente", ["Todos"] + list(df_pedidos['Cliente'].unique()))
            with col_filt3:
                filtro_club = st.selectbox("Filtrar por Club", ["Todos"] + list(df_pedidos['Club'].unique()))

        df_filtrado = df_pedidos.copy()
        if filtro_id:
            df_filtrado = df_filtrado[df_filtrado['ID'].astype(str).str.contains(filtro_id, case=False, na=False)]
        if filtro_cliente != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Cliente'] == filtro_cliente]
        if filtro_club != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Club'] == filtro_club]

        st.subheader(f"Pedidos ({len(df_filtrado)})")

        columnas_disponibles = [col for col in df_filtrado.columns if col not in ['id_documento_firestore']]
        st.dataframe(
            df_filtrado[columnas_disponibles].sort_values('ID', ascending=False),
            height=600,
            use_container_width=True
        )

    # ==============================================
    # Pestaña 3: Modificar Pedido
    # ==============================================
    with tab3:
        st.subheader("Modificar Pedido Existente")
        edit_id = st.number_input("Introduce el ID del pedido a modificar", min_value=1, step=1, key="edit_id")
        
        pedido_a_modificar = df_pedidos[df_pedidos['ID'] == edit_id]

        if not pedido_a_modificar.empty:
            st.success(f"Pedido {edit_id} encontrado. Puedes modificarlo a continuación.")
            
            with st.form("modificar_pedido_form"):
                pedido = pedido_a_modificar.iloc[0]
                
                col_mod1, col_mod2 = st.columns(2)
                with col_mod1:
                    mod_producto = st.selectbox("Producto", [""] + list(df_listas[df_listas['Tipo'] == 'Producto']['Nombre']), index=[""] + list(df_listas[df_listas['Tipo'] == 'Producto']['Nombre']).index(pedido['Producto']) if pedido['Producto'] in list(df_listas[df_listas['Tipo'] == 'Producto']['Nombre']) else 0, key="mod_producto")
                    mod_cliente = st.selectbox("Cliente", [""] + list(df_listas[df_listas['Tipo'] == 'Cliente']['Nombre']), index=[""] + list(df_listas[df_listas['Tipo'] == 'Cliente']['Nombre']).index(pedido['Cliente']) if pedido['Cliente'] in list(df_listas[df_listas['Tipo'] == 'Cliente']['Nombre']) else 0, key="mod_cliente")
                    mod_club = st.selectbox("Club", [""] + list(df_listas[df_listas['Tipo'] == 'Club']['Nombre']), index=[""] + list(df_listas[df_listas['Tipo'] == 'Club']['Nombre']).index(pedido['Club']) if pedido['Club'] in list(df_listas[df_listas['Tipo'] == 'Club']['Nombre']) else 0, key="mod_club")
                    mod_telefono = st.text_input("Teléfono", value=pedido['Telefono'], key="mod_telefono")
                    mod_talla = st.text_input("Talla", value=pedido['Talla'], key="mod_talla")
                    mod_tela = st.text_input("Tela", value=pedido['Tela'], key="mod_tela")
                    mod_descripcion = st.text_area("Breve Descripción", value=pedido['Breve Descripción'], key="mod_descripcion")
                with col_mod2:
                    mod_precio = st.number_input("Precio", value=float(pedido['Precio']), step=1.0, key="mod_precio")
                    mod_precio_factura = st.number_input("Precio Factura", value=float(pedido['Precio Factura']), step=1.0, key="mod_precio_factura")
                    mod_tipo_pago = st.selectbox("Tipo de pago", ['En efectivo', 'Tarjeta'], index=0 if pedido['Tipo de pago'] == 'En efectivo' else 1, key="mod_tipo_pago")
                    mod_adelanto = st.number_input("Adelanto", value=float(pedido['Adelanto']), step=1.0, key="mod_adelanto")
                    mod_fecha_entrada = st.date_input("Fecha entrada", value=pedido['Fecha entrada'], key="mod_fecha_entrada")
                    mod_fecha_salida = st.date_input("Fecha Salida", value=pedido['Fecha Salida'], key="mod_fecha_salida")
                    mod_observaciones = st.text_area("Observaciones", value=pedido['Observaciones'], key="mod_observaciones")
                
                col_mod_estado1, col_mod_estado2, col_mod_estado3, col_mod_estado4, col_mod_estado5 = st.columns(5)
                with col_mod_estado1:
                    mod_inicio_trabajo = st.checkbox("Inicio Trabajo", value=pedido['Inicio Trabajo'], key="mod_inicio_trabajo")
                with col_mod_estado2:
                    mod_cobrado = st.checkbox("Cobrado", value=pedido['Cobrado'], key="mod_cobrado")
                with col_mod_estado3:
                    mod_retirado = st.checkbox("Retirado", value=pedido['Retirado'], key="mod_retirado")
                with col_mod_estado4:
                    mod_pendiente = st.checkbox("Pendiente", value=pedido['Pendiente'], key="mod_pendiente")
                with col_mod_estado5:
                    mod_trabajo_terminado = st.checkbox("Trabajo Terminado", value=pedido['Trabajo Terminado'], key="mod_trabajo_terminado")

                modified_submitted = st.form_submit_button("Guardar Cambios")
                if modified_submitted:
                    # CORRECCIÓN: Se eliminan las llamadas a la función de conversión aquí.
                    # La función save_dataframe_firestore() se encarga de la conversión.
                    
                    df_pedidos.loc[df_pedidos['ID'] == edit_id, 'Producto'] = mod_producto
                    df_pedidos.loc[df_pedidos['ID'] == edit_id, 'Cliente'] = mod_cliente
                    df_pedidos.loc[df_pedidos['ID'] == edit_id, 'Club'] = mod_club
                    df_pedidos.loc[df_pedidos['ID'] == edit_id, 'Telefono'] = mod_telefono
                    df_pedidos.loc[df_pedidos['ID'] == edit_id, 'Talla'] = mod_talla
                    df_pedidos.loc[df_pedidos['ID'] == edit_id, 'Tela'] = mod_tela
                    df_pedidos.loc[df_pedidos['ID'] == edit_id, 'Breve Descripción'] = mod_descripcion
                    df_pedidos.loc[df_pedidos['ID'] == edit_id, 'Fecha entrada'] = mod_fecha_entrada
                    df_pedidos.loc[df_pedidos['ID'] == edit_id, 'Fecha Salida'] = mod_fecha_salida
                    df_pedidos.loc[df_pedidos['ID'] == edit_id, 'Precio'] = mod_precio
                    df_pedidos.loc[df_pedidos['ID'] == edit_id, 'Precio Factura'] = mod_precio_factura
                    df_pedidos.loc[df_pedidos['ID'] == edit_id, 'Tipo de pago'] = mod_tipo_pago
                    df_pedidos.loc[df_pedidos['ID'] == edit_id, 'Adelanto'] = mod_adelanto
                    df_pedidos.loc[df_pedidos['ID'] == edit_id, 'Observaciones'] = mod_observaciones
                    df_pedidos.loc[df_pedidos['ID'] == edit_id, 'Inicio Trabajo'] = mod_inicio_trabajo
                    df_pedidos.loc[df_pedidos['ID'] == edit_id, 'Cobrado'] = mod_cobrado
                    df_pedidos.loc[df_pedidos['ID'] == edit_id, 'Retirado'] = mod_retirado
                    df_pedidos.loc[df_pedidos['ID'] == edit_id, 'Pendiente'] = mod_pendiente
                    df_pedidos.loc[df_pedidos['ID'] == edit_id, 'Trabajo Terminado'] = mod_trabajo_terminado

                    if save_dataframe_firestore(df_pedidos, 'pedidos'):
                        st.success(f"Pedido {edit_id} modificado con éxito!")
                        st.session_state.data['df_pedidos'] = df_pedidos
                        st.rerun()
                    else:
                        st.error("Error al guardar los cambios en Firestore.")
        else:
            st.info("Introduce un ID válido para modificar un pedido.")

    # ==============================================
    # Pestaña 4: Eliminar Pedido
    # ==============================================
    with tab4:
        st.subheader("Eliminar Pedido Existente")
        delete_id = st.number_input("Introduce el ID del pedido a eliminar", min_value=1, step=1, key="delete_id")

        pedido_a_eliminar = df_pedidos[df_pedidos['ID'] == delete_id]

        if not pedido_a_eliminar.empty:
            st.warning(f"¿Estás seguro de que deseas eliminar el pedido con ID {delete_id}? Esta acción es irreversible.")
            pedido = pedido_a_eliminar.iloc[0].to_dict()
            st.json({
                "ID": pedido['ID'],
                "Producto": pedido['Producto'],
                "Cliente": pedido['Cliente'],
                "Fecha entrada": str(pedido['Fecha entrada']),
                "Precio": pedido['Precio']
            })
            
            confirmacion = st.checkbox("Confirmo que deseo eliminar este pedido permanentemente", key="confirm_delete")
            
            if confirmacion:
                if st.button("Eliminar Definitivamente", type="primary", key="confirm_delete_button"):
                    try:
                        df_pedidos = df_pedidos[df_pedidos['ID'] != delete_id]
                        doc_id = pedido['id_documento_firestore']
                        if delete_document_firestore('pedidos', doc_id):
                            st.session_state.data['df_pedidos'] = df_pedidos
                            if save_dataframe_firestore(df_pedidos, 'pedidos'):
                                st.success(f"Pedido {delete_id} eliminado correctamente!")
                                st.rerun()
                            else:
                                st.error("Error al guardar los cambios en Firestore")
                        else:
                            st.error("Error al eliminar el pedido de Firestore")
                    except Exception as e:
                        st.error(f"Error al eliminar el pedido: {str(e)}")