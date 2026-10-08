import io
import json
from pypdf import PdfReader
from app.services.rescheduler import EngineAI

def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages[:10]: # Primeras 10 páginas para análisis rápido
        t = page.extract_text()
        if t:
            text += t + "\n"
    return text[:8000]

def analyze_pdf_content(filename: str, pdf_text: str):
    prompt = f"""
Analiza este documento universitario ({filename}):
Texto extraído:
\"\"\"{pdf_text}\"\"\"

Determina:
1. "type": "EXAM_SCHEDULE" si contiene fechas de parciales/entregas, o "SYLLABUS_MATERIAL" si es temario, apuntes o guía de ejercicios.
2. Si es "EXAM_SCHEDULE", extrae una lista "exams": [{{"title": "Parcial 1", "date_iso": "YYYY-MM-DDTHH:MM:SS"}}].
3. Si es "SYLLABUS_MATERIAL", extrae "topics": [{{"unit": 1, "title": "Nombre tema", "hours": 8.0}}].

Responde estrictamente en formato JSON válido sin markdown:
{{"type": "...", "exams": [...], "topics": [...]}}
"""
    try:
        if hasattr(EngineAI, "client") and EngineAI.client:
            res = EngineAI.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            raw = res.text.strip().replace("```json", "").replace("```", "")
            return json.loads(raw)
    except Exception:
        pass
    return {"type": "SYLLABUS_MATERIAL", "exams": [], "topics": []}