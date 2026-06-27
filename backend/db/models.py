from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TaskRecord(Base):
    """Tracks every agent invocation — the source of truth for the dashboard."""

    __tablename__ = "agent_tasks"

    id = Column(String, primary_key=True)
    agent = Column(String, nullable=False)
    status = Column(String, default="queued")
    progress = Column(Integer, default=0)
    message = Column(String, default="")
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
