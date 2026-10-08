import logging
from datetime import datetime, timedelta
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from app.database import SessionLocal
from app.models.core import User, RoutineBlock, CalendarEvent, DayOfWeek, BlockCategory
from app.whatsapp_client import send_whatsapp_message

logger = logging.getLogger("forgeos")
tz = pytz.timezone("America/Argentina/Buenos_Aires")
scheduler = AsyncIOScheduler(timezone=tz)

notified_blocks_today = set()

# --- MONITOREO CONTINUO: AVISOS 15 MIN ANTES DE CADA BLOQUE ---
async def check_upcoming_routine_blocks():
    now = datetime.now(tz)
    day_name = now.strftime("%A").upper()
    day_enum = getattr(DayOfWeek, day_name, None)
    if not day_enum:
        return

    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user or not user.phone:
            return

        blocks = db.query(RoutineBlock).filter(
            RoutineBlock.user_id == user.id,
            RoutineBlock.day_of_week == day_enum
        ).all()

        target_time = (now + timedelta(minutes=15)).time()
        
        for b in blocks:
            block_key = f"{now.strftime('%Y-%m-%d')}_{b.id}_{b.start_time.strftime('%H:%M')}"
            if block_key in notified_blocks_today:
                continue

            # Margen de 2 minutos para el trigger
            diff_sec = abs((datetime.combine(now.date(), b.start_time) - datetime.combine(now.date(), target_time)).total_seconds())
            if diff_sec <= 120:
                notified_blocks_today.add(block_key)
                
                # Contexto especial según categoría
                extra_note = ""
                if "Física" in b.label:
                    extra_note = "\n🚨 *Materia crítica:* Cero distracciones, foco en ejercicios de parcial."
                elif "Viaje" in b.label or "Colectivo" in b.label:
                    extra_note = "\n🚌 *Ojo bondi:* Salí con 1h 15m de margen para no llegar con la lengua afuera."

                msg = (
                    f"⏰ *En 15 minutos arranca:* {b.label}\n"
                    f"Horario: *{b.start_time.strftime('%H:%M')}* ({b.duration_minutes} min){extra_note}\n\n"
                    f"¡A meterle garra, Tobías!"
                )
                await send_whatsapp_message(user.phone, msg)
                logger.info(f"Recordatorio de bloque '{b.label}' enviado a {user.phone}")

    except Exception as e:
        logger.error(f"Error en monitor continuo de bloques: {e}")
    finally:
        db.close()

# --- 08:00 AM: BRIEFING MATUTINO COMPLETO ---
async def send_morning_briefing():
    notified_blocks_today.clear() # Limpiar hash del día previo
    now = datetime.now(tz)
    day_name = now.strftime("%A").upper()
    day_enum = getattr(DayOfWeek, day_name, None)

    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user or not user.phone:
            return

        blocks = []
        if day_enum:
            blocks = db.query(RoutineBlock).filter(
                RoutineBlock.user_id == user.id,
                RoutineBlock.day_of_week == day_enum
            ).order_by(RoutineBlock.start_time).all()

        schedule_text = "\n".join([
            f"• *{b.start_time.strftime('%H:%M')}* - {b.label} ({b.duration_minutes} min)"
            for b in blocks
        ]) if blocks else "Día libre de bloques fijos."

        # Chequear próximos parciales
        events = db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user.id,
            CalendarEvent.event_date >= now.replace(tzinfo=None)
        ).order_by(CalendarEvent.event_date).limit(2).all()

        events_text = "\n".join([
            f"⚠️ *{e.title}*: faltan {(e.event_date - now.replace(tzinfo=None)).days} días ({e.event_date.strftime('%d/%m a las %H:%M')})"
            for e in events
        ]) if events else "Sin parciales inmediatos."

        msg = (
            f"¡Buen día, {user.name}! ☀️ Arrancamos con todo hoy {now.strftime('%d/%m')}.\n\n"
            f"📋 *Hoja de ruta del día:*\n{schedule_text}\n\n"
            f"🎯 *Horizonte de combate:*\n{events_text}\n\n"
            f"Acordate: constancia, disciplina y la ayuda de Dios para meter este cuatri. ¡A romperla!"
        )
        await send_whatsapp_message(user.phone, msg)
        logger.info(f"Morning briefing enviado a {user.phone}")
    except Exception as e:
        logger.error(f"Error en morning briefing: {e}")
    finally:
        db.close()

# --- 22:30 PM: BALANCE NOCTURNO Y XP ---
async def send_evening_review():
    now = datetime.now(tz)
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user or not user.phone:
            return

        msg = (
            f"Buenas noches, {user.name} 🌙\n\n"
            f"Cerramos la jornada. Tenés acumulados: ⭐ *{user.xp_total or 0} XP*.\n\n"
            f"Contame en un mensajito o audio corto qué pudiste liquidar hoy (estudio, entrenamiento o lectura) para computar tus puntos y cerrar la racha. ¡A descansar!"
        )
        await send_whatsapp_message(user.phone, msg)
        logger.info(f"Evening review enviado a {user.phone}")
    except Exception as e:
        logger.error(f"Error en evening review: {e}")
    finally:
        db.close()

def start_scheduler():
    # Revisión cada 60 segundos para no perder ningún bloque de rutina
    scheduler.add_job(
        check_upcoming_routine_blocks,
        trigger=IntervalTrigger(seconds=60),
        id="check_upcoming_routine_blocks",
        replace_existing=True
    )
    scheduler.add_job(
        send_morning_briefing,
        trigger=CronTrigger(hour=8, minute=0, timezone=tz),
        id="send_morning_briefing",
        replace_existing=True
    )
    scheduler.add_job(
        send_evening_review,
        trigger=CronTrigger(hour=22, minute=30, timezone=tz),
        id="send_evening_review",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Scheduler proactivo continuo de ForgeOS iniciado.")