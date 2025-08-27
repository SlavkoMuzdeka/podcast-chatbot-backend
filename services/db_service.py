import logging

from sqlalchemy import and_, or_, desc
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from werkzeug.security import generate_password_hash
from database.db_models import (
    User,
    Expert,
    Episode,
    UsageLog,
)

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service layer for database operations"""

    def __init__(self, db):
        self.db = db

    ########
    # USER #
    ########
    def create_user(
        self, username: str, password: str, email: str = None, full_name: str = None
    ) -> Optional[User]:
        """Create a new user"""
        try:
            # Check if user already exists
            existing_user = (
                self.db.session.query(User)
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

            self.db.session.add(user)
            self.db.session.commit()
            self.db.session.refresh(user)

            logger.info(f"Created user: {user.email}")
            return user

        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            self.db.session.rollback()
            return None

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            return self.db.session.query(User).filter(User.username == username).first()
        except Exception as e:
            logger.error(f"Error getting user by username: {str(e)}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            return User.query.get(user_id)
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            return None

    ##########
    # EXPERT #
    ##########
    def create_expert(
        self, user_id: str, expert_name: str, expert_description: str
    ) -> Optional[Expert]:
        """Create a new expert"""
        try:
            expert = Expert(
                user_id=user_id,
                name=expert_name,
                description=expert_description,
            )

            self.db.session.add(expert)
            self.db.session.commit()
            self.db.session.refresh(expert)

            logger.info(
                f"Created expert '{expert.name}' for user '{expert.user.email}'"
            )
            return expert
        except IntegrityError:
            logger.error(
                f"Error creating expert: Expert with name: '{expert_name}' already exists"
            )
            self.db.session.rollback()
            return None
        except Exception as e:
            logger.error(f"Error creating expert: {str(e)}")
            self.db.session.rollback()
            return None

    def get_user_experts(self, user_id: str) -> List[Expert]:
        """Get all experts for a user"""
        try:
            return (
                self.db.session.query(Expert)
                .filter(Expert.user_id == user_id)
                .order_by(desc(Expert.created_at))
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting user experts: {str(e)}")
            return []

    def get_expert_by_id(self, expert_id: str) -> Optional[Expert]:
        """Get expert by ID"""
        try:
            return Expert.query.get(expert_id)
        except Exception as e:
            logger.error(f"Error getting expert by ID: {str(e)}")
            return None

    def update_expert(self, expert_id: str, **kwargs) -> Optional[Expert]:
        """Update expert"""
        try:
            expert = self.get_expert_by_id(expert_id)

            if not expert:
                return None

            for key, value in kwargs.items():
                if hasattr(expert, key):
                    setattr(expert, key, value)

            expert.updated_at = datetime.now(timezone.utc)
            self.db.session.commit()
            self.db.session.refresh(expert)

            logger.info(f"Updated expert: {expert.name}")
            return expert

        except Exception as e:
            logger.error(f"Error updating expert: {str(e)}")
            self.db.session.rollback()
            return None

    def delete_expert(self, expert_id: str, user_id: str) -> bool:
        """Delete expert (soft delete)"""
        try:
            expert = (
                self.db.session.query(Expert)
                .filter(and_(Expert.id == expert_id, Expert.user_id == user_id))
                .first()
            )

            if not expert:
                return False

            self.db.session.delete(expert)
            self.db.session.commit()

            logger.info(f"Deleted expert: {expert.name}")
            return True

        except Exception as e:
            logger.error(f"Error deleting expert: {str(e)}")
            self.db.session.rollback()
            return False

    ###########
    # EPISODE #
    ###########
    def create_episode(
        self, expert_id: str, title: str, content: str
    ) -> Optional[Episode]:
        """Create a new episode"""
        try:
            episode = Episode(expert_id=expert_id, title=title, content=content)

            self.db.session.add(episode)
            self.db.session.commit()
            self.db.session.refresh(episode)

            logger.info(
                f"Created episode '{episode.title}' for expert '{episode.expert.name}'"
            )
            return episode

        except Exception as e:
            logger.error(f"Error creating episode: {str(e)}")
            self.db.session.rollback()
            return None

    def get_episodes(self, expert_id: str) -> List[Episode]:
        """Get all episodes for an expert"""
        try:
            return (
                self.db.session.query(Episode)
                .filter(Episode.expert_id == expert_id)
                .order_by(desc(Episode.created_at))
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting expert episodes: {str(e)}")
            return []

    def get_episode_by_id(self, episode_id: str) -> Optional[Episode]:
        """Get episode by ID"""
        try:
            return Episode.query.get(episode_id)
        except Exception as e:
            logger.error(f"Error getting episode by ID: {str(e)}")
            return None

    def update_episode(self, episode_id: str, **kwargs) -> Optional[Episode]:
        """Update episode"""
        try:
            episode = self.get_episode_by_id(episode_id)

            if not episode:
                return None

            for key, value in kwargs.items():
                if hasattr(episode, key):
                    setattr(episode, key, value)

            episode.updated_at = datetime.now(timezone.utc)
            self.db.session.commit()
            self.db.session.refresh(episode)

            logger.info(f"Updated episode: {episode.title}")
            return episode

        except Exception as e:
            logger.error(f"Error updating episode: {str(e)}")
            self.db.session.rollback()
            return None

    def delete_episode(self, episode_id: str) -> bool:
        """Delete an episode"""
        try:
            episode = self.get_episode_by_id(episode_id)
            if not episode:
                return False

            self.db.session.delete(episode)
            self.db.session.commit()
            logger.info(f"Deleted episode: {episode.title}")
            return True

        except Exception as e:
            logger.error(f"Error deleting episode: {str(e)}")
            self.db.session.rollback()
            return False

    ################
    # CHAT SESSION #
    ################
    # def create_chat_session(
    #     self,
    #     user_id: str,
    #     session_type: str,
    #     expert_id: str = None,
    #     episode_id: str = None,
    # ) -> Optional[ChatSession]:
    #     """Create a new chat session"""
    #     try:
    #         session = ChatSession(
    #             user_id=user_id,
    #             session_type=session_type,
    #             expert_id=expert_id,
    #             episode_id=episode_id,
    #         )

    #         self.db.session.add(session)
    #         self.db.session.commit()
    #         self.db.session.refresh(session)

    #         logger.info(
    #             f"Created chat session: {json.dumps(session.to_dict(), indent=2)}"
    #         )
    #         return session

    #     except Exception as e:
    #         logger.error(f"Error creating chat session: {str(e)}")
    #         self.db.session.rollback()
    #         return None

    # def get_chat_session(self, session_id: str) -> Optional[ChatSession]:
    #     """Get chat session by ID"""
    #     try:
    #         return ChatSession.query.get(session_id)
    #     except Exception as e:
    #         logger.error(f"Error getting chat session: {str(e)}")
    #         return None

    # def get_user_chat_sessions(
    #     self, user_id: str, limit: int = 50
    # ) -> List[ChatSession]:
    #     """Get user's chat sessions"""
    #     try:
    #         return (
    #             ChatSession.query.filter(ChatSession.user_id == user_id)
    #             .order_by(desc(ChatSession.updated_at))
    #             .limit(limit)
    #             .all()
    #         )
    #     except Exception as e:
    #         logger.error(f"Error getting user chat sessions: {str(e)}")
    #         return []

    # def add_chat_message(
    #     self,
    #     session_id: str,
    #     role: str,
    #     content: str,
    #     message_metadata: Dict[str, Any] = None,
    # ) -> Optional[ChatMessage]:
    #     """Add message to chat session"""
    #     try:
    #         message = ChatMessage(
    #             session_id=session_id,
    #             role=role,
    #             content=content,
    #             message_metadata=message_metadata,
    #         )

    #         self.db.session.add(message)

    #         session = self.get_chat_session(session_id)
    #         if session:
    #             session.updated_at = datetime.now(timezone.utc)

    #         self.db.session.commit()
    #         self.db.session.refresh(message)

    #         return message

    #     except Exception as e:
    #         logger.error(f"Error adding chat message: {str(e)}")
    #         self.db.session.rollback()
    #         return None

    # def get_chat_messages(self, session_id: str) -> List[ChatMessage]:
    #     """Get all messages for a chat session"""
    #     try:
    #         return (
    #             self.db.session.query(ChatMessage)
    #             .filter(ChatMessage.session_id == session_id)
    #             .order_by(ChatMessage.created_at)
    #             .all()
    #         )
    #     except Exception as e:
    #         logger.error(f"Error getting chat messages: {str(e)}")
    #         return []

    #############
    # USAGE LOG #
    #############
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
            usage_log = UsageLog(
                user_id=user_id,
                session_id=session_id,
                action_type=action_type,
                tokens_used=tokens_used,
                cost=cost,
                processing_time=processing_time,
                log_metadata=metadata,
            )

            self.db.session.add(usage_log)
            self.db.session.commit()
            self.db.session.refresh(usage_log)

            return usage_log

        except Exception as e:
            logger.error(f"Error logging usage: {str(e)}")
            self.db.session.rollback()
            return None
