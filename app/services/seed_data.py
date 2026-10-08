import logging
from datetime import time, datetime
from app.database import SessionLocal
from app.models.core import User, RoutineBlock, SubjectTopic, CalendarEvent, DayOfWeek, BlockCategory

logger = logging.getLogger("forgeos")

def seed_database():
    db = SessionLocal()
    try:
        # 1. Tu Usuario Oficial
        user = db.query(User).first()
        if not user:
            user = User(
                name="Tobías",
                phone="541123588856",
                is_believer=True,
                youtube_playlist_url="https://youtube.com/playlist?list=PLKvHNyj_vls4&si=MYCTP4NKt7W-oJ40",
                xp_total=240,
                streak_days=3
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("Usuario Tobías sembrado con éxito.")
        else:
            # Asegurar datos actualizados
            user.phone = "541123588856"
            user.is_believer = True
            if not user.youtube_playlist_url:
                user.youtube_playlist_url = "https://youtube.com/playlist?list=PLKvHNyj_vls4&si=MYCTP4NKt7W-oJ40"
            db.commit()

        # 2. Rutina Semanal Completa (Si no existen bloques)
        count_blocks = db.query(RoutineBlock).filter(RoutineBlock.user_id == user.id).count()
        if count_blocks == 0:
            blocks = [
                # Lunes a Viernes: Rutina Base
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.MONDAY, label="Cursada Facultad", start_time=time(8, 0), duration_minutes=240, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.MONDAY, label="Almuerzo & Descanso", start_time=time(13, 0), duration_minutes=60, category=BlockCategory.HOUSEHOLD),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.MONDAY, label="Estudio Foco: Física II", start_time=time(16, 0), duration_minutes=120, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.MONDAY, label="Entrenamiento Gym", start_time=time(18, 30), duration_minutes=90, category=BlockCategory.FITNESS),

                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.TUESDAY, label="Cursada Facultad", start_time=time(8, 0), duration_minutes=240, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.TUESDAY, label="Almuerzo & Descanso", start_time=time(13, 0), duration_minutes=60, category=BlockCategory.HOUSEHOLD),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.TUESDAY, label="Estudio Foco: Lenguajes", start_time=time(16, 0), duration_minutes=120, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.TUESDAY, label="Entrenamiento Gym", start_time=time(18, 30), duration_minutes=90, category=BlockCategory.FITNESS),

                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.WEDNESDAY, label="Cursada Facultad", start_time=time(8, 0), duration_minutes=240, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.WEDNESDAY, label="Almuerzo & Descanso", start_time=time(13, 0), duration_minutes=60, category=BlockCategory.HOUSEHOLD),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.WEDNESDAY, label="Práctica de Problemas Física II", start_time=time(16, 0), duration_minutes=120, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.WEDNESDAY, label="Entrenamiento Gym", start_time=time(18, 30), duration_minutes=90, category=BlockCategory.FITNESS),

                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.THURSDAY, label="Cursada Facultad", start_time=time(8, 0), duration_minutes=240, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.THURSDAY, label="Almuerzo & Descanso", start_time=time(13, 0), duration_minutes=60, category=BlockCategory.HOUSEHOLD),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.THURSDAY, label="Repaso Autómatas y Gramáticas", start_time=time(16, 0), duration_minutes=120, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.THURSDAY, label="Entrenamiento Gym", start_time=time(18, 30), duration_minutes=90, category=BlockCategory.FITNESS),

                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.FRIDAY, label="Cursada Facultad", start_time=time(8, 0), duration_minutes=240, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.FRIDAY, label="Almuerzo & Descanso", start_time=time(13, 0), duration_minutes=60, category=BlockCategory.HOUSEHOLD),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.FRIDAY, label="Cierre Semanal & Repaso", start_time=time(16, 0), duration_minutes=90, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.FRIDAY, label="Entrenamiento Gym", start_time=time(18, 0), duration_minutes=90, category=BlockCategory.FITNESS),

                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.SATURDAY, label="Lectura formativa & Proyectos", start_time=time(10, 30), duration_minutes=90, category=BlockCategory.READING),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.SUNDAY, label="Día del Señor / Descanso & Familia", start_time=time(10, 0), duration_minutes=180, category=BlockCategory.SPIRITUAL),
            ]
            db.bulk_save_objects(blocks)
            db.commit()
            logger.info("Bloques de rutina sembrados.")

        # 3. Temas de Materias (Syllabus)
        count_topics = db.query(SubjectTopic).filter(SubjectTopic.user_id == user.id).count()
        if count_topics == 0:
            topics = [
                SubjectTopic(user_id=user.id, subject_name="Física II", unit_number=1, title="Campos Eléctricos y Ley de Gauss", estimated_hours=8.0, is_completed=True),
                SubjectTopic(user_id=user.id, subject_name="Física II", unit_number=2, title="Potencial Eléctrico y Capacidad", estimated_hours=6.0, is_completed=True),
                SubjectTopic(user_id=user.id, subject_name="Física II", unit_number=3, title="Corriente, Resistencia y Circuitos CC", estimated_hours=8.0, is_completed=False),
                SubjectTopic(user_id=user.id, subject_name="Física II", unit_number=4, title="Campo Magnético y Fuerzas Magnéticas", estimated_hours=10.0, is_completed=False),
                SubjectTopic(user_id=user.id, subject_name="Física II", unit_number=5, title="Inducción Electromagnética y Ley de Faraday", estimated_hours=8.0, is_completed=False),

                SubjectTopic(user_id=user.id, subject_name="Teoría de Lenguajes", unit_number=1, title="Alfabetos, Lenguajes y Expresiones Regulares", estimated_hours=6.0, is_completed=True),
                SubjectTopic(user_id=user.id, subject_name="Teoría de Lenguajes", unit_number=2, title="Autómatas Finitos Deterministas y No Deterministas", estimated_hours=8.0, is_completed=False),
                SubjectTopic(user_id=user.id, subject_name="Teoría de Lenguajes", unit_number=3, title="Gramáticas Regulares y Libres de Contexto", estimated_hours=10.0, is_completed=False),
                SubjectTopic(user_id=user.id, subject_name="Teoría de Lenguajes", unit_number=4, title="Autómatas de Pila y Jerarquía de Chomsky", estimated_hours=8.0, is_completed=False),
            ]
            db.bulk_save_objects(topics)
            db.commit()
            logger.info("Temas de materias sembrados.")

    except Exception as e:
        logger.error(f"Error sembrando datos: {e}")
    finally:
        db.close()