from datetime import datetime, timedelta
import uuid
import pytz
from sqlalchemy.orm import Session
from app.config import settings
from app.models.core import User, DailyBlockInstance, BlockStatus, ActionLog, BlockCategory, CalendarEvent
from app.services.whatsapp import WhatsAppService
from app.services.rescheduler import EngineAI

class EventHandler:
    @classmethod
    async def process_incoming_payload(cls, payload: dict, db: Session):
        try:
            entries = payload.get("entry", [])
            for entry in entries:
                changes = entry.get("changes", [])
                for change in changes:
                    val = change.get("value", {})
                    messages = val.get("messages", [])
                    if not messages:
                        continue

                    msg = messages[0]
                    from_phone = msg.get("from")
                    msg_type = msg.get("type")

                    user = db.query(User).filter(User.phone == from_phone).first()
                    if not user:
                        user = User(phone=from_phone, name="Tobías", is_believer=True)
                        db.add(user)
                        db.commit()
                        db.refresh(user)

                    if msg_type == "interactive":
                        action_id = msg.get("interactive", {}).get("button_reply", {}).get("id", "")
                        await cls.handle_button_action(action_id, user, db)

                    elif msg_type == "text":
                        text_content = msg.get("text", {}).get("body", "").strip()
                        await cls.handle_text_action(text_content, user, db)

                    elif msg_type == "audio":
                        audio_id = msg.get("audio", {}).get("id")
                        if audio_id:
                            audio_bytes = await WhatsAppService.download_audio_bytes(audio_id)
                            transcript = EngineAI.transcribe_audio(audio_bytes)
                            await cls.handle_text_action(transcript, user, db)

        except Exception as e:
            print(f"[ERROR] Error procesando evento de WhatsApp: {e}")

    @classmethod
    async def handle_button_action(cls, action_id: str, user: User, db: Session):
        if not action_id:
            return
        parts = action_id.split("_", 1)
        action_type = parts[0]
        instance_id_str = parts[1] if len(parts) > 1 else ""

        try:
            block = db.query(DailyBlockInstance).filter(DailyBlockInstance.id == uuid.UUID(instance_id_str)).first()
        except Exception:
            block = None

        if action_type == "start":
            if block:
                block.status = BlockStatus.STARTED
                db.commit()
            await WhatsAppService.send_text_message(
                user.phone,
                "💪 ¡Excelente! Bloque iniciado. Al finalizar, mandame un audio o texto breve con lo logrado para validar la racha."
            )

        elif action_type == "postpone":
            if block:
                block.status = BlockStatus.POSTPONED
                block.scheduled_for += timedelta(minutes=30)
                db.commit()
            await WhatsAppService.send_text_message(
                user.phone,
                "⏱️ Bloque pospuesto 30 minutos. En un rato te vuelvo a notificar."
            )

        elif action_type == "exception":
            if block:
                block.status = BlockStatus.EXCEPTION
                db.commit()
            await WhatsAppService.send_text_message(
                user.phone,
                "📝 Entendido. Decime en una frase o audio qué imprevisto tuviste para reorganizar el día."
            )

    @classmethod
    async def handle_text_action(cls, text: str, user: User, db: Session):
        tz = pytz.timezone(settings.TIMEZONE)
        now = datetime.now(tz).replace(tzinfo=None)

        # --- COMANDO PLAYLIST YOUTUBE ---
        clean_msg = text.strip()
        if clean_msg.lower().startswith("playlist ") or clean_msg.lower().startswith("/playlist "):
            parts = clean_msg.split(maxsplit=1)
            if len(parts) > 1:
                new_url = parts[1].strip()
                user.youtube_playlist_url = new_url
                db.add(user)
                db.commit()
                db.refresh(user)
                
                from app.whatsapp_client import send_whatsapp_message
                await send_whatsapp_message(
                    user.phone,
                    f"✅ *Playlist actualizada con éxito.*\n\n🔗 Enlace: {user.youtube_playlist_url}\nYa quedó sincronizado para tus almuerzos."
                )
                return

        # 1. ¿Hay una excepción pendiente de justificar?
        pending_exception = db.query(DailyBlockInstance).filter(
            DailyBlockInstance.user_id == user.id,
            DailyBlockInstance.status == BlockStatus.EXCEPTION,
            DailyBlockInstance.exception_reason == None
        ).order_by(DailyBlockInstance.created_at.desc()).first()

        if pending_exception:
            pending_exception.exception_reason = text
            db.commit()

            remaining = db.query(DailyBlockInstance).filter(
                DailyBlockInstance.user_id == user.id,
                DailyBlockInstance.status == BlockStatus.PENDING,
                DailyBlockInstance.scheduled_for >= now
            ).all()

            data = [{"label": b.label, "category": b.category.value, "time": b.scheduled_for.strftime("%H:%M")} for b in remaining]
            plan = EngineAI.handle_exception_replan(text, data)
            await WhatsAppService.send_text_message(user.phone, plan)
            return

        # 2. Análisis de intención inteligente con Gemini
        analysis = EngineAI.classify_intent_and_extract(text, now.isoformat())
        intent = analysis.get("intent")

        # Caso A: Guardar evento en la agenda
        if intent == "CREATE_EVENT" and analysis.get("event_data"):
            ev = analysis["event_data"]
            try:
                event_date = datetime.fromisoformat(ev["date_iso"]) if ev.get("date_iso") else now
                category_enum = BlockCategory[ev.get("category", "ACADEMIC")]
            except Exception:
                event_date = now
                category_enum = BlockCategory.ACADEMIC

            new_event = CalendarEvent(
                user_id=user.id,
                title=ev.get("title") or text,
                event_date=event_date,
                category=category_enum,
                notes=ev.get("notes")
            )
            db.add(new_event)
            db.commit()

            msg = f"📅 *Agendado con éxito:*\n📌 *{new_event.title}*\n🗓️ {new_event.event_date.strftime('%d/%m/%Y a las %H:%M')}\n📂 Categoría: {new_event.category.value}"
            await WhatsAppService.send_text_message(user.phone, msg)
            return

        # Caso B: Consulta de agenda / parciales
        elif intent == "QUERY_SCHEDULE":
            upcoming_events = db.query(CalendarEvent).filter(
                CalendarEvent.user_id == user.id,
                CalendarEvent.event_date >= now,
                CalendarEvent.is_completed == False
            ).order_by(CalendarEvent.event_date.asc()).all()

            reply = EngineAI.answer_schedule_query(text, upcoming_events, now)
            await WhatsAppService.send_text_message(user.phone, reply)
            return

        # Caso C: Hábito, reflexión o avance diario
        else:
            result = EngineAI.evaluate_reflection(text, category="GENERAL", is_believer=user.is_believer)
            log = ActionLog(
                user_id=user.id,
                category=BlockCategory.ACADEMIC,
                input_text=text,
                ai_feedback=result["feedback"],
                is_validated=True,
                earned_xp=result["xp"]
            )
            user.xp_total += result["xp"]
            db.add(log)
            db.commit()

            msg = f"{result['feedback']}\n\n✨ *+{result['xp']} XP ganados* (Total acumulado: {user.xp_total} XP)"
            await WhatsAppService.send_text_message(user.phone, msg)