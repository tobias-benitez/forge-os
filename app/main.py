import logging
import json
from pathlib import Path
from datetime import datetime, date, timedelta
import pytz
import httpx
from pydantic import BaseModel
from fastapi import FastAPI, Request, HTTPException, Query, BackgroundTasks, UploadFile, File
from fastapi.responses import PlainTextResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from app import whatsapp_client
from app.config import settings, WHATSAPP_VERIFY_TOKEN
from app.whatsapp_client import send_whatsapp_message
from app.services.rescheduler import EngineAI
from app.services.syllabus_planner import SyllabusPlanner
from app.database import init_db, SessionLocal
from app.models.core import User, CalendarEvent, ActionLog, RoutineBlock, SubjectTopic, DailyCheckin, DayOfWeek, BlockCategory
from app.services.scheduler import start_scheduler
import xml.etree.ElementTree as ET
from app.services.daily_wisdom import get_daily_wisdom
from app.services.pdf_analyzer import extract_text_from_pdf, analyze_pdf_content
from app.services.auto_scheduler import recalculate_weekly_blocks
from app.whatsapp_client import send_whatsapp_message
ARG_TZ = pytz.timezone("America/Argentina/Buenos_Aires")
import random
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("forgeos")

app = FastAPI(title="ForgeOS Command Deck")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
tz = pytz.timezone("America/Argentina/Buenos_Aires")

from app.services.seed_data import seed_database

@app.on_event("startup")
def startup_event():
    init_db()
    seed_database()
    start_scheduler()

@app.get("/")
async def root():
    return {"status": "online", "system": "ForgeOS Command Deck", "dashboard": "/dashboard"}

# --- MODELOS PYDANTIC ---
class QuickLogRequest(BaseModel):
    action: str
    explanation: str = ""
    xp_type: str = "study_1h"

class RoutineBlockCompleteRequest(BaseModel):
    block_id: str
    label: str
    category: str = "GENERAL"

class NutritionLogRequest(BaseModel):
    score: int
    notes: str = ""

class HabitCheckRequest(BaseModel):
    habit_name: str
    details: str = ""

class GratitudeRequest(BaseModel):
    text: str

class RedeemRewardRequest(BaseModel):
    item_name: str
    cost_xp: int

class QuickTaskRequest(BaseModel):
    title: str
    scheduled_date: str = ""

def get_lunch_video(user, now_dt):
    is_weekend = now_dt.weekday() in [5, 6]
    if is_weekend:
        return {
            "title": "Fin de Semana: Almuerzo Libre // Mirá un capítulo de tu serie favorita",
            "channel": "Relax / Ocio",
            "duration": "Libre",
            "url": "https://www.crunchyroll.com",
            "is_free_choice": True
        }

    plist_url = getattr(user, "youtube_playlist_url", None)
    if plist_url:
        import re
        match = re.search(r"list=([a-zA-Z0-9_-]+)", plist_url)
        if match:
            plist_id = match.group(1)
            rss_url = f"https://www.youtube.com/feeds/videos.xml?playlist_id={plist_id}"
            headers = {"User-Agent": "Mozilla/5.0"}
            try:
                with httpx.Client(timeout=6.0, follow_redirects=True, headers=headers) as client:
                    resp = client.get(rss_url)
                    if resp.status_code == 200:
                        import xml.etree.ElementTree as ET
                        root = ET.fromstring(resp.text)
                        ns = {'yt': 'http://www.youtube.com/xml/schemas/2015', 'atom': 'http://www.w3.org/2005/Atom'}
                        entries = root.findall('atom:entry', ns)
                        if entries:
                            idx = now_dt.timetuple().tm_yday % len(entries)
                            chosen = entries[idx]
                            return {
                                "title": chosen.find('atom:title', ns).text,
                                "channel": chosen.find('atom:author/atom:name', ns).text or "Tu Playlist",
                                "duration": "Tu Lista",
                                "url": chosen.find('atom:link', ns).attrib.get('href'),
                                "is_free_choice": False
                            }
            except Exception as e:
                logger.error(f"Error parseando playlist RSS: {e}")

    return {
        "title": "Arquitectura de Software Limpia en Producción",
        "channel": "ByteByteGo",
        "duration": "15 min",
        "url": "https://www.youtube.com/watch?v=01ymxP_a5kQ",
        "is_free_choice": False
    }

