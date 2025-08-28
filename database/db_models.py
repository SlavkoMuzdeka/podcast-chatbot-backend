import uuid

from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
    func,
    Text,
    Column,
    String,
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

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "fullName": self.full_name,
            "totalExperts": len(self.experts),
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
            "createdAt": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updatedAt": self.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        }


class Expert(db.Model):
    """Expert model for custom AI experts created by users"""

    __tablename__ = "experts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
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

    def __repr__(self):
        return f"<Expert(name='{self.name}', user_id='{self.user_id}')>"

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "totalEpisodes": len(self.episodes),
            "createdAt": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updatedAt": self.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
