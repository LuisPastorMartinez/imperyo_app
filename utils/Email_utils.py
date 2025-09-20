import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

def send_completion_email(to_email, client_name, product_name, delivery_date):
    """
    Envía un email al cliente cuando su pedido cambia a 'Terminado'.
    """
    try:
        # --- CONFIGURACIÓN SMTP (MODIFICA ESTO) ---
        SMTP_SERVER = "smtp.gmail.com"  # Cambia si usas Outlook, Yahoo, etc.
        SMTP_PORT = 587
        SENDER_EMAIL = st.secrets["email"]["sender"]  # Ej: "tuemail@gmail.com"
        SENDER_PASSWORD = st.secrets["email"]["password"]  # Contraseña de app (no la de la cuenta)

        # --- CREAR MENSAJE ---
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = "🎉 ¡Tu pedido está listo! - Imperyo Sport"

        body = f"""
Hola {client_name},

¡Buenas noticias! Tu pedido de "{product_name}" ya está terminado y listo para retirar.

📅 Fecha estimada de entrega: {delivery_date}

Gracias por confiar en nosotros. ¡Te esperamos!

— Equipo Imperyo Sport
        """.strip()

        msg.attach(MIMEText(body, 'plain'))

        # --- ENVIAR EMAIL ---
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, to_email, text)
        server.quit()

        return True

    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False