# --- DASHBOARD PRINCIPAL ---
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_view(request: Request):
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user:
            user = User(name="Tobías", phone="541123588856", xp_total=0, streak_days=1)
            db.add(user)
            db.commit()
            db.refresh(user)

        total_xp = user.xp_total or 0
        level = (total_xp // 500) + 1
        xp_current_level = total_xp % 500
        xp_percent = int((xp_current_level / 500) * 100)

        ranks = ["Novato", "Aprendiz Constante", "Forjador de Hábitos", "Aspirante a Ingeniero", "Estratega Implacable", "Maestro Forge"]
        rank_title = ranks[min(level - 1, len(ranks) - 1)]

        now = datetime.now(tz)
        today_date = now.date()
        day_name = now.strftime("%A").upper()
        day_enum = getattr(DayOfWeek, day_name, None)

        dias_es = {
            "MONDAY": "Lunes", "TUESDAY": "Martes", "WEDNESDAY": "Miércoles",
            "THURSDAY": "Jueves", "FRIDAY": "Viernes", "SATURDAY": "Sábado", "SUNDAY": "Domingo"
        }
        current_day_es = dias_es.get(day_name, "Hoy")

        checkin = db.query(DailyCheckin).filter(
            DailyCheckin.user_id == user.id,
            DailyCheckin.checkin_date == today_date
        ).first()
        if not checkin:
            checkin = DailyCheckin(user_id=user.id, checkin_date=today_date)
            db.add(checkin)
            db.commit()
            db.refresh(checkin)

        blocks = []
        if day_enum:
            blocks = db.query(RoutineBlock).filter(
                RoutineBlock.user_id == user.id,
                RoutineBlock.day_of_week == day_enum
            ).order_by(RoutineBlock.start_time).all()

        today_start = datetime.combine(today_date, datetime.min.time())
        today_logs = db.query(ActionLog).filter(
            ActionLog.user_id == user.id,
            ActionLog.created_at >= today_start
        ).all()
        completed_block_labels = {log.input_text.replace("Rutina cumplida: ", "").strip() for log in today_logs}

        events = db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user.id,
            CalendarEvent.is_completed == False
        ).order_by(CalendarEvent.event_date).all()

        # Detección de Modo Examen Inminente (menos de 7 días)
        defcon1_active = False
        defcon1_subject = ""
        for ev in events:
            if ev.category == BlockCategory.ACADEMIC and ev.event_date:
                days_to_exam = (ev.event_date.date() - today_date).days
                if 0 <= days_to_exam <= 7:
                    defcon1_active = True
                    defcon1_subject = ev.title
                    break

        roadmap_fisica = SyllabusPlanner.calculate_study_roadmap(user.id, "Física II")
        roadmap_lenguajes = SyllabusPlanner.calculate_study_roadmap(user.id, "Teoría de Lenguajes")

        # Traer todas las materias únicas del usuario
        all_subject_records = db.query(SubjectTopic.subject_name).filter(
            SubjectTopic.user_id == user.id
        ).distinct().all()

        # Lista con los nombres de todas las materias (ej: ['Física II', 'Teoría de Lenguajes', 'Cálculo'])
        subject_names = [s[0] for s in all_subject_records] if all_subject_records else ["Física II", "Teoría de Lenguajes"]
        if "Física II" not in subject_names:
            subject_names.insert(0, "Física II")

        # Armar roadmaps dinámicos para cada materia
        all_roadmaps = []
        for s_name in subject_names:
            rm = SyllabusPlanner.calculate_study_roadmap(user.id, s_name)
            if rm:
                all_roadmaps.append(rm)

        logs = db.query(ActionLog).filter(
            ActionLog.user_id == user.id
        ).order_by(ActionLog.created_at.desc()).limit(12).all()

        current_week = now.isocalendar()[1]

        # Progresión RPG: De Soldado/Vikingo a Rey Conquistador
        avatar_seeds = {
            1: "Ragnar-Recruit",
            2: "Viking-Warrior",
            3: "Nordic-Berserker",
            4: "Iron-Warlord",
            5: "King-Conqueror"
        }
        avatar_seed = avatar_seeds.get(level, "God-Emperor")

        # Regla de fin de semana para comidas
        is_weekend = now.weekday() in [5, 6]  # Sábado (5) o Domingo (6)

        # Frase y versículo dinámicos del día
        daily_quote, daily_verse = get_daily_wisdom()

        # Radar de Atributos RPG calculado a partir de logs del día
        intellect_xp = sum(l.earned_xp for l in today_logs if l.category == BlockCategory.ACADEMIC)
        vitality_xp = sum(l.earned_xp for l in today_logs if l.category == BlockCategory.FITNESS)
        spirit_xp = sum(l.earned_xp for l in today_logs if l.category == BlockCategory.SPIRITUAL)
        leadership_xp = sum(l.earned_xp for l in today_logs if l.category == BlockCategory.UPSKILLING or l.category == BlockCategory.READING)

        attributes = {
            "intellect": min(100, int((intellect_xp / 150) * 100)),
            "vitality": min(100, int((vitality_xp / 100) * 100)),
            "spirit": min(100, int((spirit_xp / 60) * 100)),
            "leadership": min(100, int((leadership_xp / 100) * 100))
        }

        active_video = get_lunch_video(user, now)
        

        context = {
            "request": request,
            "user": user,
            "level": level,
            "rank_title": rank_title,
            "xp_current_level": xp_current_level,
            "xp_percent": xp_percent,
            "avatar_seed": avatar_seed,
            "is_weekend": is_weekend,
            "daily_quote": daily_quote,
            "daily_verse": daily_verse,
            "attributes": attributes,
            "current_day_es": current_day_es,
            "current_week": current_week,
            "checkin": checkin,
            "blocks": blocks,
            "completed_block_labels": completed_block_labels,
            "events": events,
            "defcon1_active": defcon1_active,
            "defcon1_subject": defcon1_subject,
            "roadmap_fisica": roadmap_fisica,
            "roadmap_lenguajes": roadmap_lenguajes,
            "all_roadmaps": all_roadmaps,
            "active_video": active_video,
            "logs": logs
        }

        return templates.TemplateResponse(request=request, name="dashboard.html", context=context)
    except Exception as e:
        logger.error(f"Error renderizando dashboard: {e}")
        raise e
    finally:
        db.close()

