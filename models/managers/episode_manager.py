import uuid
import logging

from datetime import datetime
from models.episode import Episode, Expert
from typing import List, Optional, Dict, Any
from services.database_service import db_service
from models.managers.product_a_client import ProductAClient
from models.managers.pinecone_manager import PineconeManager

logger = logging.getLogger(__name__)


class EpisodeManager:
    def __init__(self):
        """Initialize episode manager with Product A, Pinecone, and Database"""
        self.product_a_client = ProductAClient()
        self.pinecone_manager = PineconeManager()

    def create_temporary_episode(self, url: str, title: str = "") -> Episode:
        """Create a temporary episode for single episode chat"""
        # Create episode in database
        db_episode = db_service.create_episode(
            expert_id=None,
            title=title or f"Episode from {url}",
            url=url,
            is_temporary=True,
        )

        if not db_episode:
            raise Exception("Failed to create episode in database")

        # Convert to domain model
        episode = Episode(
            id=str(db_episode.id),
            title=db_episode.title,
            url=db_episode.url,
            transcript=db_episode.transcript or "",
            summary=db_episode.summary or "",
            duration=db_episode.duration,
            created_at=db_episode.created_at,
            processed=db_episode.processing_status == "completed",
        )

        return episode

    def process_episode_with_product_a(self, episode_id: str) -> bool:
        """Process episode using Product A"""
        try:
            # Get episode from database
            db_episode = db_service.get_episode_by_id(episode_id)
            if not db_episode:
                logger.error(f"Episode {episode_id} not found in database")
                return False

            # Update status to processing
            db_service.update_episode(episode_id, processing_status="processing")

            logger.info(f"Processing episode {episode_id} with Product A")

            # Call Product A to process the episode
            result = self.product_a_client.process_episode(db_episode.url, episode_id)

            if result["success"]:
                # Update episode with processed content
                update_data = {
                    "transcript": result.get("transcript", ""),
                    "summary": result.get("summary", ""),
                    "title": result.get("title", db_episode.title),
                    "duration": result.get("duration"),
                    "episode_metadata": result.get(
                        "metadata", {}
                    ),  # Updated column name
                    "processing_status": "completed",
                    "processed_at": datetime.utcnow(),
                }

                db_service.update_episode(episode_id, **update_data)
                logger.info(f"Successfully processed episode {episode_id}")
                return True
            else:
                # Update with error status
                db_service.update_episode(
                    episode_id,
                    processing_status="failed",
                    processing_error=result.get("error", "Unknown error"),
                )
                logger.error(
                    f"Failed to process episode {episode_id}: {result.get('error')}"
                )
                return False

        except Exception as e:
            logger.error(f"Error processing episode {episode_id}: {str(e)}")
            db_service.update_episode(
                episode_id, processing_status="failed", processing_error=str(e)
            )
            return False

    def store_episode_in_pinecone(self, episode_id: str, namespace: str) -> bool:
        """Store episode content in Pinecone"""
        try:
            db_episode = db_service.get_episode_by_id(episode_id)
            if not db_episode or db_episode.processing_status != "completed":
                logger.warning(f"Episode {episode_id} not processed or has no content")
                return False

            metadata = {
                "title": db_episode.title,
                "url": db_episode.url,
                "duration": db_episode.duration,
                "created_at": (
                    db_episode.created_at.isoformat() if db_episode.created_at else None
                ),
            }

            return self.pinecone_manager.store_episode_content(
                episode_id,
                namespace,
                db_episode.transcript,
                db_episode.summary,
                metadata,
            )

        except Exception as e:
            logger.error(f"Error storing episode {episode_id} in Pinecone: {str(e)}")
            return False

    def create_expert(
        self, user_id: str, name: str, description: str, episode_urls: List[str]
    ) -> Optional[Expert]:
        """Create a new expert with associated episodes"""
        try:
            expert_id = str(uuid.uuid4())
            namespace = f"expert_{expert_id}"

            # Create expert in database
            db_expert = db_service.create_expert(
                user_id=user_id,
                name=name,
                description=description,
                pinecone_namespace=namespace,
            )

            if not db_expert:
                logger.error("Failed to create expert in database")
                return None

            # Create episodes for this expert
            episode_ids = []
            for url in episode_urls:
                db_episode = db_service.create_episode(
                    expert_id=str(db_expert.id),
                    title=f"Episode from {url}",
                    url=url,
                    is_temporary=False,
                )
                if db_episode:
                    episode_ids.append(str(db_episode.id))

            # Convert to domain model
            expert = Expert(
                id=str(db_expert.id),
                name=db_expert.name,
                description=db_expert.description,
                episodes=[],  # Will be populated when needed
                created_at=db_expert.created_at,
                updated_at=db_expert.updated_at,
                user_id=user_id,
                namespace=namespace,
            )

            # Process episodes asynchronously (in a real app, this would be a background task)
            self._process_expert_episodes(str(db_expert.id), episode_ids)

            return expert

        except Exception as e:
            logger.error(f"Error creating expert: {str(e)}")
            return None

    def _process_expert_episodes(self, expert_id: str, episode_ids: List[str]):
        """Process all episodes for an expert and store in Pinecone"""
        db_expert = db_service.get_expert_by_id(expert_id)
        if not db_expert:
            logger.error(f"Expert {expert_id} not found")
            return

        logger.info(
            f"Processing {len(episode_ids)} episodes for expert {db_expert.name}"
        )

        # Update expert status to processing
        db_service.update_expert(expert_id, processing_status="processing")

        processed_count = 0
        for episode_id in episode_ids:
            try:
                # Process with Product A
                if self.process_episode_with_product_a(episode_id):
                    # Store in Pinecone if processing was successful
                    if self.store_episode_in_pinecone(
                        episode_id, db_expert.pinecone_namespace
                    ):
                        processed_count += 1
                        logger.info(
                            f"Successfully processed episode {episode_id} for expert {db_expert.name}"
                        )
                    else:
                        logger.error(
                            f"Failed to store episode {episode_id} in Pinecone"
                        )

            except Exception as e:
                logger.error(
                    f"Error processing episode {episode_id} for expert {db_expert.name}: {str(e)}"
                )

        # Update expert status
        if processed_count == len(episode_ids):
            db_service.update_expert(expert_id, processing_status="completed")
        elif processed_count > 0:
            db_service.update_expert(expert_id, processing_status="partially_completed")
        else:
            db_service.update_expert(expert_id, processing_status="failed")

    def get_user_experts(self, user_id: str) -> List[Expert]:
        """Get all experts for a user"""
        try:
            db_experts = db_service.get_user_experts(user_id)
            experts = []

            for db_expert in db_experts:
                # Get episode count
                episodes = db_service.get_expert_episodes(str(db_expert.id))

                expert = Expert(
                    id=str(db_expert.id),
                    name=db_expert.name,
                    description=db_expert.description,
                    episodes=[],  # Don't load all episodes here for performance
                    created_at=db_expert.created_at,
                    updated_at=db_expert.updated_at,
                    user_id=user_id,
                    namespace=db_expert.pinecone_namespace,
                )
                experts.append(expert)

            return experts

        except Exception as e:
            logger.error(f"Error getting user experts: {str(e)}")
            return []

    def get_expert(self, expert_id: str) -> Optional[Expert]:
        """Get a specific expert with episodes"""
        try:
            db_expert = db_service.get_expert_by_id(expert_id)
            if not db_expert:
                return None

            # Get episodes
            db_episodes = db_service.get_expert_episodes(expert_id)
            episodes = []

            for db_episode in db_episodes:
                episode = Episode(
                    id=str(db_episode.id),
                    title=db_episode.title,
                    url=db_episode.url,
                    transcript=db_episode.transcript or "",
                    summary=db_episode.summary or "",
                    duration=db_episode.duration,
                    created_at=db_episode.created_at,
                    processed=db_episode.processing_status == "completed",
                )
                episodes.append(episode)

            expert = Expert(
                id=str(db_expert.id),
                name=db_expert.name,
                description=db_expert.description,
                episodes=episodes,
                created_at=db_expert.created_at,
                updated_at=db_expert.updated_at,
                user_id=str(db_expert.user_id),
                namespace=db_expert.pinecone_namespace,
            )

            return expert

        except Exception as e:
            logger.error(f"Error getting expert {expert_id}: {str(e)}")
            return None

    def update_expert(
        self,
        expert_id: str,
        name: str = None,
        description: str = None,
        add_episodes: List[str] = None,
        remove_episode_ids: List[str] = None,
    ) -> Optional[Expert]:
        """Update an expert"""
        try:
            # Update basic info
            update_data = {}
            if name:
                update_data["name"] = name
            if description:
                update_data["description"] = description

            if update_data:
                db_service.update_expert(expert_id, **update_data)

            db_expert = db_service.get_expert_by_id(expert_id)
            if not db_expert:
                return None

            # Add new episodes
            if add_episodes:
                new_episode_ids = []
                for url in add_episodes:
                    db_episode = db_service.create_episode(
                        expert_id=expert_id,
                        title=f"Episode from {url}",
                        url=url,
                        is_temporary=False,
                    )
                    if db_episode:
                        new_episode_ids.append(str(db_episode.id))

                # Process new episodes
                self._process_expert_episodes(expert_id, new_episode_ids)

            # Remove episodes
            if remove_episode_ids:
                for episode_id in remove_episode_ids:
                    # Remove from Pinecone
                    self.pinecone_manager.delete_episode_content(
                        episode_id, db_expert.pinecone_namespace
                    )
                    # Note: In a real app, you might want to soft delete instead of hard delete
                    # For now, we'll just mark them as inactive or remove them

            return self.get_expert(expert_id)

        except Exception as e:
            logger.error(f"Error updating expert {expert_id}: {str(e)}")
            return None

    def delete_expert(self, expert_id: str, user_id: str) -> bool:
        """Delete an expert"""
        try:
            db_expert = db_service.get_expert_by_id(expert_id)
            if not db_expert or str(db_expert.user_id) != user_id:
                return False

            # Remove from Pinecone
            self.pinecone_manager.delete_namespace(db_expert.pinecone_namespace)

            # Soft delete expert (mark as inactive)
            success = db_service.delete_expert(expert_id, user_id)

            if success:
                logger.info(f"Deleted expert {expert_id}")

            return success

        except Exception as e:
            logger.error(f"Error deleting expert {expert_id}: {str(e)}")
            return False

    def get_episode(self, episode_id: str) -> Optional[Episode]:
        """Get episode by ID"""
        try:
            db_episode = db_service.get_episode_by_id(episode_id)
            if not db_episode:
                return None

            episode = Episode(
                id=str(db_episode.id),
                title=db_episode.title,
                url=db_episode.url,
                transcript=db_episode.transcript or "",
                summary=db_episode.summary or "",
                duration=db_episode.duration,
                created_at=db_episode.created_at,
                processed=db_episode.processing_status == "completed",
            )

            return episode

        except Exception as e:
            logger.error(f"Error getting episode {episode_id}: {str(e)}")
            return None

    def get_episode_processing_status(self, episode_id: str) -> Dict[str, Any]:
        """Get processing status for an episode"""
        try:
            db_episode = db_service.get_episode_by_id(episode_id)
            if not db_episode:
                return {"success": False, "error": "Episode not found"}

            return {
                "success": True,
                "status": db_episode.processing_status,
                "processed": db_episode.processing_status == "completed",
                "error": db_episode.processing_error,
            }

        except Exception as e:
            logger.error(f"Error getting episode status {episode_id}: {str(e)}")
            return {"success": False, "error": str(e)}
