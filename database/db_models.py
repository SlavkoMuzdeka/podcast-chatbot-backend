import uuid

from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
    func,
    Text,
    JSON,
    Float,
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
)

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication and user management"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )
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

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "fullName": self.full_name,
            "isActive": self.is_active,
            "totalExperts": len(self.experts),
            "totalChatSessions": len(self.chat_sessions),
            "totalUsageLogs": len(self.usage_logs),
        }


class Episode(db.Model):
    """Episode model for podcast episodes"""

    __tablename__ = "episodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expert_id = Column(UUID(as_uuid=True), ForeignKey("experts.id"))
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    expert = relationship("Expert", back_populates="episodes")

    def __repr__(self):
        return f"<Episode(title='{self.title}')>"

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "expertName": self.expert.name,
            "title": self.title,
            "content": self.content,
        }


class Expert(db.Model):
    """Expert model for custom AI experts created by users"""

    __tablename__ = "experts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = relationship("User", back_populates="experts")
    episodes = relationship(
        "Episode", back_populates="expert", cascade="all, delete-orphan"
    )
    chat_sessions = relationship("ChatSession", back_populates="expert")

    def __repr__(self):
        return f"<Expert(name='{self.name}', user_id='{self.user_id}')>"

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "userEmail": self.user.email,
            "name": self.name,
            "description": self.description,
            "totalEpisodes": len(self.episodes),
            "totalChatSessions": len(self.chat_sessions),
        }


class ChatSession(db.Model):
    """Chat session model for tracking conversations"""

    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    expert_id = Column(UUID(as_uuid=True), ForeignKey("experts.id"), nullable=True)
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"), nullable=True)
    session_type = Column(String(20), nullable=False)  # "expert" or "episode"
    title = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    expert = relationship("Expert", back_populates="chat_sessions")
    episode = relationship("Episode")
    messages = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ChatSession(id='{self.id}', type='{self.session_type}')>"

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "userEmail": self.user.email,
            "expertName": self.expert.name,
            "episodeName": self.episode.title if self.episode else None,
            "sessionType": self.session_type,
            "title": self.title,
            "isActive": self.is_active,
        }


class ChatMessage(db.Model):
    """Chat message model for storing conversation messages"""

    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False
    )
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(role='{self.role}', session_id='{self.session_id}')>"

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "sessionId": str(self.session_id),
            "role": self.role,
            "content": self.content,
            "messageMetadata": self.message_metadata,
            "createdAt": self.created_at,
        }


class UsageLog(db.Model):
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
    log_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="usage_logs")
    session = relationship("ChatSession")

    def __repr__(self):
        return f"<UsageLog(action='{self.action_type}', user_id='{self.user_id}')>"

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "userEmail": self.user.email,
            "sessionId": str(self.session_id),
            "actionType": self.action_type,
            "tokensUsed": self.tokens_used,
            "cost": self.cost,
            "processingTime": self.processing_time,
            "logMetadata": self.log_metadata,
            "createdAt": self.created_at,
        }