async def send_lunch_reminder():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user or not user.phone:
            return

        now = datetime.now(ARG_TZ)
        video = get_lunch_video(user, now)

        msg = "🍽️ *HORA DE ALMUERZO // RECARGA*\n\n"
        if video.get("is_free_choice"):
            msg += "Hoy es día libre o fin de semana. No hay video obligatorio:\n"
            msg += "🎬 *Podés ver un capítulo de tu serie o anime favorito.*\n"
            msg += f"👉 Enlace: {video['url']}\n"
        else:
            msg += "Video de alto valor para acompañar la comida:\n"
            msg += f"📺 *{video['title']}*\n"
            msg += f"👤 Canal: {video['channel']} ({video['duration']})\n"
            msg += f"🔗 Ver en YouTube: {video['url']}\n"

        msg += "\nComé tranquilo, descansá la vista y desconectá 30 minutos."
        await send_whatsapp_message(user.phone, msg)
        logger.info(f"Recordatorio de almuerzo enviado a {user.phone}")
    except Exception as e:
        logger.error(f"Error enviando almuerzo: {e}")
    finally:
        db.close()

# --- API: GRATITUD DIARIA CON FILTRO ANTI-REPETICIÓN ---
@app.post("/api/gratitude/submit")
async def api_submit_gratitude(req: GratitudeRequest):
    db = SessionLocal()
    try:
        user = db.query(User).first()
        today_date = date.today()
        text = req.text.strip()
        if len(text) < 10:
            return JSONResponse(status_code=400, content={"error": "Escribí algo más específico sobre tu día."})

        # Chequeo contra los últimos 7 días
        recent_logs = db.query(ActionLog).filter(
            ActionLog.user_id == user.id,
            ActionLog.category == BlockCategory.SPIRITUAL,
            ActionLog.created_at >= datetime.utcnow() - timedelta(days=7)
        ).all()

        is_repeated = any(text.lower() in log.input_text.lower() or log.input_text.lower() in text.lower() for log in recent_logs)

        checkin = db.query(DailyCheckin).filter(
            DailyCheckin.user_id == user.id,
            DailyCheckin.checkin_date == today_date
        ).first()

        if is_repeated:
            earned = 25
            feedback = "Agradecido, pero intentá buscar detalles específicos de hoy en vez de repetir siempre lo mismo."
        else:
            earned = 60
            feedback = "Gratitud genuina registrada en el altar. Descanso en paz."

        checkin.gratitude_done = True
        checkin.gratitude_text = text
        user.xp_total = (user.xp_total or 0) + earned

        log = ActionLog(
            user_id=user.id,
            category=BlockCategory.SPIRITUAL,
            input_text=f"Gratitud nocturna: {text}",
            ai_feedback=feedback,
            earned_xp=earned
        )
        db.add(log)
        db.commit()
        return {"status": "ok", "earned": earned, "feedback": feedback, "new_xp": user.xp_total}
    finally:
        db.close()

