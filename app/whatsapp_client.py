import httpx
import logging
from app.config import WHATSAPP_ACCESS_TOKEN, PHONE_NUMBER_ID

logger = logging.getLogger("forgeos")

def format_destination_number(number: str) -> str:
    """
    Normaliza el número para la API de Meta.
    En Argentina, los números entrantes suelen venir como '54911XXXXXXXX'.
    En el sandbox de Meta, la lista de permitidos a menudo registra '5411XXXXXXXX' (sin el 9).
    """
    clean_num = "".join(filter(str.isdigit, number))
    
    # Si es número de Argentina con el prefijo 9 móvil (54 9 ...), probamos primero el formato estándar sin el 9
    if clean_num.startswith("549") and len(clean_num) == 13:
        return f"54{clean_num[3:]}"
    
    return clean_num

async def send_whatsapp_message(to_number: str, text: str):
    """Envía un mensaje de texto de WhatsApp a través de la Cloud API de Meta."""
    dest_number = format_destination_number(to_number)
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": dest_number,
        "type": "text",
        "text": {"body": text}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        
        # Si falla con el formato sin el 9, intentamos con el número original con el 9
        if response.status_code != 200 and dest_number != to_number:
            logger.warning(f"Reintentando envío con formato original: {to_number}")
            payload["to"] = to_number
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            logger.info(f"Mensaje enviado con éxito a {payload['to']}")
        else:
            logger.error(f"Error enviando mensaje ({response.status_code}): {response.text}")