import logging
from datetime import time
from app.database import SessionLocal
from app.models.core import User, RoutineBlock, SubjectTopic, DayOfWeek, BlockCategory

logger = logging.getLogger("forgeos")

def seed_database():
    db = SessionLocal()
    try:
        # 1. Configuración de Usuario
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
        else:
            user.phone = "541123588856"
            user.is_believer = True
            if not user.youtube_playlist_url:
                user.youtube_playlist_url = "https://youtube.com/playlist?list=PLKvHNyj_vls4&si=MYCTP4NKt7W-oJ40"
            db.commit()

        # 2. Rutina Semanal con Bloques de Estudio Dinámicos
        count_blocks = db.query(RoutineBlock).filter(RoutineBlock.user_id == user.id).count()
        if count_blocks == 0:
            blocks = [
                # --- LUNES (Cursada Mañana + Estudio Tarde + Gym) ---
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.MONDAY, label="Cursada Facultad", start_time=time(8, 0), duration_minutes=240, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.MONDAY, label="Almuerzo & Descanso", start_time=time(13, 0), duration_minutes=60, category=BlockCategory.HOUSEHOLD),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.MONDAY, label="Estudio Foco: Sesión 1", start_time=time(16, 0), duration_minutes=120, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.MONDAY, label="Entrenamiento Gym", start_time=time(18, 30), duration_minutes=90, category=BlockCategory.FITNESS),

                # --- MARTES (Cursada Mañana + Estudio Tarde + Gym) ---
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.TUESDAY, label="Cursada Facultad", start_time=time(8, 0), duration_minutes=240, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.TUESDAY, label="Almuerzo & Descanso", start_time=time(13, 0), duration_minutes=60, category=BlockCategory.HOUSEHOLD),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.TUESDAY, label="Estudio Foco: Sesión 2", start_time=time(16, 0), duration_minutes=120, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.TUESDAY, label="Entrenamiento Gym", start_time=time(18, 30), duration_minutes=90, category=BlockCategory.FITNESS),

                # --- MIÉRCOLES (Estudio Mañana + Gym Mediodía + Cursada Noche) ---
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.WEDNESDAY, label="Estudio Foco Matutino", start_time=time(9, 30), duration_minutes=120, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.WEDNESDAY, label="Entrenamiento Gym", start_time=time(12, 30), duration_minutes=90, category=BlockCategory.FITNESS),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.WEDNESDAY, label="Almuerzo & Recarga", start_time=time(14, 15), duration_minutes=45, category=BlockCategory.HOUSEHOLD),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.WEDNESDAY, label="Cursada Facultad (Noche)", start_time=time(18, 30), duration_minutes=240, category=BlockCategory.ACADEMIC),

                # --- JUEVES (Cursada Mañana + Estudio Tarde + Gym) ---
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.THURSDAY, label="Cursada Facultad", start_time=time(8, 0), duration_minutes=240, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.THURSDAY, label="Almuerzo & Descanso", start_time=time(13, 0), duration_minutes=60, category=BlockCategory.HOUSEHOLD),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.THURSDAY, label="Estudio Foco: Práctica y Ejercicios", start_time=time(16, 0), duration_minutes=120, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.THURSDAY, label="Entrenamiento Gym", start_time=time(18, 30), duration_minutes=90, category=BlockCategory.FITNESS),

                # --- VIERNES (Cursada Mañana + Cierre Semanal) ---
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.FRIDAY, label="Cursada Facultad", start_time=time(8, 0), duration_minutes=240, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.FRIDAY, label="Almuerzo & Descanso", start_time=time(13, 0), duration_minutes=60, category=BlockCategory.HOUSEHOLD),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.FRIDAY, label="Cierre Semanal & Repaso General", start_time=time(16, 0), duration_minutes=90, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.FRIDAY, label="Entrenamiento Gym", start_time=time(18, 0), duration_minutes=90, category=BlockCategory.FITNESS),

                # --- FIN DE SEMANA ---
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.SATURDAY, label="Lectura Formativa & Proyectos", start_time=time(10, 30), duration_minutes=90, category=BlockCategory.READING),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.SUNDAY, label="Día del Señor / Descanso & Familia", start_time=time(10, 0), duration_minutes=180, category=BlockCategory.SPIRITUAL),
            ]
            db.bulk_save_objects(blocks)
            db.commit()
            logger.info("Rutina semanal canónica sembrada.")

    except Exception as e:
        logger.error(f"Error sembrando datos: {e}")
    finally:
        db.close()