# --- API: COMPLETAR RUTINA DEL DÍA ---
@app.post("/api/routine/complete")
async def api_complete_routine_block(req: RoutineBlockCompleteRequest):
    db = SessionLocal()
    try:
        user = db.query(User).first()
        label_lower = req.label.lower()

        if any(w in label_lower for w in ["cursada", "facultad", "universidad"]):
            earned = 45
            ai_msg = "Cursada presencial completada."
        elif any(w in label_lower for w in ["podcast", "inglés", "ingles", "viaje", "bondi"]):
            earned = 35
            ai_msg = "Tiempo muerto convertido en valor formativo."
        elif any(w in label_lower for w in ["estudio", "física", "lenguajes", "parcial"]):
            earned = 100
            ai_msg = "Bloque de estudio pesado liquidado."
        elif any(w in label_lower for w in ["entrenamiento", "gimnasio", "fuerza"]):
            earned = 80
            ai_msg = "Cuerpo y disciplina física forjados."
        else:
            earned = 50
            ai_msg = f"Bloque '{req.label}' cumplido."

        user.xp_total = (user.xp_total or 0) + earned
        log = ActionLog(
            user_id=user.id,
            category=BlockCategory.ACADEMIC if "estudio" in label_lower or "cursada" in label_lower else BlockCategory.UPSKILLING,
            input_text=f"Rutina cumplida: {req.label}",
            ai_feedback=ai_msg,
            earned_xp=earned
        )
        db.add(log)
        db.commit()
        return {"status": "ok", "earned": earned, "new_xp": user.xp_total}
    finally:
        db.close()

# --- API: HÁBITOS DE VIDA (ORACIÓN, LECTURA, VIDEO ALMUERZO) ---
@app.post("/api/habits/toggle")
async def api_toggle_habit(req: HabitCheckRequest):
    db = SessionLocal()
    try:
        user = db.query(User).first()
        today_date = date.today()
        checkin = db.query(DailyCheckin).filter(
            DailyCheckin.user_id == user.id,
            DailyCheckin.checkin_date == today_date
        ).first()

        earned = 0
        desc = ""
        cat = BlockCategory.SPIRITUAL

        if req.habit_name == "prayer":
            checkin.prayer_done = True
            earned = 50
            desc = "Santuario y Oración: Encomendé mi camino a Dios"
            cat = BlockCategory.SPIRITUAL
        elif req.habit_name == "reading":
            checkin.reading_done = True
            # Bonus si explicó lo que leyó
            earned = 85 if len(req.details.strip()) > 15 else 50
            desc = f"Lectura: 'Cómo ganar amigos' ({req.details if req.details else '15 págs'})"
            cat = BlockCategory.READING
        elif req.habit_name == "meal_video":
            checkin.mindful_eating = True
            earned = 45
            desc = "Comida Inteligente: Vi video formativo en vez de contenido vacío"
            cat = BlockCategory.UPSKILLING

        user.xp_total = (user.xp_total or 0) + earned
        log = ActionLog(
            user_id=user.id,
            category=cat,
            input_text=desc,
            ai_feedback="Hábito ejecutado con compromiso.",
            earned_xp=earned
        )
        db.add(log)
        db.commit()
        return {"status": "ok", "earned": earned, "new_xp": user.xp_total}
    finally:
        db.close()

# --- API: NUTRICIÓN DEL 1 AL 10 ---
@app.post("/api/nutrition/log")
async def api_log_nutrition(req: NutritionLogRequest):
    db = SessionLocal()
    try:
        user = db.query(User).first()
        today_date = date.today()
        checkin = db.query(DailyCheckin).filter(
            DailyCheckin.user_id == user.id,
            DailyCheckin.checkin_date == today_date
        ).first()

        checkin.nutrition_score = req.score
        checkin.nutrition_notes = req.notes

        if req.score >= 8:
            earned = 80
            fb = f"Nutrición óptima ({req.score}/10). Proteína y macros alineados al gym."
        elif req.score >= 6:
            earned = 50
            fb = f"Buena nutrición ({req.score}/10). Sólido balance."
        else:
            earned = 20
            fb = f"Día flexible ({req.score}/10). Mañana se retoma el estándar."

        user.xp_total = (user.xp_total or 0) + earned
        log = ActionLog(
            user_id=user.id,
            category=BlockCategory.FITNESS,
            input_text=f"Nutrición del día: {req.score}/10 {f'({req.notes})' if req.notes else ''}",
            ai_feedback=fb,
            earned_xp=earned
        )
        db.add(log)
        db.commit()
        return {"status": "ok", "score": req.score, "earned": earned, "new_xp": user.xp_total}
    finally:
        db.close()

# --- API: ACCIÓN RÁPIDA / PRUEBA DE TRABAJO (ANTI-MENTIRA) ---
@app.post("/api/action/log")
async def api_quick_log(req: QuickLogRequest):
    db = SessionLocal()
    try:
        user = db.query(User).first()
        base_xp = {
            "help_friend": 90,
            "leadership": 75,
            "study_1h": 60,
            "study_2h": 120,
            "workout": 80,
            "quick": 35
        }.get(req.xp_type, 50)

        # Bonus por explicar con tus palabras lo que hiciste
        bonus = 40 if len(req.explanation.strip()) >= 20 else 0
        total_earned = base_xp + bonus

        user.xp_total = (user.xp_total or 0) + total_earned
        log = ActionLog(
            user_id=user.id,
            category=BlockCategory.UPSKILLING,
            input_text=f"{req.action} {f'// Explicación: {req.explanation}' if req.explanation else ''}",
            ai_feedback=f"Registrado (+{base_xp} base {f'+{bonus} bonus síntesis' if bonus else ''}).",
            earned_xp=total_earned
        )
        db.add(log)
        db.commit()
        return {"status": "ok", "new_xp": user.xp_total, "earned": total_earned}
    finally:
        db.close()

