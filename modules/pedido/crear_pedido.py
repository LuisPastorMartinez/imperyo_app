import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime, date

from utils.firestore_utils import save_dataframe_firestore
from utils.data_utils import limpiar_telefono
from .helpers import convert_to_firestore_type


def get_next_id_por_año(df_pedidos, año):
    """
    Devuelve el siguiente ID disponible SOLO para el año indicado.
    """
    if df_pedidos is None or df_pedidos.empty:
        return 1

    df_year = df_pedidos[df_pedidos["Año"] == año]

    if df_year.empty:
        return 1

    ids = pd.to_numeric(df_year["ID"], errors="coerce").dropna()

    if ids.empty:
        return 1

    return int(ids.max()) + 1


def show_create(df_pedidos, df_listas):
<<<<<<< HEAD
    st.subheader("➕ Crear Pedido")

    # ---------- ASEGURAR DATAFRAME ----------
    if df_pedidos is None:
        st.error("❌ No hay datos de pedidos.")
        return

    # ---------- ASEGURAR COLUMNA AÑO ----------
    if "Año" not in df_pedidos.columns:
        df_pedidos["Año"] = datetime.now().year

    df_pedidos["Año"] = pd.to_numeric(
        df_pedidos["Año"], errors="coerce"
    ).fillna(datetime.now().year).astype("int64")

    # ---------- SELECTOR DE AÑO ----------
    año_actual = datetime.now().year

    años_disponibles = sorted(
        df_pedidos["Año"].dropna().unique(),
        reverse=True
    )

    if año_actual not in años_disponibles:
        años_disponibles.insert(0, año_actual)

    año_seleccionado = st.selectbox(
        "📅 Año del pedido",
        años_disponibles,
        key="create_año_selector"
    )

    # ---------- CALCULAR ID ----------
    next_id = get_next_id_por_año(df_pedidos, año_seleccionado)

    st.markdown(
        f"### 🆔 ID del pedido: **{next_id}**  \n"
        f"📆 Año: **{año_seleccionado}**"
    )

=======
    st.markdown("## 🆕 Crear Nuevo Pedido")
>>>>>>> b77774bbac2e133467caea9785292209ee2cc27a
    st.write("---")

    # ---------- PRODUCTOS ----------
    st.markdown("### 🧵 Productos")

<<<<<<< HEAD
    if "productos_crear" not in st.session_state:
        st.session_state.productos_crear = [
            {"Producto": "", "Tela": "", "PrecioUnitario": 0.0, "Cantidad": 1}
        ]

    productos_lista = [""] + (
        df_listas["Producto"].dropna().unique().tolist()
        if "Producto" in df_listas.columns else []
    )
    telas_lista = [""] + (
        df_listas["Tela"].dropna().unique().tolist()
        if "Tela" in df_listas.columns else []
    )
=======
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
>>>>>>> b77774bbac2e133467caea9785292209ee2cc27a

    total_productos = 0.0

<<<<<<< HEAD
    for i, p in enumerate(st.session_state.productos_crear):
=======
    for i in range(st.session_state.num_productos):
>>>>>>> b77774bbac2e133467caea9785292209ee2cc27a
        cols = st.columns([3, 3, 2, 2])

        with cols[0]:
            p["Producto"] = st.selectbox(
                f"Producto {i+1}",
                productos_lista,
<<<<<<< HEAD
                index=productos_lista.index(p.get("Producto", ""))
                if p.get("Producto", "") in productos_lista else 0,
                key=f"create_producto_{i}"
=======
                index=safe_select_index(productos_lista, ""),
                key=f"producto_{i}"
>>>>>>> b77774bbac2e133467caea9785292209ee2cc27a
            )

        with cols[1]:
            p["Tela"] = st.selectbox(
                f"Tela {i+1}",
                telas_lista,
<<<<<<< HEAD
                index=telas_lista.index(p.get("Tela", ""))
                if p.get("Tela", "") in telas_lista else 0,
                key=f"create_tela_{i}"
=======
                index=safe_select_index(telas_lista, ""),
                key=f"tela_{i}"
>>>>>>> b77774bbac2e133467caea9785292209ee2cc27a
            )

        with cols[2]:
<<<<<<< HEAD
            p["PrecioUnitario"] = st.number_input(
                "Precio €",
                min_value=0.0,
                value=float(p.get("PrecioUnitario", 0.0)),
                key=f"create_precio_{i}"
=======
            precio_unit = st.number_input(
                f"Precio €", 
                min_value=0.0, 
                value=0.0, 
                step=0.5,
                format="%.2f",
                key=f"precio_unit_{i}"
>>>>>>> b77774bbac2e133467caea9785292209ee2cc27a
            )

        with cols[3]:
<<<<<<< HEAD
            p["Cantidad"] = st.number_input(
                "Cantidad",
                min_value=1,
                value=int(p.get("Cantidad", 1)),
                key=f"create_cantidad_{i}"
=======
            cantidad = st.number_input(
                f"Cantidad", 
                min_value=1, 
                value=1, 
                step=1,
                key=f"cantidad_{i}"
>>>>>>> b77774bbac2e133467caea9785292209ee2cc27a
            )

        total_productos += p["PrecioUnitario"] * p["Cantidad"]

    st.markdown(f"**💰 Subtotal productos:** {total_productos:.2f} €")

<<<<<<< HEAD
    col_add, col_remove = st.columns(2)

    with col_add:
        if st.button("➕ Añadir producto"):
            st.session_state.productos_crear.append(
                {"Producto": "", "Tela": "", "PrecioUnitario": 0.0, "Cantidad": 1}
            )
            st.rerun()

    with col_remove:
        if len(st.session_state.productos_crear) > 1:
            if st.button("➖ Quitar último producto"):
                st.session_state.productos_crear.pop()
=======
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
>>>>>>> b77774bbac2e133467caea9785292209ee2cc27a
                st.rerun()

    st.write("---")

<<<<<<< HEAD
    # ---------- FORMULARIO ----------
    with st.form("crear_pedido_form"):
        col1, col2 = st.columns(2)

        with col1:
            cliente = st.text_input("Cliente*", "")
            telefono = st.text_input("Teléfono*", "")
            club = st.text_input("Club*", "")
            descripcion = st.text_area("Descripción")

        with col2:
            fecha_entrada = st.date_input("Fecha entrada", datetime.now().date())
            precio = st.number_input("Precio total (€)", min_value=0.0, value=0.0)
            precio_factura = st.number_input("Precio factura (€)", min_value=0.0, value=0.0)

        crear = st.form_submit_button("✅ Crear Pedido", type="primary")

    # ---------- CREAR PEDIDO ----------
    if crear:
        if not cliente or not telefono or not club:
            st.error("❌ Cliente, Teléfono y Club son obligatorios.")
            return

        telefono_limpio = limpiar_telefono(telefono)
        if not telefono_limpio:
            st.error("❌ Teléfono inválido.")
            return

        nuevo_pedido = {
            "ID": next_id,
            "Año": año_seleccionado,
            "Productos": json.dumps(st.session_state.productos_crear),
            "Cliente": convert_to_firestore_type(cliente),
            "Telefono": convert_to_firestore_type(telefono_limpio),
            "Club": convert_to_firestore_type(club),
            "Breve Descripción": convert_to_firestore_type(descripcion),
            "Fecha entrada": convert_to_firestore_type(fecha_entrada),
            "Fecha Salida": None,
            "Precio": convert_to_firestore_type(precio),
            "Precio Factura": convert_to_firestore_type(precio_factura),
            "Inicio Trabajo": False,
            "Trabajo Terminado": False,
            "Cobrado": False,
            "Retirado": False,
            "Pendiente": False
        }

        df_pedidos = pd.concat(
            [df_pedidos, pd.DataFrame([nuevo_pedido])],
            ignore_index=True
        )

        if not save_dataframe_firestore(df_pedidos, "pedidos"):
            st.error("❌ Error al guardar el pedido.")
            return

        st.success(f"✅ Pedido {next_id} del año {año_seleccionado} creado correctamente")
        st.balloons()
        time.sleep(1)

        # Limpiar estado
        if "productos_crear" in st.session_state:
            del st.session_state.productos_crear

        st.session_state.data["df_pedidos"] = df_pedidos
        st.rerun()
=======
    # === Datos del cliente: con +crear al principio y campo inmediato ===
    next_id = get_next_id(df_pedidos, 'ID')
    st.markdown(f"### 🆔 ID del pedido: **{next_id}**")

    col1, col2 = st.columns(2)
    
    with col1:
        # === CLIENTE ===
        clientes_existentes = df_pedidos['Cliente'].dropna().unique().tolist() if 'Cliente' in df_pedidos.columns else []
        opciones_cliente = ["", "➕ Escribir nuevo..."] + sorted(clientes_existentes)
        cliente_seleccion = st.selectbox("Cliente*", opciones_cliente, key="cliente_seleccion")
        if cliente_seleccion == "➕ Escribir nuevo...":
            st.caption("✏️ Escribe el nombre del nuevo cliente:")
            cliente = st.text_input("Nuevo cliente*", key="cliente_nuevo", placeholder="Ej: Juan Pérez", label_visibility="collapsed")
        else:
            cliente = cliente_seleccion

        # === TELÉFONO ===
        telefonos_existentes = []
        if 'Telefono' in df_pedidos.columns:
            telefonos_limpios = df_pedidos['Telefono'].dropna().astype(str).apply(limpiar_telefono)
            telefonos_validos = telefonos_limpios[telefonos_limpios.str.len() == 9]
            telefonos_existentes = sorted(telefonos_validos.unique().tolist())
        opciones_telefono = ["", "➕ Escribir nuevo..."] + telefonos_existentes
        telefono_seleccion = st.selectbox("Teléfono* (9 dígitos)", opciones_telefono, key="telefono_seleccion")
        if telefono_seleccion == "➕ Escribir nuevo...":
            st.caption("✏️ Escribe el nuevo número (9 dígitos):")
            telefono = st.text_input("Nuevo teléfono*", key="telefono_nuevo", placeholder="Ej: 612345678", label_visibility="collapsed")
        else:
            telefono = telefono_seleccion

        # === CLUB ===
        clubes_existentes = df_pedidos['Club'].dropna().unique().tolist() if 'Club' in df_pedidos.columns else []
        opciones_club = ["", "➕ Escribir nuevo..."] + sorted(clubes_existentes)
        club_seleccion = st.selectbox("Club*", opciones_club, key="club_seleccion")
        if club_seleccion == "➕ Escribir nuevo...":
            st.caption("✏️ Escribe el nombre del nuevo club:")
            club = st.text_input("Nuevo club*", key="club_nuevo", placeholder="Ej: Imperyo FC", label_visibility="collapsed")
        else:
            club = club_seleccion

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

                        # Actualizar datos en sesión
                        st.session_state.data['df_pedidos'] = df_pedidos
                        st.session_state.data_loaded = False
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("❌ Error al crear el pedido. Por favor, inténtelo de nuevo.")
>>>>>>> b77774bbac2e133467caea9785292209ee2cc27a
