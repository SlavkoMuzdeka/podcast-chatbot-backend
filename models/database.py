import os
import uuid

from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy import (
    Text,
    JSON,
    Float,
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    create_engine,
)

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class User(Base):
    """User model for authentication and user management"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    experts = relationship(
        "Expert", back_populates="user", cascade="all, delete-orphan"
    )
    chat_sessions = relationship(
        "ChatSession", back_populates="user", cascade="all, delete-orphan"
    )
    usage_logs = relationship(
        "UsageLog", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"


class Expert(Base):
    """Expert model for custom AI experts created by users"""

    __tablename__ = "experts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    pinecone_namespace = Column(String(100), nullable=False, unique=True)
    system_prompt = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    processing_status = Column(
        String(20), default="pending"
    )  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    user = relationship("User", back_populates="experts")
    episodes = relationship(
        "Episode", back_populates="expert", cascade="all, delete-orphan"
    )
    chat_sessions = relationship("ChatSession", back_populates="expert")

    def __repr__(self):
        return f"<Expert(name='{self.name}', user_id='{self.user_id}')>"


class Episode(Base):
    """Episode model for podcast episodes"""

    __tablename__ = "episodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expert_id = Column(
        UUID(as_uuid=True), ForeignKey("experts.id"), nullable=True
    )  # Null for temporary episodes
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    episode_metadata = Column(
        JSON, nullable=True
    )  # Changed from 'metadata' to 'episode_metadata'
    processing_status = Column(
        String(20), default="pending"
    )  # pending, processing, completed, failed
    processing_error = Column(Text, nullable=True)
    is_temporary = Column(Boolean, default=False)  # True for single episode chats
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    expert = relationship("Expert", back_populates="episodes")

    def __repr__(self):
        return f"<Episode(title='{self.title}', url='{self.url}')>"


class ChatSession(Base):
    """Chat session model for tracking conversations"""

    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    expert_id = Column(
        UUID(as_uuid=True), ForeignKey("experts.id"), nullable=True
    )  # Null for episode chats
    episode_id = Column(
        UUID(as_uuid=True), ForeignKey("episodes.id"), nullable=True
    )  # For single episode chats
    session_type = Column(String(20), nullable=False)  # "expert" or "episode"
    title = Column(String(200), nullable=True)  # Auto-generated or user-defined
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    ended_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    expert = relationship("Expert", back_populates="chat_sessions")
    episode = relationship("Episode")
    messages = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ChatSession(id='{self.id}', type='{self.session_type}')>"


class ChatMessage(Base):
    """Chat message model for storing conversation messages"""

    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False
    )
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    message_metadata = Column(
        JSON, nullable=True
    )  # Changed from 'metadata' to 'message_metadata'
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(role='{self.role}', session_id='{self.session_id}')>"


class UsageLog(Base):
    """Usage log model for tracking API usage and costs"""

    __tablename__ = "usage_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=True
    )
    action_type = Column(
        String(50), nullable=False
    )  # "chat_message", "episode_processing", "expert_creation"
    tokens_used = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)
    processing_time = Column(Float, nullable=True)  # Time in seconds
    log_metadata = Column(
        JSON, nullable=True
    )  # Changed from 'metadata' to 'log_metadata'
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    user = relationship("User", back_populates="usage_logs")
    session = relationship("ChatSession")

    def __repr__(self):
        return f"<UsageLog(action='{self.action_type}', user_id='{self.user_id}')>"


class SystemConfig(Base):
    """System configuration model for storing app settings"""

    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<SystemConfig(key='{self.key}', value='{self.value}')>"


# Create all tables
def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)


if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully!")