# --- API: TIENDA DE PUNTOS (RATIO 2.5:1) ---
@app.post("/api/rewards/redeem")
async def api_redeem_reward(req: RedeemRewardRequest):
    db = SessionLocal()
    try:
        user = db.query(User).first()
        current_xp = user.xp_total or 0
        if current_xp < req.cost_xp:
            return JSONResponse(status_code=400, content={"error": f"Te faltan {req.cost_xp - current_xp} XP."})

        user.xp_total = current_xp - req.cost_xp
        log = ActionLog(
            user_id=user.id,
            category=BlockCategory.LEISURE,
            input_text=f"Canje en Tienda: {req.item_name}",
            ai_feedback="Recompensa desbloqueada con disciplina neta.",
            earned_xp=-req.cost_xp
        )
        db.add(log)
        db.commit()
        return {"status": "ok", "new_xp": user.xp_total, "item": req.item_name}
    finally:
        db.close()

# --- API: SUBIR ARCHIVOS / PDFS DE MATERIAS ---
@app.post("/api/subjects/{subject_name}/upload")
async def api_upload_subject_file(subject_name: str, file: UploadFile = File(...)):
    db = SessionLocal()
    try:
        user = db.query(User).first()
        target_dir = BASE_DIR / "uploads" / subject_name
        target_dir.mkdir(parents=True, exist_ok=True)
        file_bytes = await file.read()
        file_path = target_dir / file.filename
        with open(file_path, "wb") as buffer:
            buffer.write(file_bytes)

        # Analizar contenido con pypdf y Gemini
        extracted = extract_text_from_pdf(file_bytes)
        analysis = analyze_pdf_content(file.filename, extracted)

        msg = f"Archivo '{file.filename}' guardado en {subject_name}."
        if analysis.get("type") == "EXAM_SCHEDULE":
            for ex in analysis.get("exams", []):
                try:
                    dt = datetime.fromisoformat(ex["date_iso"])
                    ev = CalendarEvent(user_id=user.id, title=f"[{subject_name}] {ex['title']}", event_date=dt, category=BlockCategory.ACADEMIC)
                    db.add(ev)
                except Exception:
                    pass
            db.commit()
            msg += " Se detectaron y agendaron fechas de exámenes automáticamente."
        elif analysis.get("type") == "SYLLABUS_MATERIAL" and analysis.get("topics"):
            for top in analysis.get("topics", []):
                st = SubjectTopic(user_id=user.id, subject_name=subject_name, unit_number=top.get("unit", 1), title=top.get("title", "Unidad"), estimated_hours=top.get("hours", 6.0))
                db.add(st)
            db.commit()
            msg += " Se detectaron y agregaron temas de estudio al plan de la materia."

        return {"status": "ok", "message": msg}
    finally:
        db.close()

# --- API: TAREAS RÁPIDAS ---
@app.post("/api/tasks/create")
async def api_create_task(req: QuickTaskRequest):
    db = SessionLocal()
    try:
        user = db.query(User).first()
        task_dt = datetime.fromisoformat(req.scheduled_date) if req.scheduled_date else datetime.now()
        new_task = CalendarEvent(
            user_id=user.id,
            title=req.title,
            event_date=task_dt,
            category=BlockCategory.HOUSEHOLD
        )
        db.add(new_task)
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()

@app.post("/api/tasks/{task_id}/toggle")
async def api_toggle_task(task_id: str):
    db = SessionLocal()
    try:
        task = db.query(CalendarEvent).filter(CalendarEvent.id == task_id).first()
        if task:
            task.is_completed = True
            db.commit()
        return {"status": "ok"}
    finally:
        db.close()

