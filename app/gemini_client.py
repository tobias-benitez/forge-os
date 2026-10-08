import json
import logging
from datetime import datetime
from google import genai
from app.config import GEMINI_API_KEY

logger = logging.getLogger("forgeos")
client = genai.Client(api_key=GEMINI_API_KEY)

async def generate_response(user_message: str) -> dict:
    """
    Analiza el mensaje. Si es una petición de recordatorio, devuelve la fecha y texto.
    Si es una conversación normal, responde directamente.
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    system_prompt = f"""
Sos ForgeOS, un asistente inteligente en WhatsApp.
Fecha y hora actual local: {now_str} (Zona horaria de Argentina GMT-3).

Tu rol:
1. Si el usuario te pide un recordatorio o alarma (ej: "recordame estudiar a las 16", "avisame en 10 minutos de sacar la comida"):
   Respondé ÚNICAMENTE un JSON con este formato:
   {{
       "action": "create_reminder",
       "remind_at": "YYYY-MM-DD HH:MM:00",
       "reminder_text": "texto claro de la tarea",
       "reply": "Mensaje confirmando que lo agendaste (ej: 'Anotado, te aviso a las 16:00 hs.')"
   }}

2. Si es una conversación general, duda o consulta normal:
   Respondé ÚNICAMENTE un JSON con:
   {{
       "action": "chat",
       "reply": "Tu respuesta directa, concisa y formateada para WhatsApp"
   }}

IMPORTANTE: Devolvé SOLO el objeto JSON sin bloques de código markdown ni texto adicional.
"""

    models_to_try = ["gemini-3.5-flash-lite", "gemini-2.0-flash-lite", "gemini-2.0-flash"]
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_message,
                config={
                    "system_instruction": system_prompt,
                    "temperature": 0.2,
                }
            )
            raw = response.text.strip()
            # Limpieza básica por si el modelo incluye ```json
            if raw.startswith("```"):
                raw = raw.strip("`").replace("json", "", 1).strip()
            return json.loads(raw)
        except Exception as e:
            logger.warning(f"Error con modelo {model_name}: {e}")
            continue

    return {"action": "chat", "reply": "Disculpá, tuve un error procesando el mensaje."}