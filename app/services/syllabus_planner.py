import logging
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.core import User, CalendarEvent, SubjectTopic, RoutineBlock

logger = logging.getLogger("forgeos")

class SyllabusPlanner:
    @staticmethod
    def calculate_study_roadmap(user_id, subject_name: str = "Física II"):
        """
        Calcula días restantes hasta el parcial, balancea horas totales necesarias 
        vs bloques semanales disponibles y genera un desglose de horas por tema.
        """
        db = SessionLocal()
        try:
            now = datetime.now()
            
            # 1. Buscar parcial de la materia
            exam = db.query(CalendarEvent).filter(
                CalendarEvent.user_id == user_id,
                CalendarEvent.title.ilike(f"%{subject_name}%"),
                CalendarEvent.event_date >= now
            ).order_by(CalendarEvent.event_date).first()

            # 2. Buscar temas de la materia
            topics = db.query(SubjectTopic).filter(
                SubjectTopic.user_id == user_id,
                SubjectTopic.subject_name.ilike(f"%{subject_name}%")
            ).order_by(SubjectTopic.unit_number).all()

            if not exam:
                days_left = 30  # Default si no hay fecha cargada aún
                exam_date_str = "A definir"
            else:
                days_left = max((exam.event_date.date() - now.date()).days, 1)
                exam_date_str = exam.event_date.strftime("%d/%m/%Y")

            total_hours_needed = sum(max(t.estimated_hours - t.completed_hours, 0) for t in topics)
            weeks_left = max(days_left / 7.0, 1.0)
            hours_per_week_target = round(total_hours_needed / weeks_left, 1) if total_hours_needed > 0 else 0

            # 3. Asignación de semanas y cuotas de horas por unidad
            breakdown = []
            cum_hours = 0
            for t in topics:
                pending_h = max(t.estimated_hours - t.completed_hours, 0)
                assigned_week = int(cum_hours / max(hours_per_week_target, 1)) + 1 if hours_per_week_target > 0 else 1
                cum_hours += pending_h
                breakdown.append({
                    "unit": t.unit_number,
                    "title": t.title,
                    "estimated_hours": t.estimated_hours,
                    "completed_hours": t.completed_hours,
                    "pending_hours": pending_h,
                    "target_week": f"Semana {assigned_week}",
                    "is_completed": t.is_completed
                })

            return {
                "subject": subject_name,
                "exam_date": exam_date_str,
                "days_left": days_left,
                "weeks_left": round(weeks_left, 1),
                "total_hours_needed": total_hours_needed,
                "hours_per_week_target": hours_per_week_target,
                "topics": breakdown
            }
        finally:
            db.close()

    @staticmethod
    def get_roadmap_summary_text(user_id, subject_name: str = "Física II") -> str:
        data = SyllabusPlanner.calculate_study_roadmap(user_id, subject_name)
        if not data["topics"]:
            return f"No tenés temas cargados todavía para *{subject_name}*. Cargalos con: 'Cargar tema: Unidad 1 - Electrostática (12h)'."

        lines = [
            f"📊 *Estrategia de Estudio - {data['subject']}*",
            f"📅 Parcial: *{data['exam_date']}* (Quedan {data['days_left']} días / ~{data['weeks_left']} semanas)",
            f"⏱️ Horas totales pendientes: *{data['total_hours_needed']} hs*",
            f"🎯 Ritmo recomendado: *{data['hours_per_week_target']} hs/semana*\n",
            "📌 *Distribución por Unidades:*"
        ]

        for t in data["topics"]:
            status = "✅" if t["is_completed"] else f"⏳ {t['pending_hours']}h rest."
            lines.append(f"• *U{t['unit']}: {t['title']}* → {status} ({t['target_week']})")

        return "\n".join(lines)