# --- WEBHOOK & COMANDOS DIRECTOS POR WHATSAPP ---
@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(content=hub_challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Token inválido")
async def send_morning_briefing():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user or not user.phone:
            return

        now = datetime.now(ARG_TZ)
        today_dow = DayOfWeek(now.strftime("%A").upper())

        today_blocks = (
            db.query(RoutineBlock)
            .filter(RoutineBlock.user_id == user.id, RoutineBlock.day_of_week == today_dow)
            .order_by(RoutineBlock.start_time.asc())
            .all()
        )

        quote, verse = get_daily_wisdom()

        msg = "🌅 *DESPERTAR // FORGE OS*\n\n"
        if getattr(user, "is_believer", True):
            msg += f"✝️ *Versículo del día:*\n_{verse['text']}_\n— *{verse['ref']}*\n\n"
            msg += "🙏 *Oración:* Encomienda tu jornada, tu estudio y tu fuerza a Dios antes de arrancar.\n\n"

        msg += f"🏛️ *Cita Estoica:*\n_{quote['text']}_\n— *{quote['author']}*\n\n"
        msg += f"⚔️ *MISIONES DE HOY ({today_dow.name}):*\n"
        if today_blocks:
            for b in today_blocks:
                msg += f"• {b.start_time.strftime('%H:%M')} | {b.label}\n"
        else:
            msg += "• Día de recuperación familiar y descanso.\n"

        msg += "\nRespondé *'arranco'* o tildá tus bloques en la web."
        await send_whatsapp_message(user.phone, msg)
        logger.info(f"Morning briefing enviado a {user.phone}")
    except Exception as e:
        logger.error(f"Error morning briefing: {e}")
    finally:
        db.close()

async def check_upcoming_routine_blocks():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user or not user.phone:
            return

        now = datetime.now(ARG_TZ)
        today_dow = DayOfWeek(now.strftime("%A").upper())

        blocks = (
            db.query(RoutineBlock)
            .filter(RoutineBlock.user_id == user.id, RoutineBlock.day_of_week == today_dow)
            .all()
        )

        for b in blocks:
            diff_min = (b.start_time.hour * 60 + b.start_time.minute) - (now.hour * 60 + now.minute)
            # Notifica entre 12 y 17 minutos antes de iniciar
            if 12 <= diff_min <= 17:
                msg = f"⏳ *RECORDATORIO DE BLOQUE (en 15 min):*\n\n"
                msg += f"📍 *{b.label}*\n"
                msg += f"⏰ Inicio: {b.start_time.strftime('%H:%M')} ({b.duration_minutes}m)\n\n"
                msg += "Prepará el mate o el agua, silenciá distracciones y metele foco."
                await send_whatsapp_message(user.phone, msg)
                logger.info(f"Notificación de bloque '{b.label}' enviada.")
    except Exception as e:
        logger.error(f"Error comprobando bloques: {e}")
    finally:
        db.close()

async def send_evening_review():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user or not user.phone:
            return
        msg = "🌙 *CIERRE DEL DÍA // FORGE OS*\n\n"
        msg += "¿Completaste tus bloques de hoy? Respondé con tu balance o registrá tus misiones en la web para no perder la racha de XP."
        await send_whatsapp_message(user.phone, msg)
    except Exception as e:
        logger.error(f"Error evening review: {e}")
    finally:
        db.close()

async def process_and_reply(recipient: str, text: str):
    now = datetime.now(tz)
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == recipient).first()
        if not user:
            user = User(phone=recipient, name="Tobías")
            db.add(user)
            db.commit()
            db.refresh(user)

        lower_text = text.lower().strip()
        
        # COMANDO: RESUMEN AYER
        if lower_text in ["resumen ayer", "que hice ayer", "ayer"]:
            yesterday = (now - timedelta(days=1)).date()
            y_checkin = db.query(DailyCheckin).filter(DailyCheckin.user_id == user.id, DailyCheckin.checkin_date == yesterday).first()
            y_logs = db.query(ActionLog).filter(
                ActionLog.user_id == user.id,
                ActionLog.created_at >= datetime.combine(yesterday, datetime.min.time()),
                ActionLog.created_at <= datetime.combine(yesterday, datetime.max.time())
            ).all()

            nutr = f"{y_checkin.nutrition_score}/10" if y_checkin and y_checkin.nutrition_score else "No registrada"
            grat = y_checkin.gratitude_text if y_checkin and y_checkin.gratitude_text else "Sin registrar"
            total_earned = sum(l.earned_xp for l in y_logs if l.earned_xp > 0)

            reply = (
                f"📊 *Auditoría de Ayer ({yesterday.strftime('%d/%m')}):*\n"
                f"• Nutrición: {nutr}\n"
                f"• Gratitud: \"{grat}\"\n"
                f"• Acciones cumplidas: {len(y_logs)}\n"
                f"• XP ganado: +{total_earned} XP ⭐"
            )

        # COMANDO: QUE COMI
        elif lower_text.startswith("que comi"):
            recent_nutr = db.query(ActionLog).filter(
                ActionLog.user_id == user.id,
                ActionLog.category == BlockCategory.FITNESS
            ).order_by(ActionLog.created_at.desc()).limit(3).all()
            if recent_nutr:
                lines = [f"• {l.created_at.strftime('%a %d/%m')}: {l.input_text}" for l in recent_nutr]
                reply = "🥗 *Últimas comidas registradas:*\n" + "\n".join(lines)
            else:
                reply = "No tenés comidas registradas recientemente."

        # COMANDO: REGISTRO RÁPIDO DE COMIDA
        elif lower_text.startswith("comi ") or any(w in lower_text for w in ["almorcé ", "cené "]):
            score = 8 if any(w in lower_text for w in ["pollo", "arroz", "huevos", "proteina", "sano", "bien"]) else 6
            earned = 70 if score >= 8 else 45
            user.xp_total = (user.xp_total or 0) + earned
            log = ActionLog(
                user_id=user.id,
                category=BlockCategory.FITNESS,
                input_text=f"Nutrición: {text}",
                ai_feedback=f"Comida registrada ({score}/10).",
                earned_xp=earned
            )
            db.add(log)
            db.commit()
            reply = f"🥗 *Nutrición guardada ({score}/10):*\n\"{text}\"\n⭐ +{earned} XP de Vitalidad."

        # COMANDO: ESTADO DEL LIBRO
        elif lower_text in ["libro", "libro estado", "que estoy leyendo"]:
            reply = (
                "📚 *Libro Actual:* 'Cómo ganar amigos e influir sobre las personas'\n"
                "• *Capítulo Activo:* Cap 1 - No critiques, no condenes ni te quejes.\n"
                "• *Reto de Hoy:* Si alguien comete un error, buscá entender su motivo sin quejarte en voz alta.\n"
                "• Para registrar avance: escribí 'lei [páginas o resumen]'."
            )

        # COMANDO: PARCIALES / EXÁMENES
        elif lower_text in ["parciales", "examenes", "fechas"]:
            events = db.query(CalendarEvent).filter(
                CalendarEvent.user_id == user.id,
                CalendarEvent.category == BlockCategory.ACADEMIC,
                CalendarEvent.is_completed == False
            ).order_by(CalendarEvent.event_date).all()
            if events:
                lines = [f"• *{ev.title}*: {ev.event_date.strftime('%d/%m a las %H:%M')}" for ev in events]
                reply = "🚨 *Horizonte de Exámenes:*\n" + "\n".join(lines)
            else:
                reply = "No tenés exámenes pendientes agendados."

        # COMANDO: TEMAS DE MATERIA
        elif "temas" in lower_text:
            subj = "Teoría de Lenguajes" if "lenguaje" in lower_text else "Física II"
            reply = SyllabusPlanner.get_roadmap_summary_text(user.id, subj)
        
        # COMANDO DIRECTO: PLAYLIST YOUTUBE
        elif lower_text.startswith("playlist ") or lower_text.startswith("/playlist "):
            parts = text.strip().split(maxsplit=1)
            if len(parts) > 1:
                clean_url = parts[1].strip()
                # Actualizar tanto el usuario del chat como el del dashboard web
                all_users = db.query(User).all()
                for u in all_users:
                    u.youtube_playlist_url = clean_url
                db.commit()
                reply = f"✅ *Playlist actualizada con éxito.*\n\n🔗 Enlace guardado: {clean_url}\nYa quedó sincronizado tanto en WhatsApp como en la web."
            else:
                reply = "⚠️ Mandá el link así: `playlist https://www.youtube.com/playlist?list=...`"

        # COMANDO POR WHATSAPP: CONFIGURAR PREFERENCIA DE FE
        elif any(w in lower_text for w in ["soy cristiano", "no soy cristiano", "soy ateo", "recordatorios fe"]):
            if "no" in lower_text or "ateo" in lower_text:
                user.is_believer = False
                reply = "Entendido. Se deshabilitaron los recordatorios de oración y el versículo diario. El sistema se enfocará 100% en rendimiento académico, gimnasio y hábitos."
            else:
                user.is_believer = True
                reply = "Configurado. Recibirás el versículo canónico matutino y la llamada a la gratitud nocturna."
            db.commit()

        # REPLANIFICACIÓN POR IMPREVISTO
        elif any(kw in lower_text for kw in ["se me complicó", "se me complico", "no llego", "imprevisto", "reprogramar"]):
            day_name = now.strftime("%A").upper()
            day_enum = getattr(DayOfWeek, day_name, None)
            remaining_blocks = []
            if day_enum:
                blocks = db.query(RoutineBlock).filter(
                    RoutineBlock.user_id == user.id,
                    RoutineBlock.day_of_week == day_enum
                ).all()
                for b in blocks:
                    if b.start_time >= now.time():
                        remaining_blocks.append({
                            "label": b.label,
                            "category": b.category.value if hasattr(b.category, "value") else b.category,
                            "time": b.start_time.strftime("%H:%M")
                        })
            reply = EngineAI.handle_exception_replan(text, remaining_blocks)

        # CUALQUIER OTRA CONSULTA
        else:
            events = db.query(CalendarEvent).filter(CalendarEvent.user_id == user.id, CalendarEvent.is_completed == False).all()
            reply = EngineAI.answer_schedule_query(text, events, now)

    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        reply = "Hubo un error procesando el mensaje."
    finally:
        db.close()

    await send_whatsapp_message(recipient, reply)

