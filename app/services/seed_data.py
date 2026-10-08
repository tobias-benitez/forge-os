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

        # 2. Rutina Semanal Real y Optimizada
        count_blocks = db.query(RoutineBlock).filter(RoutineBlock.user_id == user.id).count()
        if count_blocks == 0:
            blocks = [
                # --- LUNES (Programación II + Admin. Empresas) ---
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.MONDAY, label="Cursada: Programación II", start_time=time(8, 0), duration_minutes=240, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.MONDAY, label="Almuerzo & Recarga", start_time=time(13, 0), duration_minutes=60, category=BlockCategory.HOUSEHOLD),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.MONDAY, label="Estudio Dinámico / Repaso Parciales", start_time=time(15, 0), duration_minutes=120, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.MONDAY, label="Cursada: Admin. de Empresas", start_time=time(18, 30), duration_minutes=150, category=BlockCategory.ACADEMIC),

                # --- MARTES (Estudio Matutino + Gym + Sistemas de Info I) ---
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.TUESDAY, label="Estudio Foco: Curso SQL / Proyecto", start_time=time(9, 30), duration_minutes=120, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.TUESDAY, label="Almuerzo Pre-Entreno", start_time=time(12, 0), duration_minutes=30, category=BlockCategory.HOUSEHOLD),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.TUESDAY, label="Entrenamiento Gym", start_time=time(12, 30), duration_minutes=90, category=BlockCategory.FITNESS),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.TUESDAY, label="Cursada: Sistemas de Información I", start_time=time(18, 30), duration_minutes=150, category=BlockCategory.ACADEMIC),

                # --- MIÉRCOLES (Estudio Matutino + Voluntariado + Cálculo Numérico) ---
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.WEDNESDAY, label="Estudio Foco Matutino", start_time=time(9, 30), duration_minutes=120, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.WEDNESDAY, label="Almuerzo Rápido", start_time=time(13, 0), duration_minutes=45, category=BlockCategory.HOUSEHOLD),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.WEDNESDAY, label="Voluntariado", start_time=time(14, 0), duration_minutes=120, category=BlockCategory.SPIRITUAL),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.WEDNESDAY, label="Cursada: Cálculo Numérico", start_time=time(18, 30), duration_minutes=150, category=BlockCategory.ACADEMIC),

                # --- JUEVES (EDyA + Gym Tarde + Repaso) ---
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.THURSDAY, label="Cursada: Estructuras de Datos y Algoritmos", start_time=time(8, 0), duration_minutes=240, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.THURSDAY, label="Almuerzo & Descanso", start_time=time(13, 0), duration_minutes=60, category=BlockCategory.HOUSEHOLD),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.THURSDAY, label="Entrenamiento Gym", start_time=time(15, 0), duration_minutes=90, category=BlockCategory.FITNESS),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.THURSDAY, label="Práctica EDyA / Proyectos", start_time=time(17, 30), duration_minutes=90, category=BlockCategory.ACADEMIC),

                # --- VIERNES (Física II + Bloque Élite de Estudio) ---
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.FRIDAY, label="Cursada: Física II", start_time=time(8, 0), duration_minutes=240, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.FRIDAY, label="Almuerzo & Desconexión", start_time=time(13, 0), duration_minutes=60, category=BlockCategory.HOUSEHOLD),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.FRIDAY, label="Bloque Élite: Avance Máximo (Física II / SQL)", start_time=time(15, 0), duration_minutes=180, category=BlockCategory.ACADEMIC),

                # --- SÁBADO (Cursada + Descanso + Gym Tarde) ---
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.SATURDAY, label="Cursada Facultad", start_time=time(8, 0), duration_minutes=240, category=BlockCategory.ACADEMIC),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.SATURDAY, label="Almuerzo & Descanso", start_time=time(13, 0), duration_minutes=120, category=BlockCategory.HOUSEHOLD),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.SATURDAY, label="Entrenamiento Gym", start_time=time(16, 30), duration_minutes=90, category=BlockCategory.FITNESS),

                # --- DOMINGO (Oración, Lectura y Preparación) ---
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.SUNDAY, label="Misa / Día del Señor & Familia", start_time=time(10, 0), duration_minutes=180, category=BlockCategory.SPIRITUAL),
                RoutineBlock(user_id=user.id, day_of_week=DayOfWeek.SUNDAY, label="Planificación Semanal & Lectura", start_time=time(18, 0), duration_minutes=90, category=BlockCategory.READING),
            ]
            db.bulk_save_objects(blocks)
            db.commit()
            logger.info("Rutina semanal real sembrada.")

    except Exception as e:
        logger.error(f"Error sembrando datos: {e}")
    finally:
        db.close()