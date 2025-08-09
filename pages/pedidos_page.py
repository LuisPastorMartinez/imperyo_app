# pages/pedidos_page.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.firestore_utils import (
    save_dataframe_firestore,
    delete_document_firestore,
    get_next_id
)

def highlight_pedidos_rows(row):
    """Función para resaltar filas según estado del pedido"""
    styles = [''] * len(row)
    if row['Trabajo Terminado'] and row['Cobrado'] and row['Retirado'] and not row['Pendiente']:
        styles = ['background-color: #00B050'] * len(row)  # Verde - Completo
    elif row['Inicio Trabajo'] and not row['Pendiente']:
        styles = ['background-color: #0070C0'] * len(row)  # Azul - En progreso
    elif row['Trabajo Terminado'] and not row['Pendiente']:
        styles = ['background-color: #FFC000'] * len(row)  # Amarillo - Terminado
    elif row['Pendiente']:
        styles = ['background-color: #FF00FF'] * len(row)  # Rosa - Pendiente
    return styles

def show_pedidos_page(df_pedidos, df_listas):
    """Página principal de gestión de pedidos"""
    st.header("Gestión de Pedidos")
    tab1, tab2, tab3, tab4 = st.tabs(["Guardar Nuevo", "Buscar", "Modificar", "Eliminar"])

    with tab1:  # Guardar nuevo pedido
        with st.form("nuevo_pedido_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nuevo_id = get_next_id(df_pedidos, 'ID')
                producto = st.selectbox("Producto", [""] + df_listas['Producto'].dropna().unique().tolist())
                cliente = st.text_input("Cliente*")
                telefono = st.text_input("Teléfono (9 dígitos)*", max_chars=9)
                club = st.text_input("Club")
                talla = st.selectbox("Talla", [""] + df_listas['Talla'].dropna().unique().tolist())
                tela = st.selectbox("Tela", [""] + df_listas['Tela'].dropna().unique().tolist())
                descripcion = st.text_area("Descripción")
            
            with col2:
                fecha_entrada = st.date_input("Fecha entrada*", datetime.now())
                fecha_salida = st.date_input("Fecha salida")
                precio = st.number_input("Precio*", min_value=0.0)
                precio_factura = st.number_input("Precio factura", min_value=0.0)
                tipo_pago = st.selectbox("Tipo de pago", [""] + df_listas['Tipo de pago'].dropna().unique().tolist())
                adelanto = st.number_input("Adelanto", min_value=0.0)
                observaciones = st.text_area("Observaciones")

            # Estado del pedido
            st.write("**Estado del pedido:**")
            estado_cols = st.columns(5)
            with estado_cols[0]:
                empezado = st.checkbox("Empezado")
            with estado_cols[1]:
                terminado = st.checkbox("Terminado")
            with estado_cols[2]:
                cobrado = st.checkbox("Cobrado")
            with estado_cols[3]:
                retirado = st.checkbox("Retirado")
            with estado_cols[4]:
                pendiente = st.checkbox("Pendiente")

            if st.form_submit_button("Guardar Pedido"):
                if not cliente or not telefono or not fecha_entrada:
                    st.error("Campos obligatorios (*) incompletos")
                else:
                    nuevo_pedido = {
                        'ID': nuevo_id,
                        'Producto': producto or None,
                        'Cliente': cliente,
                        'Telefono': telefono,
                        'Club': club,
                        'Talla': talla or None,
                        'Tela': tela or None,
                        'Breve Descripción': descripcion,
                        'Fecha entrada': fecha_entrada,
                        'Fecha Salida': fecha_salida if fecha_salida else None,
                        'Precio': float(precio),
                        'Precio Factura': float(precio_factura) if precio_factura else None,
                        'Tipo de pago': tipo_pago or None,
                        'Adelanto': float(adelanto) if adelanto else None,
                        'Observaciones': observaciones,
                        'Inicio Trabajo': empezado,
                        'Trabajo Terminado': terminado,
                        'Cobrado': cobrado,
                        'Retirado': retirado,
                        'Pendiente': pendiente
                    }

                    # Guardar en Firestore
                    df_nuevo = pd.DataFrame([nuevo_pedido])
                    df_pedidos = pd.concat([df_pedidos, df_nuevo], ignore_index=True)
                    
                    if save_dataframe_firestore(df_pedidos, 'pedidos'):
                        st.success(f"Pedido {nuevo_id} guardado!")
                        st.rerun()
                    else:
                        st.error("Error al guardar")

    with tab2:  # Buscar pedido
        buscar_id = st.number_input("ID del pedido:", min_value=1)
        if st.button("Buscar"):
            pedido = df_pedidos[df_pedidos['ID'] == buscar_id]
            if not pedido.empty:
                st.dataframe(pedido.style.apply(highlight_pedidos_rows, axis=1))
            else:
                st.warning("Pedido no encontrado")

    with tab3:  # Modificar pedido
        mod_id = st.number_input("ID a modificar:", min_value=1)
        pedido = df_pedidos[df_pedidos['ID'] == mod_id]
        
        if not pedido.empty:
            with st.form("modificar_form"):
                # Similar al formulario de nuevo pero con valores precargados
                # ... (código similar al formulario nuevo pero con st.form_submit_button("Actualizar"))
                if st.form_submit_button("Actualizar"):
                    # Lógica similar a guardar pero con actualización
                    pass
        else:
            st.warning("Ingrese un ID válido")

    with tab4:  # Eliminar pedido
        del_id = st.number_input("ID a eliminar:", min_value=1)
        pedido = df_pedidos[df_pedidos['ID'] == del_id]
        
        if not pedido.empty:
            st.warning(f"¿Eliminar pedido {del_id}?")
            st.dataframe(pedido)
            
            if st.button("Confirmar eliminación"):
                doc_id = pedido.iloc[0]['id_documento_firestore']
                if delete_document_firestore('pedidos', doc_id):
                    st.success("Pedido eliminado")
                    st.rerun()
                else:
                    st.error("Error al eliminar")
        else:
            st.warning("Ingrese un ID válido")