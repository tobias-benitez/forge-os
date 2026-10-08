import enum
import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, ForeignKey, Enum, Text, Time
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class BlockCategory(str, enum.Enum):
    ACADEMIC = "ACADEMIC"
    UPSKILLING = "UPSKILLING"
    HOUSEHOLD = "HOUSEHOLD"
    FITNESS = "FITNESS"
    SPIRITUAL = "SPIRITUAL"
    READING = "READING"
    LEISURE = "LEISURE"

class DayOfWeek(str, enum.Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), default="Tobías")
    xp_total = Column(Integer, default=0)
    streak_days = Column(Integer, default=1)
    is_believer = Column(Boolean, default=True)
    focus_area = Column(String(100), default="Ingeniería / Desarrollo & Vida Integral")
    youtube_playlist_url = Column(String(300), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class DailyCheckin(Base):
    __tablename__ = "daily_checkins"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    checkin_date = Column(Date, default=date.today)
    prayer_done = Column(Boolean, default=False)
    reading_done = Column(Boolean, default=False)
    current_book_chapter = Column(String(200), default="Capítulo 1: No critiques, no condenes ni te quejes")
    current_book_page = Column(Integer, default=24)
    nutrition_score = Column(Integer, default=0)
    nutrition_notes = Column(Text, nullable=True)
    mindful_eating = Column(Boolean, default=False)
    gratitude_done = Column(Boolean, default=False)
    gratitude_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class RoutineBlock(Base):
    __tablename__ = "routine_blocks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    day_of_week = Column(Enum(DayOfWeek), nullable=False)
    start_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    category = Column(Enum(BlockCategory), nullable=False)
    label = Column(String(200), nullable=False)

class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    event_date = Column(DateTime, nullable=False)
    category = Column(Enum(BlockCategory), default=BlockCategory.ACADEMIC)
    notes = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ActionLog(Base):
    __tablename__ = "action_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    category = Column(Enum(BlockCategory), nullable=False)
    input_text = Column(Text, nullable=False)
    ai_feedback = Column(Text, nullable=False)
    is_validated = Column(Boolean, default=True)
    earned_xp = Column(Integer, default=30)
    created_at = Column(DateTime, default=datetime.utcnow)

class SubjectTopic(Base):
    __tablename__ = "subject_topics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    subject_name = Column(String(100), nullable=False)
    unit_number = Column(Integer, default=1)
    title = Column(String(200), nullable=False)
    estimated_hours = Column(Float, default=10.0)
    completed_hours = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)
    target_week = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)