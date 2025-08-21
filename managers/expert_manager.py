import logging

from database.db_models import Expert
from typing import List, Optional, Dict
from services.db_service import DatabaseService
from managers.pinecone_manager import PineconeManager

logger = logging.getLogger(__name__)


class ExpertManager:
    def __init__(self, db_service: DatabaseService, pinecone_manager: PineconeManager):
        """Initialize expert manager with Pinecone and Database"""
        self.db_service = db_service
        self.pinecone_manager = pinecone_manager

    def create_expert_with_content(
        self,
        user_id: str,
        expert_name: str,
        expert_description: str,
        episodes: List[Dict[str, str]],
    ) -> Optional[Expert]:
        """Create a new expert with manual content"""
        try:
            # Create expert in database
            db_expert = self.db_service.create_expert(
                user_id=user_id,
                expert_name=expert_name,
                expert_description=expert_description,
            )

            if not db_expert:
                logger.error("Failed to create expert in database")
                return None

            # Create episodes for this expert
            stored_episodes = []
            for episode_data in episodes:
                db_episode = self.db_service.create_episode(
                    expert_id=db_expert.id,
                    title=episode_data["title"],
                    content=episode_data["content"],
                )
                stored_episodes.append(db_episode)

            # Store content in Pinecone
            self._store_expert_content_in_pinecone(stored_episodes, db_expert.name)

            return db_expert

        except Exception as e:
            logger.error(f"Error creating expert: {str(e)}")
            return None

    def get_user_experts(self, user_id: str) -> List[Expert]:
        """Get all experts for a user"""
        try:
            user_experts = self.db_service.get_user_experts(user_id)
            return user_experts
        except Exception as e:
            logger.error(f"Error getting user experts: {str(e)}")
            return []

    # def add_episode_content(self, expert_id: str, title: str, content: str) -> bool:
    #     """Add new episode content to existing expert"""
    #     try:
    #         db_expert = self.db_service.get_expert_by_id(expert_id)
    #         if not db_expert:
    #             logger.error(f"Expert {expert_id} not found")
    #             return False

    #         # Create new episode
    #         db_episode = self.db_service.create_episode(
    #             expert_id=expert_id,
    #             title=title,
    #             url="",  # No URL for manual content
    #             is_temporary=False,
    #         )

    #         if not db_episode:
    #             logger.error("Failed to create episode in database")
    #             return False

    #         # Update with content
    #         self.db_service.update_episode(
    #             str(db_episode.id),
    #             transcript=content,
    #             summary="Manual content",
    #             processing_status="completed",
    #             processed_at=datetime.utcnow(),
    #         )

    #         # Store in Pinecone
    #         success = self._store_episode_content_in_pinecone(
    #             str(db_episode.id), db_expert.pinecone_namespace, title, content
    #         )

    #         if success:
    #             # Update expert's updated_at timestamp
    #             self.db_service.update_expert(
    #                 expert_id, updated_at=datetime.now(timezone.utc)
    #             )
    #             logger.info(f"Successfully added episode content to expert {expert_id}")
    #             return True
    #         else:
    #             logger.error(f"Failed to store episode content in Pinecone")
    #             return False

    #     except Exception as e:
    #         logger.error(f"Error adding episode content: {str(e)}")
    #         return False

    def _store_expert_content_in_pinecone(
        self, stored_episodes: List[str], db_expert_name: str
    ):
        """Store all expert content in Pinecone"""
        try:
            for db_episode in stored_episodes:
                self.pinecone_manager.store_episode_content(db_episode, db_expert_name)
        except Exception as e:
            logger.error(f"Error storing episode {db_episode.id} in Pinecone: {str(e)}")

    # def get_expert(self, expert_id: str) -> Optional[Expert]:
    #     """Get a specific expert with episodes"""
    #     try:
    #         db_expert = self.db_service.get_expert_by_id(expert_id)
    #         if not db_expert:
    #             return None

    #         # Get episodes
    #         db_episodes = self.db_service.get_expert_episodes(expert_id)
    #         episodes = []

    #         for db_episode in db_episodes:
    #             episode = Episode(
    #                 id=str(db_episode.id),
    #                 title=db_episode.title,
    #                 url=db_episode.url,
    #                 transcript=db_episode.transcript or "",
    #                 summary=db_episode.summary or "",
    #                 duration=db_episode.duration,
    #                 created_at=db_episode.created_at,
    #                 processed=db_episode.processing_status == "completed",
    #             )
    #             episodes.append(episode)

    #         expert = Expert(
    #             id=str(db_expert.id),
    #             name=db_expert.name,
    #             description=db_expert.description,
    #             episodes=episodes,
    #             created_at=db_expert.created_at,
    #             updated_at=db_expert.updated_at,
    #             user_id=str(db_expert.user_id),
    #             namespace=db_expert.pinecone_namespace,
    #         )

    #         return expert

    #     except Exception as e:
    #         logger.error(f"Error getting expert {expert_id}: {str(e)}")
    #         return None

    # def delete_expert(self, expert_id: str, user_id: str) -> bool:
    #     """Delete an expert"""
    #     try:
    #         db_expert = self.db_service.get_expert_by_id(expert_id)
    #         if not db_expert or str(db_expert.user_id) != user_id:
    #             return False

    #         # Remove from Pinecone
    #         self.pinecone_manager.delete_namespace(db_expert.pinecone_namespace)

    #         # Soft delete expert (mark as inactive)
    #         success = self.db_service.delete_expert(expert_id, user_id)

    #         if success:
    #             logger.info(f"Deleted expert {expert_id}")

    #         return success

    #     except Exception as e:
    #         logger.error(f"Error deleting expert {expert_id}: {str(e)}")
    #         return False
