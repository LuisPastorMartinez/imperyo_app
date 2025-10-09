# modules/pedido/crear_pedido.py
import streamlit as st  
import pandas as pd
import json
from datetime import datetime
from utils.firestore_utils import get_next_id, save_dataframe_firestore
from utils.data_utils import limpiar_telefono
from .helpers import convert_to_firestore_type, safe_select_index
import time

def show_create(df_pedidos, df_listas):
    st.markdown("## 🆕 Crear Nuevo Pedido")
    st.write("---")

    año_actual = datetime.now().year
    st.info(f"📅 **Año del pedido:** {año_actual}")

    if "num_productos" not in st.session_state:
        st.session_state.num_productos = 1

    # === Productos del pedido ===
    st.markdown("### 🧵 Productos del pedido")
    
    productos_lista = [""]
    if 'Producto' in df_listas.columns:
        unique_products = df_listas['Producto'].dropna().unique()
        if len(unique_products) > 0:
            productos_lista.extend(unique_products.tolist())

    telas_lista = [""]
    if 'Tela' in df_listas.columns:
        unique_telas = df_listas['Tela'].dropna().unique()
        if len(unique_telas) > 0:
            telas_lista.extend(unique_telas.tolist())

    total_productos = 0.0
    productos_temp = []

    for i in range(st.session_state.num_productos):
        cols = st.columns([3, 3, 2, 2])
        with cols[0]:
            producto = st.selectbox(
                f"Producto {i+1}",
                productos_lista,
                index=safe_select_index(productos_lista, ""),
                key=f"producto_{i}"
            )
        with cols[1]:
            tela = st.selectbox(
                f"Tela {i+1}",
                telas_lista,
                index=safe_select_index(telas_lista, ""),
                key=f"tela_{i}"
            )
        with cols[2]:
            precio_unit = st.number_input(
                f"Precio €", 
                min_value=0.0, 
                value=0.0, 
                step=0.5,
                format="%.2f",
                key=f"precio_unit_{i}"
            )
        with cols[3]:
            cantidad = st.number_input(
                f"Cantidad", 
                min_value=1, 
                value=1, 
                step=1,
                key=f"cantidad_{i}"
            )

        total_productos += precio_unit * cantidad
        productos_temp.append({
            "Producto": producto,
            "Tela": tela,
            "PrecioUnitario": precio_unit,
            "Cantidad": cantidad
        })

    st.markdown(f"<div style='background-color: #e3f2fd; padding: 10px; border-radius: 8px;'><b>💰 Subtotal productos:</b> <span style='font-size: 1.2em; color: #1976d2;'>{total_productos:.2f} €</span></div>", unsafe_allow_html=True)

    st.write("")
    add_col, remove_col = st.columns(2)
    with add_col:
        if st.button("➕ Añadir otro producto", use_container_width=True):
            st.session_state.num_productos += 1
            st.rerun()
    with remove_col:
        if st.session_state.num_productos > 1:
            if st.button("➖ Quitar último producto", use_container_width=True):
                st.session_state.num_productos -= 1
                st.rerun()

    st.write("---")

    # === Datos del cliente (con persistencia en session_state) ===
    next_id = get_next_id(df_pedidos, 'ID')
    st.markdown(f"### 🆔 ID del pedido: **{next_id}**")

    col1, col2 = st.columns(2)
    
    with col1:
        # Cliente
        clientes_existentes = df_pedidos['Cliente'].dropna().unique().tolist() if 'Cliente' in df_pedidos.columns else []
        opciones_cliente = [""] + sorted(clientes_existentes) + ["➕ Escribir nuevo..."]
        cliente_seleccion = st.selectbox("Cliente*", opciones_cliente, key="cliente_seleccion")
        if cliente_seleccion == "➕ Escribir nuevo...":
            cliente = st.text_input(
                "Nuevo cliente*",
                key="cliente_nuevo_input",
                value=st.session_state.get("cliente_nuevo", ""),
                placeholder="Ej: Juan Pérez"
            )
            st.session_state["cliente_nuevo"] = cliente
        else:
            cliente = cliente_seleccion
            if "cliente_nuevo" in st.session_state:
                del st.session_state["cliente_nuevo"]

        # Teléfono
        telefonos_existentes = []
        if 'Telefono' in df_pedidos.columns:
            telefonos_limpios = df_pedidos['Telefono'].dropna().astype(str).apply(limpiar_telefono)
            telefonos_validos = telefonos_limpios[telefonos_limpios.str.len() == 9]
            telefonos_existentes = sorted(telefonos_validos.unique().tolist())
        opciones_telefono = [""] + telefonos_existentes + ["➕ Escribir nuevo..."]
        telefono_seleccion = st.selectbox("Teléfono* (9 dígitos)", opciones_telefono, key="telefono_seleccion")
        if telefono_seleccion == "➕ Escribir nuevo...":
            telefono = st.text_input(
                "Nuevo teléfono*",
                key="telefono_nuevo_input",
                placeholder="Ej: 612345678",
                value=st.session_state.get("telefono_nuevo", "")
            )
            st.session_state["telefono_nuevo"] = telefono
        else:
            telefono = telefono_seleccion
            if "telefono_nuevo" in st.session_state:
                del st.session_state["telefono_nuevo"]

        # Club
        clubes_existentes = df_pedidos['Club'].dropna().unique().tolist() if 'Club' in df_pedidos.columns else []
        opciones_club = [""] + sorted(clubes_existentes) + ["➕ Escribir nuevo..."]
        club_seleccion = st.selectbox("Club*", opciones_club, key="club_seleccion")
        if club_seleccion == "➕ Escribir nuevo...":
            club = st.text_input(
                "Nuevo club*",
                key="club_nuevo_input",
                value=st.session_state.get("club_nuevo", ""),
                placeholder="Ej: Imperyo FC"
            )
            st.session_state["club_nuevo"] = club
        else:
            club = club_seleccion
            if "club_nuevo" in st.session_state:
                del st.session_state["club_nuevo"]

        descripcion = st.text_area("Descripción", key="descripcion")

    with col2:
        fecha_entrada = st.date_input("📅 Fecha de entrada", value=datetime.now().date())
        tiene_fecha_salida = st.checkbox("📆 Establecer fecha de salida", key="tiene_fecha_salida")
        fecha_salida = st.date_input("Fecha de salida", value=datetime.now().date()) if tiene_fecha_salida else None
        precio = st.number_input("💰 Precio total (€)", min_value=0.0, value=0.0, step=1.0, format="%.2f", key="precio")
        precio_factura = st.number_input("🧾 Precio factura (€)", min_value=0.0, value=0.0, step=1.0, format="%.2f", key="precio_factura")
        
        tipos_pago = [""]
        if 'Tipo de pago' in df_listas.columns:
            tipos_pago.extend(df_listas['Tipo de pago'].dropna().unique().tolist())
        tipo_pago = st.selectbox("💳 Tipo de pago", tipos_pago, key="tipo_pago")
        
        adelanto = st.number_input("💵 Adelanto (€)", min_value=0.0, value=0.0, step=1.0, format="%.2f", key="adelanto")
        observaciones = st.text_area("📝 Observaciones adicionales", key="observaciones")

    # Estados del pedido
    st.write("### 🏷️ Estado del pedido")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        empezado = st.checkbox("Empezado", key="empezado")
    with col_b:
        cobrado = st.checkbox("Cobrado", key="cobrado")
    with col_c:
        pendiente = st.checkbox("Pendiente", key="pendiente")

    # Botón de guardar
    if st.button("✅ Guardar Nuevo Pedido", type="primary", use_container_width=True):
        # Validación de campos obligatorios
        if not cliente or not telefono or not club:
            st.error("❌ Por favor complete los campos obligatorios (*)")
        else:
            telefono_limpio = limpiar_telefono(telefono)
            if not telefono_limpio or len(telefono_limpio) != 9:
                st.error("❌ El teléfono debe contener exactamente 9 dígitos numéricos")
            else:
                productos_json = json.dumps(productos_temp)

                new_pedido = {
                    'ID': next_id,
                    'Productos': productos_json,
                    'Cliente': convert_to_firestore_type(cliente),
                    'Telefono': convert_to_firestore_type(telefono_limpio),
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
                    'Trabajo Terminado': False,
                    'Cobrado': convert_to_firestore_type(cobrado),
                    'Retirado': False,
                    'Pendiente': convert_to_firestore_type(pendiente),
                    'Año': año_actual,
                    'id_documento_firestore': None
                }

                with st.spinner("💾 Guardando pedido..."):
                    new_pedido_df = pd.DataFrame([new_pedido])
                    df_pedidos = pd.concat([df_pedidos, new_pedido_df], ignore_index=True)
                    df_pedidos = df_pedidos.where(pd.notna(df_pedidos), None)

                    for c in df_pedidos.columns:
                        df_pedidos[c] = df_pedidos[c].apply(lambda x: None if x is pd.NaT else x)

                    if save_dataframe_firestore(df_pedidos, 'pedidos'):
                        st.success(f"🎉 ¡Pedido **{next_id}** del año **{año_actual}** creado correctamente!")
                        st.balloons()
                        
                        # Opcional: notificación por Telegram
                        try:
                            from utils.notifications import enviar_telegram
                            precio_mostrar = precio if precio > 0 else precio_factura if precio_factura > 0 else 0.0
                            mensaje = f"🆕 <b>Nuevo pedido</b>\nID: {next_id}\nCliente: {cliente}\nEquipo: {club}\nPrecio: {precio_mostrar:.2f} €"
                            enviar_telegram(
                                mensaje=mensaje,
                                bot_token=st.secrets["telegram"]["bot_token"],
                                chat_id=st.secrets["telegram"]["chat_id"]
                            )
                        except Exception as e:
                            st.warning(f"⚠️ No se pudo enviar notificación: {e}")

                        # Limpiar campos de nuevo cliente/equipo/telefono del estado
                        for key in ["cliente_nuevo", "telefono_nuevo", "club_nuevo"]:
                            if key in st.session_state:
                                del st.session_state[key]

                        # Actualizar datos en sesión y recargar
                        st.session_state.data['df_pedidos'] = df_pedidos
                        st.session_state.data_loaded = False
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("❌ Error al crear el pedido. Por favor, inténtelo de nuevo.")