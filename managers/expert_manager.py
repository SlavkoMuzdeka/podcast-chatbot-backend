import logging


from flask import jsonify
from database.db_models import Expert
from typing import List, Optional, Dict
from services.db_service import DatabaseService
from services.pinecone_service import PineconeService

logger = logging.getLogger(__name__)


class ExpertManager:
    def __init__(self, db_service: DatabaseService, pinecone_service: PineconeService):
        """Initialize expert manager with Pinecone and Database"""
        self.db_service = db_service
        self.pinecone_service = pinecone_service

    def get_experts(self, user_id: str) -> List[Expert]:
        """Get all experts for a user"""
        experts = []
        db_experts = self.db_service.get_user_experts(user_id)

        for expert in db_experts:
            experts.append(expert.to_dict())

        return jsonify({"success": True, "data": {"experts": experts}}), 200

    def create_expert(
        self,
        user_id: str,
        data: Dict,
    ) -> Optional[Expert]:
        """Create a new expert with manual content"""
        if not data:
            return (
                jsonify({"success": False, "error": "No data provided."}),
                400,
            )

        expert_name = data.get("name", "").strip()
        expert_description = data.get("description", "").strip()
        episodes = data.get("episodes", [])

        if not expert_name:
            return jsonify({"success": False, "error": "Expert name is required."}), 400

        if not expert_description:
            return (
                jsonify({"success": False, "error": "Expert description is required."}),
                400,
            )

        if not episodes or len(episodes) == 0:
            return (
                jsonify(
                    {"success": False, "error": "At least one episode is required."}
                ),
                400,
            )

        # Validate episodes
        valid_episodes = []
        for episode in episodes:
            title = episode.get("title", "").strip()
            content = episode.get("content", "").strip()

            if title and content:
                valid_episodes.append({"title": title, "content": content})

        if len(valid_episodes) == 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "At least one episode with title and content is required.",
                    }
                ),
                400,
            )

        # Create expert in database
        expert = self.db_service.create_expert(
            user_id=user_id,
            expert_name=expert_name,
            expert_description=expert_description,
        )

        if not expert:
            return jsonify({"success": False, "error": "Failed to create expert."}), 400

        # Create episodes for this expert
        stored_episodes = []
        for episode_data in episodes:
            db_episode = self.db_service.create_episode(
                expert_id=expert.id,
                title=episode_data["title"],
                content=episode_data["content"],
            )
            stored_episodes.append(db_episode)

        # Store content in Pinecone
        for db_episode in stored_episodes:
            self.pinecone_service.store_episode_content(db_episode, expert.name)

        return jsonify({"success": True}), 201

    def delete_expert(self, expert_id: str, user_id: str) -> bool:
        """Delete an expert"""
        db_expert = self.db_service.get_expert_by_id(expert_id)
        if not db_expert:
            return jsonify({"success": False, "error": "Expert not found"}), 404

        # Remove from Pinecone
        is_deleted_from_pinecone = self.pinecone_service.delete_namespace(
            db_expert.name
        )

        if not is_deleted_from_pinecone:
            return (
                jsonify(
                    {"success": False, "error": "Failed to remove expert from Pinecone"}
                ),
                500,
            )

        # Remove from database
        is_deleted_from_db = self.db_service.delete_expert(expert_id, user_id)

        if not is_deleted_from_db:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Failed to delete expert {expert_id} from database",
                    }
                ),
                500,
            )

        return jsonify({"success": True}), 200
