# utils/notifications.py
import requests
import logging

logger = logging.getLogger(__name__)

def enviar_telegram(mensaje, bot_token, chat_id):
    """
    Envía un mensaje a un grupo de Telegram.
    
    Args:
        mensaje (str): Texto del mensaje.
        bot_token (str): Token del bot de Telegram.
        chat_id (str): ID del grupo o chat.
    """
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": mensaje,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        logger.info(f"Telegram enviado: {mensaje}")
        return True
    except Exception as e:
        logger.error(f"Error al enviar Telegram: {e}")
        return False