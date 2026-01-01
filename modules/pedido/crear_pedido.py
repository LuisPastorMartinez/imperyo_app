import streamlit as st
import pandas as pd
import json
from datetime import datetime
from utils.firestore_utils import save_dataframe_firestore, get_next_id_por_año
from utils.data_utils import limpiar_telefono
from .helpers import convert_to_firestore_type, safe_select_index
import time

def show_create(df_pedidos, df_listas):
    st.markdown("## 🆕 Crear Nuevo Pedido")
    st.write("---")

    año_actual = datetime.now().year
    st.info(f"📅 Año del pedido: {año_actual}")

    if "num_productos" not in st.session_state:
        st.session_state.num_productos = 1

    productos_lista = [""] + df_listas.get('Producto', pd.Series()).dropna().unique().tolist()
    telas_lista = [""] + df_listas.get('Tela', pd.Series()).dropna().unique().tolist()

    total_productos = 0.0
    productos_temp = []

    for i in range(st.session_state.num_productos):
        c1, c2, c3, c4 = st.columns([3,3,2,2])
        with c1:
            producto = st.selectbox(f"Producto {i+1}", productos_lista, key=f"producto_{i}")
        with c2:
            tela = st.selectbox(f"Tela {i+1}", telas_lista, key=f"tela_{i}")
        with c3:
            precio_unit = st.number_input("Precio €", min_value=0.0, step=0.5, key=f"precio_{i}")
        with c4:
            cantidad = st.number_input("Cantidad", min_value=1, step=1, key=f"cantidad_{i}")

        total_productos += precio_unit * cantidad
        productos_temp.append({
            "Producto": producto,
            "Tela": tela,
            "PrecioUnitario": precio_unit,
            "Cantidad": cantidad
        })

    st.markdown(f"**Subtotal productos:** {total_productos:.2f} €")

    col_add, col_remove = st.columns(2)
    with col_add:
        if st.button("➕ Añadir producto"):
            st.session_state.num_productos += 1
            st.rerun()
    with col_remove:
        if st.session_state.num_productos > 1 and st.button("➖ Quitar producto"):
            st.session_state.num_productos -= 1
            st.rerun()

    # ✅ ID REINICIADO POR AÑO
    next_id = get_next_id_por_año(df_pedidos, año_actual)
    st.markdown(f"### 🆔 ID del pedido: **{next_id}**")

    col1, col2 = st.columns(2)
    with col1:
        cliente = st.text_input("Cliente*")
        telefono = st.text_input("Teléfono*")
        club = st.text_input("Club*")
        descripcion = st.text_area("Descripción")

    with col2:
        fecha_entrada = st.date_input("Fecha entrada", value=datetime.now().date())
        precio = st.number_input("Precio total (€)", min_value=0.0)
        precio_factura = st.number_input("Precio factura (€)", min_value=0.0)
        tipo_pago = st.selectbox("Tipo de pago", [""] + df_listas.get('Tipo de pago', pd.Series()).dropna().tolist())
        adelanto = st.number_input("Adelanto (€)", min_value=0.0)
        observaciones = st.text_area("Observaciones")

    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        empezado = st.checkbox("Empezado")
    with col_e2:
        cobrado = st.checkbox("Cobrado")
    with col_e3:
        pendiente = st.checkbox("Pendiente")

    if st.button("✅ Guardar Pedido", type="primary", use_container_width=True):
        telefono_limpio = limpiar_telefono(telefono)
        if not cliente or not telefono_limpio or not club:
            st.error("Campos obligatorios incorrectos")
            return

        pedido = {
            'ID': next_id,
            'Año': año_actual,
            'Productos': json.dumps(productos_temp),
            'Cliente': cliente,
            'Telefono': telefono_limpio,
            'Club': club,
            'Breve Descripción': descripcion,
            'Fecha entrada': fecha_entrada,
            'Precio': precio,
            'Precio Factura': precio_factura,
            'Tipo de pago': tipo_pago,
            'Adelanto': adelanto,
            'Observaciones': observaciones,
            'Inicio Trabajo': empezado,
            'Trabajo Terminado': False,
            'Cobrado': cobrado,
            'Retirado': False,
            'Pendiente': pendiente,
            'id_documento_firestore': None
        }

        df_pedidos = pd.concat([df_pedidos, pd.DataFrame([pedido])], ignore_index=True)

        if save_dataframe_firestore(df_pedidos, 'pedidos'):
            st.success(f"Pedido {next_id} ({año_actual}) creado correctamente")
            st.balloons()
            time.sleep(1.5)
            st.session_state.data['df_pedidos'] = df_pedidos
            st.rerun()
        else:
            st.error("Error al guardar el pedido")
