from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from backend.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def new_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=new_uuid)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(256), unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String(32), default="user")  # admin | user | readonly
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    sessions = relationship("ChatSession", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=new_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    title = Column(String(256), default="New Chat")
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=new_uuid)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(16), nullable=False)        # user | assistant | system
    content = Column(Text, nullable=False)
    model_used = Column(String(128), nullable=True)
    provider = Column(String(64), nullable=True)     # openai | anthropic | gemini | ollama
    tokens_in = Column(Integer, default=0)
    tokens_out = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    cost_usd = Column(Float, default=0.0)
    attempt = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    metadata_ = Column("metadata", JSON, default=dict)

    session = relationship("ChatSession", back_populates="messages")
    feedback = relationship("Feedback", back_populates="message", uselist=False)


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(String, primary_key=True, default=new_uuid)
    message_id = Column(String, ForeignKey("messages.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    rating = Column(Integer, nullable=False)         # 1-5
    tags = Column(JSON, default=list)                # ["too_long", "wrong", "helpful"]
    comment = Column(Text, nullable=True)
    triggered_retry = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    message = relationship("Message", back_populates="feedback")
    user = relationship("User", back_populates="feedbacks")


class ModelPerformance(Base):
    __tablename__ = "model_performance"

    id = Column(String, primary_key=True, default=new_uuid)
    provider = Column(String(64), nullable=False)
    model = Column(String(128), nullable=False)
    query_type = Column(String(128), default="general")
    avg_rating = Column(Float, default=3.0)
    total_queries = Column(Integer, default=0)
    avg_latency_ms = Column(Float, default=0.0)
    avg_cost_usd = Column(Float, default=0.0)
    success_rate = Column(Float, default=1.0)
    weight = Column(Float, default=1.0)              # adaptive routing weight
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=new_uuid)
    event_type = Column(String(64), nullable=False)
    user_id = Column(String, nullable=True)
    ip_address = Column(String(64), nullable=True)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    id = Column(String, primary_key=True, default=new_uuid)
    user_id = Column(String, nullable=True)
    key = Column(String(256), nullable=False)
    value = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    source = Column(String(64), default="manual")   # manual | auto | feedback
    embedding_id = Column(String, nullable=True)    # Chroma doc ID
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
