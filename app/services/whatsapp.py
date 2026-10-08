import httpx
from app.config import settings

GRAPH_API_URL = f"https://graph.facebook.com/v21.0/{settings.PHONE_NUMBER_ID}/messages"

class WhatsAppService:
    @staticmethod
    def _headers() -> dict:
        return {
            "Authorization": f"Bearer {settings.META_TOKEN}",
            "Content-Type": "application/json"
        }

    @classmethod
    async def send_text_message(cls, to_phone: str, text: str) -> dict:
        """Envía un mensaje de texto simple."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "text",
            "text": {"body": text}
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(GRAPH_API_URL, headers=cls._headers(), json=payload)
            return response.json()

    @classmethod
    async def send_block_prompt(cls, to_phone: str, block_instance_id: str, label: str, category: str) -> dict:
        """
        Envía un mensaje interactivo con los 3 botones debatidos:
        - Arranco ya
        - Posponer 30 min
        - Excepción
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": f"⏰ *Bloque programado:* {label}\n📂 *Categoría:* {category}\n\n¿Cómo querés proceder?"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"start_{block_instance_id}",
                                "title": "Arranco ya"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"postpone_{block_instance_id}",
                                "title": "Posponer 30m"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"exception_{block_instance_id}",
                                "title": "Excepción"
                            }
                        }
                    ]
                }
            }
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(GRAPH_API_URL, headers=cls._headers(), json=payload)
            return response.json()

    @classmethod
    async def download_audio_bytes(cls, media_id: str) -> bytes:
        """Obtiene la URL y descarga el binario del audio de WhatsApp."""
        headers = {"Authorization": f"Bearer {settings.META_TOKEN}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            media_info_res = await client.get(f"https://graph.facebook.com/v21.0/{media_id}", headers=headers)
            media_url = media_info_res.json().get("url")
            if not media_url:
                raise ValueError("No se pudo obtener la URL del audio desde Meta.")
            audio_res = await client.get(media_url, headers=headers)
            return audio_res.content