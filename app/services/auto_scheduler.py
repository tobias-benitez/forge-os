from datetime import datetime, date, time
from app.database import SessionLocal
from app.models.core import RoutineBlock, CalendarEvent, DayOfWeek, BlockCategory

DIFFICULTY_MAP = {
    "Física II": 9.5,
    "Programación II": 9.0,
    "Teoría de Lenguajes": 8.0,
    "Sistemas de Información 1": 5.0,
    "Administración de Empresas": 4.5,
    "Cálculo Numérico": 4.0
}

def recalculate_weekly_blocks(user_id: int):
    """Calcula y reorganiza los bloques de estudio de la semana según fechas de exámenes."""
    db = SessionLocal()
    try:
        today = date.today()
        upcoming_exams = (
            db.query(CalendarEvent)
            .filter(
                CalendarEvent.user_id == user_id,
                CalendarEvent.category == BlockCategory.ACADEMIC,
                CalendarEvent.event_date >= datetime.combine(today, time.min)
            )
            .order_by(CalendarEvent.event_date.asc())
            .all()
        )

        exam_urgency = {}
        for ex in upcoming_exams:
            days = max(1, (ex.event_date.date() - today).days)
            name = ex.title.replace("Parcial ", "").replace("[", "").replace("]", "").strip()
            base_diff = 5.0
            for k, v in DIFFICULTY_MAP.items():
                if k.lower() in name.lower():
                    base_diff = v
                    break
            exam_urgency[name] = (base_diff * 10) / days

        # Materia de mayor emergencia (si no hay fechas cargadas, foco en Lenguajes/Física)
        primary = max(exam_urgency, key=exam_urgency.get) if exam_urgency else "Teoría de Lenguajes"

        # Ventanas libres estratégicas (Martes M, Miércoles M, Jueves T, Viernes T, Sábado S)
        study_slots = [
            (DayOfWeek.TUESDAY, time(9, 30), 180, f"Bloque Foco // {primary}"),
            (DayOfWeek.WEDNESDAY, time(9, 30), 180, "Bloque Foco // Física II"),
            (DayOfWeek.THURSDAY, time(17, 30), 120, "Bloque Foco // Programación II (Recuperatorio)"),
            (DayOfWeek.FRIDAY, time(15, 0), 120, f"Bloque Refuerzo // {primary}"),
            (DayOfWeek.SATURDAY, time(14, 0), 90, "Bloque Entregable // Sistemas de Información (Diagrama)")
        ]

        # Borrar solo los bloques de estudio dinámicos anteriores (mantiene cursadas, gym y voluntariado)
        db.query(RoutineBlock).filter(
            RoutineBlock.user_id == user_id,
            RoutineBlock.label.like("Bloque %")
        ).delete(synchronize_session=False)

        for dow, t_start, dur, lbl in study_slots:
            b = RoutineBlock(
                user_id=user_id,
                day_of_week=dow,
                start_time=t_start,
                duration_minutes=dur,
                category=BlockCategory.ACADEMIC,
                label=lbl
            )
            db.add(b)

        db.commit()
    finally:
        db.close()