class CreateSubjectRequest(BaseModel):
    name: str
    exam_date: str = ""
    hours_per_week: float = 6.0

class UserFeSettingsRequest(BaseModel):
    is_believer: bool
    receive_spiritual_reminders: bool = True

# --- API: CREAR NUEVA MATERIA Y SU CARPETA ---
@app.post("/api/subjects/create")
async def api_create_subject(req: CreateSubjectRequest):
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user:
            return JSONResponse(status_code=404, content={"error": "Usuario no encontrado"})

        sanitized_name = req.name.strip().replace(" ", "_")
        target_dir = BASE_DIR / "uploads" / sanitized_name
        target_dir.mkdir(parents=True, exist_ok=True)

        if req.exam_date:
            try:
                ev_dt = datetime.fromisoformat(req.exam_date)
                new_ev = CalendarEvent(
                    user_id=user.id,
                    title=f"Parcial {req.name}",
                    event_date=ev_dt,
                    category=BlockCategory.ACADEMIC
                )
                db.add(new_ev)
            except Exception:
                pass

        new_topic = SubjectTopic(
            user_id=user.id,
            subject_name=req.name,
            unit_number=1,
            title=f"Introducción y Unidad 1 de {req.name}",
            estimated_hours=req.hours_per_week,
            target_week=1
        )
        db.add(new_topic)
        db.commit()
        return {"status": "ok", "subject": req.name}
    finally:
        db.close()

