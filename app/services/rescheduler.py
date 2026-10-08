import json
from datetime import datetime
from google import genai
from google.genai import types
from app.config import settings

ai_client = genai.Client(api_key=settings.GEMINI_API_KEY or None)
MODEL_NAME = "gemini-3.5-flash-lite"

SYSTEM_INSTRUCTION = """
Eres el núcleo de inteligencia de ForgeOS, asistente personal, mentor de hábitos y agenda inteligente de Tobías.
Perfil:
- Estudiante de Ingeniería / Sistemas y desarrollador de software.
- Creyente: prioriza su relación con Dios, oración matutina, lectura de la Palabra y Misa dominical. Hace voluntariado en un hogar de niños los miércoles.
- Salud: entrena fuerza y cardio (3 días por semana: martes, jueves, sábados). Valora el buen descanso.
- Familia: asados dominicales con abuelos, acompaña a su hermano menor en sus partidos de básquet.

Prioridades Académicas Actuales:
1. Física II [PRIORIDAD 1 - CRÍTICA]: Desaprobó el 1er parcial. Debe aprobar sí o sí el 2do parcial el Viernes 30 de Octubre a las 09:00.
2. Programación II [PRIORIDAD 2]: Materia filtro. Buen nivel técnico pero requiere asegurar práctica constante.
3. Teoría de Lenguajes [PRIORIDAD 3]: Nivel inicial cero. Parcial el Sábado 24 de Octubre a las 09:00. Requiere estudio anticipado.
4. Estructura de Datos y Algoritmos: 1er parcial aprobado con 7. Final obligatorio.
5. Sistemas de Información I: Tranqui, solo resta terminar 1 diagrama.
6. Cálculo Numérico: Excelente dominio. Parcial el Miércoles 28 de Octubre a las 18:30 (repaso ligero).
7. Administración de Empresas: 10 en 1er parcial. Resta solo un oral grupal.

Reglas de interacción:
- Habla en español rioplatense natural (che, vos, dale), cercano, motivador, fraterno y técnico. Cero corporativismo.
- Considera sus tiempos de viaje en colectivo (salidas con 1 hora y cuarto de anticipación).
- Al calcular tiempos para parciales, calcula con exactitud matemática días y horas restantes respecto al datetime actual.
"""

class EngineAI:
    @staticmethod
    def classify_intent_and_extract(text: str, current_datetime_str: str) -> dict:
        prompt = f"""
        Fecha y hora actual de referencia: {current_datetime_str}.
        Mensaje recibido de Tobías: "{text}"

        Determina la intención y devuelve estrictamente un objeto JSON:
        {{
            "intent": "CREATE_EVENT" | "QUERY_SCHEDULE" | "LOG_HABIT" | "GENERAL_CONVERSATION",
            "event_data": {{
                "title": "string o null",
                "date_iso": "YYYY-MM-DDTHH:MM:SS o null (calculado relativo a la fecha actual)",
                "category": "ACADEMIC" | "UPSKILLING" | "HOUSEHOLD" | "FITNESS" | "SPIRITUAL" | "READING" | "LEISURE",
                "notes": "string o null"
            }},
            "query_subject": "string o null",
            "habit_summary": "string o null"
        }}
        Devuelve SOLO el JSON sin bloques de código ni texto adicional.
        """

        response = ai_client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json"
            )
        )

        try:
            return json.loads(response.text)
        except Exception:
            return {"intent": "GENERAL_CONVERSATION", "event_data": None}

    @staticmethod
    def evaluate_reflection(text: str, category: str, is_believer: bool = True) -> dict:
        prompt = f"""
        Tobías compartió esta reflexión o avance en '{category}':
        "{text}"

        Genera una respuesta fraternal, directa y práctica (1 a 2 párrafos cortos para WhatsApp).
        Asigna de 20 a 50 XP según el nivel de reflexión y esfuerzo.

        Formato estricto:
        FEEDBACK: [Tu respuesta]
        XP: [Número entero]
        """
        response = ai_client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
        )
        content = response.text or ""
        feedback = "Excelente avance en tus objetivos de hoy."
        xp = 35

        try:
            for line in content.split("\n"):
                if line.startswith("FEEDBACK:"):
                    feedback = line.replace("FEEDBACK:", "").strip()
                elif line.startswith("XP:"):
                    xp = int(line.replace("XP:", "").strip())
        except Exception:
            feedback = content.strip()

        return {"feedback": feedback, "xp": xp}

    @staticmethod
    def answer_schedule_query(query: str, events: list, current_datetime: datetime) -> str:
        events_context = "\n".join([
            f"- {e.title} ({e.category.value if hasattr(e.category, 'value') else e.category}): {e.event_date.strftime('%d/%m/%Y a las %H:%M')}"
            for e in events
        ]) if events else "No hay eventos agendados próximos."

        prompt = f"""
        Fecha y hora actual: {current_datetime.strftime('%d/%m/%Y %H:%M')}.
        Eventos agendados en base de datos:
        {events_context}

        Pregunta de Tobías: "{query}"

        Instrucciones:
        - Responde de forma clara y directa para WhatsApp.
        - Calcula con precisión los días y horas restantes para las fechas consultadas.
        - Si pregunta por Física II o Teoría de Lenguajes, dale un empuje motivador recordando su estrategia y prioridad.
        """
        response = ai_client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
        )
        return response.text or "No encontré fechas registradas para esa consulta."

    @staticmethod
    def handle_exception_replan(reason: str, remaining_blocks: list) -> str:
        blocks_text = "\n".join([f"- {b['label']} ({b['category']}) a las {b['time']}" for b in remaining_blocks])
        prompt = f"""
        Tobías reportó una EXCEPCIÓN en su rutina con este motivo: "{reason}"
        Bloques restantes de hoy:
        {blocks_text}

        Reorganizale la jornada de forma realista y sin culpa, cuidando que descanse y no sacrifique lo crítico (como repasar Física II si correspondía). Respuesta concisa en viñetas para WhatsApp.
        """
        response = ai_client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
        )
        return response.text or "Entendido el imprevisto. Reacomodamos el resto de la jornada."

    @staticmethod
    def transcribe_audio(audio_bytes: bytes) -> str:
        res = ai_client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/ogg"),
                "Transcribe de forma literal y precisa el mensaje en español sin agregar comentarios."
            ]
        )
        return (res.text or "").strip()