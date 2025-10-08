# modules/pedido/crear_pedido.py
import streamlit as st  
import pandas as pd
import json
from datetime import datetime
from utils.firestore_utils import get_next_id, save_dataframe_firestore
from utils.data_utils import limpiar_telefono
from .helpers import convert_to_firestore_type, safe_select_index
import time
st.error("🚨 ¡ESTE ES EL ARCHIVO crear_pedido.py QUE SE ESTÁ EJECUTANDO AHORA!")
st.stop()
def show_create(df_pedidos, df_listas):
    # Mostrar un indicador visual de que esta es la versión actualizada (puedes eliminarlo luego)
    # st.toast("✅ Versión actualizada: ahora puedes escribir nuevos clientes, teléfonos o clubes.", icon="📝")

    st.markdown("## 🆕 Crear Nuevo Pedido")
    st.write("---")

    año_actual = datetime.now().year
    st.info(f"📅 **Año del pedido:** {año_actual}")

    # Inicializar número de productos si no existe
    if "num_productos" not in st.session_state:
        st.session_state.num_productos = 1

    st.markdown("### 🧵 Productos del pedido")
    
    # Lista de productos
    productos_lista = [""]
    if 'Producto' in df_listas.columns:
        unique_products = df_listas['Producto'].dropna().unique()
        if len(unique_products) > 0:
            productos_lista.extend(unique_products.tolist())

    # Lista de telas
    telas_lista = [""]
    if 'Tela' in df_listas.columns:
        unique_telas = df_listas['Tela'].dropna().unique()
        if len(unique_telas) > 0:
            telas_lista.extend(unique_telas.tolist())

    total_productos = 0.0
    productos_temp = []

    # Renderizar cada producto
    for i in range(st.session_state.num_productos):
        cols = st.columns([3, 3, 2, 2])
        with cols[0]:
            producto = st.selectbox(
                f"Producto {i+1}",
                productos_lista,
                index=safe_select_index(productos_lista, ""),
                key=f"producto_{i}",
                help="Selecciona un producto de la lista"
            )
        with cols[1]:
            tela = st.selectbox(
                f"Tela {i+1}",
                telas_lista,
                index=safe_select_index(telas_lista, ""),
                key=f"tela_{i}",
                help="Selecciona el tipo de tela"
            )
        with cols[2]:
            precio_unit = st.number_input(
                f"Precio €", 
                min_value=0.0, 
                value=0.0, 
                step=0.5,
                format="%.2f",
                key=f"precio_unit_{i}",
                help="Precio unitario del producto"
            )
        with cols[3]:
            cantidad = st.number_input(
                f"Cantidad", 
                min_value=1, 
                value=1, 
                step=1,
                key=f"cantidad_{i}",
                help="Cantidad de unidades"
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

    # Botones para añadir/quitar productos
    add_col, remove_col = st.columns([1, 1])
    with add_col:
        if st.button("➕ Añadir otro producto", type="secondary", use_container_width=True):
            st.session_state.num_productos += 1
            st.rerun()

    with remove_col:
        if st.session_state.num_productos > 1:
            if st.button("➖ Quitar último producto", type="secondary", use_container_width=True):
                st.session_state.num_productos -= 1
                st.rerun()

    st.write("---")

    # Formulario principal del pedido
    with st.form("nuevo_pedido_form"):
        next_id = get_next_id(df_pedidos, 'ID')
        st.markdown(f"### 🆔 ID del pedido: **{next_id}**")

        col1, col2 = st.columns(2)
        
        with col1:
            # ===== CLIENTE CON SOPORTE PARA NUEVOS VALORES =====
            clientes_existentes = df_pedidos['Cliente'].dropna().unique().tolist() if 'Cliente' in df_pedidos.columns else []
            opciones_cliente = [""] + sorted(clientes_existentes) + ["➕ Escribir nuevo..."]
            cliente_seleccion = st.selectbox(
                "Cliente*",
                opciones_cliente,
                key="cliente_seleccion",
                help="Selecciona un cliente existente o elige 'Escribir nuevo...'"
            )
            
            if cliente_seleccion == "➕ Escribir nuevo...":
                cliente = st.text_input(
                    "Nuevo nombre de cliente*",
                    key="cliente_nuevo_valor",
                    placeholder="Escribe el nombre del nuevo cliente"
                )
            else:
                cliente = cliente_seleccion

            # ===== TELÉFONO CON SOPORTE PARA NUEVOS VALORES =====
            telefonos_existentes = []
            if 'Telefono' in df_pedidos.columns:
                telefonos_limpios = df_pedidos['Telefono'].dropna().astype(str).apply(limpiar_telefono)
                telefonos_validos = telefonos_limpios[telefonos_limpios.str.len() == 9]
                telefonos_existentes = sorted(telefonos_validos.unique().tolist())
            
            opciones_telefono = [""] + telefonos_existentes + ["➕ Escribir nuevo..."]
            telefono_seleccion = st.selectbox(
                "Teléfono* (9 dígitos)",
                opciones_telefono,
                key="telefono_seleccion",
                help="Selecciona un teléfono existente o elige 'Escribir nuevo...'"
            )
            
            if telefono_seleccion == "➕ Escribir nuevo...":
                telefono_input = st.text_input(
                    "Nuevo teléfono*",
                    key="telefono_nuevo_valor",
                    placeholder="Ej: 612345678"
                )
                telefono = telefono_input
            else:
                telefono = telefono_seleccion

            # ===== CLUB CON SOPORTE PARA NUEVOS VALORES =====
            clubes_existentes = df_pedidos['Club'].dropna().unique().tolist() if 'Club' in df_pedidos.columns else []
            opciones_club = [""] + sorted(clubes_existentes) + ["➕ Escribir nuevo..."]
            club_seleccion = st.selectbox(
                "Club*",
                opciones_club,
                key="club_seleccion",
                help="Selecciona un club existente o elige 'Escribir nuevo...'"
            )
            
            if club_seleccion == "➕ Escribir nuevo...":
                club = st.text_input(
                    "Nuevo nombre de club*",
                    key="club_nuevo_valor",
                    placeholder="Escribe el nombre del nuevo club"
                )
            else:
                club = club_seleccion
            
            descripcion = st.text_area(
                "Descripción",
                key="descripcion",
                placeholder="Detalles del pedido, observaciones, etc."
            )

        with col2:
            fecha_entrada = st.date_input(
                "📅 Fecha de entrada", 
                value=datetime.now().date()
            )
            
            tiene_fecha_salida = st.checkbox("📆 Establecer fecha de salida")
            if tiene_fecha_salida:
                fecha_salida = st.date_input("Fecha de salida", value=datetime.now().date())
            else:
                fecha_salida = None
            
            precio = st.number_input(
                "💰 Precio total (€)", 
                min_value=0.0, 
                value=0.0, 
                step=1.0,
                format="%.2f"
            )
            
            precio_factura = st.number_input(
                "🧾 Precio factura (€)", 
                min_value=0.0, 
                value=0.0, 
                step=1.0,
                format="%.2f"
            )
            
            tipos_pago = [""]
            if 'Tipo de pago' in df_listas.columns:
                unique_tipos = df_listas['Tipo de pago'].dropna().unique()
                if len(unique_tipos) > 0:
                    tipos_pago.extend(unique_tipos.tolist())
            tipo_pago = st.selectbox(
                "💳 Tipo de pago", 
                tipos_pago,
                key="tipo_pago"
            )
            
            adelanto = st.number_input(
                "💵 Adelanto (€)", 
                min_value=0.0, 
                value=0.0, 
                step=1.0,
                format="%.2f"
            )
            
            observaciones = st.text_area(
                "📝 Observaciones adicionales",
                key="observaciones",
                placeholder="Notas internas, acuerdos, etc."
            )

        # Estados del pedido
        st.write("### 🏷️ Estado del pedido")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            empezado = st.checkbox("Empezado", value=False)
        with col_b:
            cobrado = st.checkbox("Cobrado", value=False)
        with col_c:
            pendiente = st.checkbox("Pendiente", value=False)

        submitted = st.form_submit_button("✅ Guardar Nuevo Pedido", type="primary", use_container_width=True)

        if submitted:
            # Validación de campos obligatorios
            if not cliente or not telefono or not club:
                st.error("❌ Por favor complete los campos obligatorios (*)")
                return

            telefono_limpio = limpiar_telefono(telefono)
            if not telefono_limpio or len(telefono_limpio) != 9:
                st.error("❌ El teléfono debe contener exactamente 9 dígitos numéricos")
                return

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

                    # Actualizar sesión y recargar
                    st.session_state.data['df_pedidos'] = df_pedidos
                    st.session_state.data_loaded = False
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Error al crear el pedido. Por favor, inténtelo de nuevo.")