from sqlalchemy import Column, String, Integer, Text, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class TaskRecord(Base):
    """Tracks every agent invocation — the source of truth for the dashboard."""

    __tablename__ = "agent_tasks"

    id = Column(String, primary_key=True)           # UUID
    agent = Column(String, nullable=False)           # hunt | analyze | score | tailor | cover_letter | interview
    status = Column(String, default="queued")        # queued | running | done | failed
    progress = Column(Integer, default=0)            # 0-100
    message = Column(String, default="")
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
