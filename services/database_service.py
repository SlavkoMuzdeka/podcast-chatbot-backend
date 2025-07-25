import logging

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Dict, Any
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import (
    get_db,
    User,
    Expert,
    Episode,
    UsageLog,
    ChatSession,
    ChatMessage,
    SystemConfig,
)

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service layer for database operations"""

    def __init__(self):
        self.db = None

    def get_session(self) -> Session:
        """Get database session"""
        if not self.db:
            self.db = next(get_db())
        return self.db

    def close_session(self):
        """Close database session"""
        if self.db:
            self.db.close()
            self.db = None

    # User operations
    def create_user(
        self, username: str, password: str, email: str = None, full_name: str = None
    ) -> Optional[User]:
        """Create a new user"""
        try:
            db = self.get_session()

            # Check if user already exists
            existing_user = (
                db.query(User)
                .filter(or_(User.username == username, User.email == email))
                .first()
            )

            if existing_user:
                return None

            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                full_name=full_name,
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            logger.info(f"Created user: {username}")
            return user

        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            db.rollback()
            return None

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        try:
            db = self.get_session()
            user = db.query(User).filter(User.username == username).first()

            if user and check_password_hash(user.password_hash, password):
                # Update last login
                user.last_login = datetime.now()
                db.commit()
                return user

            return None

        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            db = self.get_session()
            return db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            return None

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            db = self.get_session()
            return db.query(User).filter(User.username == username).first()
        except Exception as e:
            logger.error(f"Error getting user by username: {str(e)}")
            return None

    # Expert operations
    def create_expert(
        self, user_id: str, name: str, description: str, pinecone_namespace: str
    ) -> Optional[Expert]:
        """Create a new expert"""
        try:
            db = self.get_session()

            expert = Expert(
                user_id=user_id,
                name=name,
                description=description,
                pinecone_namespace=pinecone_namespace,
            )

            db.add(expert)
            db.commit()
            db.refresh(expert)

            logger.info(f"Created expert: {name} for user {user_id}")
            return expert

        except Exception as e:
            logger.error(f"Error creating expert: {str(e)}")
            db.rollback()
            return None

    def get_user_experts(self, user_id: str) -> List[Expert]:
        """Get all experts for a user"""
        try:
            db = self.get_session()
            return (
                db.query(Expert)
                .filter(and_(Expert.user_id == user_id, Expert.is_active == True))
                .order_by(desc(Expert.created_at))
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting user experts: {str(e)}")
            return []

    def get_expert_by_id(self, expert_id: str) -> Optional[Expert]:
        """Get expert by ID"""
        try:
            db = self.get_session()
            return db.query(Expert).filter(Expert.id == expert_id).first()
        except Exception as e:
            logger.error(f"Error getting expert by ID: {str(e)}")
            return None

    def update_expert(self, expert_id: str, **kwargs) -> Optional[Expert]:
        """Update expert"""
        try:
            db = self.get_session()
            expert = db.query(Expert).filter(Expert.id == expert_id).first()

            if not expert:
                return None

            for key, value in kwargs.items():
                if hasattr(expert, key):
                    setattr(expert, key, value)

            expert.updated_at = datetime.now()
            db.commit()
            db.refresh(expert)

            logger.info(f"Updated expert: {expert_id}")
            return expert

        except Exception as e:
            logger.error(f"Error updating expert: {str(e)}")
            db.rollback()
            return None

    def delete_expert(self, expert_id: str, user_id: str) -> bool:
        """Delete expert (soft delete)"""
        try:
            db = self.get_session()
            expert = (
                db.query(Expert)
                .filter(and_(Expert.id == expert_id, Expert.user_id == user_id))
                .first()
            )

            if not expert:
                return False

            expert.is_active = False
            expert.updated_at = datetime.now()
            db.commit()

            logger.info(f"Deleted expert: {expert_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting expert: {str(e)}")
            db.rollback()
            return False

    # Episode operations
    def create_episode(
        self, expert_id: str, title: str, url: str, is_temporary: bool = False
    ) -> Optional[Episode]:
        """Create a new episode"""
        try:
            db = self.get_session()

            episode = Episode(
                expert_id=expert_id if not is_temporary else None,
                title=title,
                url=url,
                is_temporary=is_temporary,
            )

            db.add(episode)
            db.commit()
            db.refresh(episode)

            logger.info(f"Created episode: {title}")
            return episode

        except Exception as e:
            logger.error(f"Error creating episode: {str(e)}")
            db.rollback()
            return None

    def get_expert_episodes(self, expert_id: str) -> List[Episode]:
        """Get all episodes for an expert"""
        try:
            db = self.get_session()
            return db.query(Episode).filter(Episode.expert_id == expert_id).all()
        except Exception as e:
            logger.error(f"Error getting expert episodes: {str(e)}")
            return []

    def get_episode_by_id(self, episode_id: str) -> Optional[Episode]:
        """Get episode by ID"""
        try:
            db = self.get_session()
            return db.query(Episode).filter(Episode.id == episode_id).first()
        except Exception as e:
            logger.error(f"Error getting episode by ID: {str(e)}")
            return None

    def update_episode(self, episode_id: str, **kwargs) -> Optional[Episode]:
        """Update episode"""
        try:
            db = self.get_session()
            episode = db.query(Episode).filter(Episode.id == episode_id).first()

            if not episode:
                return None

            for key, value in kwargs.items():
                if hasattr(episode, key):
                    setattr(episode, key, value)

            episode.updated_at = datetime.now()
            db.commit()
            db.refresh(episode)

            return episode

        except Exception as e:
            logger.error(f"Error updating episode: {str(e)}")
            db.rollback()
            return None

    # Chat session operations
    def create_chat_session(
        self,
        user_id: str,
        session_type: str,
        expert_id: str = None,
        episode_id: str = None,
    ) -> Optional[ChatSession]:
        """Create a new chat session"""
        try:
            db = self.get_session()

            session = ChatSession(
                user_id=user_id,
                session_type=session_type,
                expert_id=expert_id,
                episode_id=episode_id,
            )

            db.add(session)
            db.commit()
            db.refresh(session)

            logger.info(f"Created chat session: {session.id}")
            return session

        except Exception as e:
            logger.error(f"Error creating chat session: {str(e)}")
            db.rollback()
            return None

    def get_chat_session(self, session_id: str) -> Optional[ChatSession]:
        """Get chat session by ID"""
        try:
            db = self.get_session()
            return db.query(ChatSession).filter(ChatSession.id == session_id).first()
        except Exception as e:
            logger.error(f"Error getting chat session: {str(e)}")
            return None

    def get_user_chat_sessions(
        self, user_id: str, limit: int = 50
    ) -> List[ChatSession]:
        """Get user's chat sessions"""
        try:
            db = self.get_session()
            return (
                db.query(ChatSession)
                .filter(ChatSession.user_id == user_id)
                .order_by(desc(ChatSession.updated_at))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting user chat sessions: {str(e)}")
            return []

    def add_chat_message(
        self,
        session_id: str,
        role: str,
        content: str,
        message_metadata: Dict[str, Any] = None,
    ) -> Optional[ChatMessage]:
        """Add message to chat session"""
        try:
            db = self.get_session()

            message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                message_metadata=message_metadata,  # Updated column name
            )

            db.add(message)

            # Update session timestamp
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                session.updated_at = datetime.now()

            db.commit()
            db.refresh(message)

            return message

        except Exception as e:
            logger.error(f"Error adding chat message: {str(e)}")
            db.rollback()
            return None

    def get_chat_messages(self, session_id: str) -> List[ChatMessage]:
        """Get all messages for a chat session"""
        try:
            db = self.get_session()
            return (
                db.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at)
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting chat messages: {str(e)}")
            return []

    # Usage logging
    def log_usage(
        self,
        user_id: str,
        action_type: str,
        session_id: str = None,
        tokens_used: int = None,
        cost: float = None,
        processing_time: float = None,
        metadata: Dict[str, Any] = None,
    ) -> Optional[UsageLog]:
        """Log usage for analytics and billing"""
        try:
            db = self.get_session()

            usage_log = UsageLog(
                user_id=user_id,
                session_id=session_id,
                action_type=action_type,
                tokens_used=tokens_used,
                cost=cost,
                processing_time=processing_time,
                log_metadata=metadata,  # Updated column name
            )

            db.add(usage_log)
            db.commit()
            db.refresh(usage_log)

            return usage_log

        except Exception as e:
            logger.error(f"Error logging usage: {str(e)}")
            db.rollback()
            return None

    # System configuration
    def get_config(self, key: str) -> Optional[str]:
        """Get system configuration value"""
        try:
            db = self.get_session()
            config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            return config.value if config else None
        except Exception as e:
            logger.error(f"Error getting config: {str(e)}")
            return None

    def set_config(self, key: str, value: str, description: str = None) -> bool:
        """Set system configuration value"""
        try:
            db = self.get_session()
            config = db.query(SystemConfig).filter(SystemConfig.key == key).first()

            if config:
                config.value = value
                config.updated_at = datetime.now()
                if description:
                    config.description = description
            else:
                config = SystemConfig(key=key, value=value, description=description)
                db.add(config)

            db.commit()
            return True

        except Exception as e:
            logger.error(f"Error setting config: {str(e)}")
            db.rollback()
            return False


# Global database service instance
db_service = DatabaseService()
