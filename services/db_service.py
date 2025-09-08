import logging

from sqlalchemy import and_, desc, func
from datetime import datetime, timezone
from typing import List, Optional, Dict
from sqlalchemy.exc import IntegrityError
from database.db_models import User, Expert, Episode

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service layer for database operations"""

    def __init__(self, db):
        self.db = db

    ########
    # USER #
    ########
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            return self.db.session.query(User).filter(User.username == username).first()
        except Exception as e:
            logger.error(f"Error getting user by username: {str(e)}")
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

    #########
    # STATS #
    #########
    def get_user_stats(self, user_id: str) -> Dict:
        """Get dashboard statistics for a user"""
        try:
            # Get total experts count
            total_experts = (
                self.db.session.query(func.count(Expert.id))
                .filter(Expert.user_id == user_id)
                .scalar()
            )

            # Get total episodes count
            total_episodes = (
                self.db.session.query(func.count(Episode.id))
                .join(Expert, Episode.expert_id == Expert.id)
                .filter(Expert.user_id == user_id)
                .scalar()
            )

            return {
                "total_experts": total_experts or 0,
                "total_episodes": total_episodes or 0,
            }

        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return {
                "total_experts": 0,
                "total_episodes": 0,
            }