# --- API: GUARDAR LINK DE YOUTUBE ---
@app.post("/api/user/youtube-playlist")
async def api_save_youtube_playlist(url: str = Query(...)):
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if user:
            user.youtube_playlist_url = url.strip()
            db.commit()
            return {"status": "ok", "url": user.youtube_playlist_url}
        return JSONResponse(status_code=404, content={"error": "Usuario no encontrado"})
    finally:
        db.close()


@app.get("/api/heartbeat-cron")
async def api_heartbeat_cron():
    """
    Endpoint de latido cardíaco invocado cada 5 minutos por cron-job.org.
    Mantiene el contenedor de Render despierto y despacha las alertas a su hora exacta.
    """
    now = datetime.now(ARG_TZ)

    # 1. Mañana (07:15 - 07:20 AM)
    if now.hour == 7 and 15 <= now.minute <= 20:
        await send_morning_briefing()

    # 2. Almuerzo (13:00 - 13:05 PM)
    if now.hour == 13 and 0 <= now.minute <= 5:
        await send_lunch_reminder()

    # 3. Monitor de bloques (15 min antes de cursada/gym/estudio)
    await check_upcoming_routine_blocks()

    # 4. Cierre nocturno (22:30 - 22:35 PM)
    if now.hour == 22 and 30 <= now.minute <= 35:
        await send_evening_review()

    return {"status": "alive", "time": now.strftime("%Y-%m-%d %H:%M:%S")}

@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
    except Exception:
        raw_body = await request.body()
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception:
            return JSONResponse(content={"status": "invalid_json"}, status_code=200)

    try:
        entries = payload.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                for msg in messages:
                    remitente = msg.get("from")
                    if msg.get("type") == "text":
                        texto = msg.get("text", {}).get("body", "").strip()
                        background_tasks.add_task(process_and_reply, remitente, texto)
    except Exception as e:
        logger.error(f"Error procesando webhook: {e}")

    return JSONResponse(content={"status": "received"}, status_code=200)

@app.get("/api/test-morning-message")
async def api_test_morning():
    await send_morning_briefing()
    return {"status": "ok", "message": "Mensaje enviado a tu WhatsApp"}

@app.get("/api/test-lunch-message")
async def api_test_lunch():
    await send_lunch_reminder()
    return {"status": "ok", "message": "Mensaje de almuerzo disparado a WhatsApp"}

@app.get("/api/admin/reset-routine")
async def api_reset_routine():
    """Limpia los bloques antiguos y aplica la rutina canónica limpia."""
    from app.services.seed_data import seed_database
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if user:
            db.query(RoutineBlock).filter(RoutineBlock.user_id == user.id).delete()
            db.commit()
            seed_database()
            return {"status": "ok", "message": "Rutina sincronizada. Lista para recibir tus programas en PDF."}
        return {"status": "error", "message": "Usuario no encontrado"}
    finally:
        db.close()