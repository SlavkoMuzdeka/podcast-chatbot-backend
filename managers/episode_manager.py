import logging

from flask import jsonify
from typing import Dict, Tuple
from services.db_service import DatabaseService
from services.pinecone_service import PineconeService

logger = logging.getLogger(__name__)


class EpisodeManager:
    def __init__(self, db_service: DatabaseService, pinecone_service: PineconeService):
        """Initialize episode manager with Pinecone and Database"""
        self.db_service = db_service
        self.pinecone_service = pinecone_service

    def create_episode(self, expert_id: str, data: Dict):
        expert = self.db_service.get_expert_by_id(expert_id)

        is_valid, error_message = self._validate_data(expert, data)
        if not is_valid:
            return jsonify({"success": False, "error": error_message}), 400

        episode = self.db_service.create_episode(
            expert_id, data["title"], data["content"]
        )

        if episode:
            self.pinecone_service.store_episode_content(episode, expert.name)
            return (
                jsonify({"success": True, "data": {"episode": episode.to_dict()}}),
                201,
            )
        else:
            return jsonify({"success": False, "error": "Failed to create episode"}), 500

    def get_episodes(self, expert_id):
        """Get all episodes for a specific expert"""
        db_episodes = self.db_service.get_episodes(expert_id)
        episodes = []

        for db_episode in db_episodes:
            episodes.append(db_episode.to_dict())

        return jsonify({"success": True, "data": {"episodes": episodes}}), 200

    def update_episode(self, expert_id: str, episode_id: str, data: Dict):
        """Update an existing episode"""
        db_expert = self.db_service.get_expert_by_id(expert_id)

        is_valid, error_message = self._validate_data(db_expert, data)
        if not is_valid:
            return jsonify({"success": False, "error": error_message}), 400

        # Update episode in database
        episode = self.db_service.update_episode(
            episode_id,
            title=data["title"],
            content=data["content"],
        )

        if not episode:
            return (
                jsonify(
                    {"success": False, "error": "Failed to update episode in database"}
                ),
                500,
            )

        # Update content in Pinecone
        is_deleted = self.pinecone_service.delete_episode(episode_id, db_expert.name)
        if not is_deleted:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Failed to delete old episode content from Pinecone",
                    }
                ),
                500,
            )

        is_stored = self.pinecone_service.store_episode_content(episode, db_expert.name)
        if not is_stored:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Failed to store updated episode content in Pinecone",
                    }
                ),
                500,
            )

        return jsonify({"success": True}), 200

    def delete_episode(self, expert_id: str, episode_id: str):
        expert = self.db_service.get_expert_by_id(expert_id)
        if not expert:
            return (
                jsonify({"success": False, "error": "Expert not found"}),
                404,
            )

        # Verify episode belongs to expert
        episode = self.db_service.get_episode_by_id(episode_id)
        if not episode:
            return jsonify({"success": False, "error": "Episode not found"}), 404

        # Delete from Pinecone first
        is_deleted_from_pinecone = self.pinecone_service.delete_episode(
            episode_id, expert.name.lower().replace(" ", "_")
        )

        if not is_deleted_from_pinecone:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Failed to delete episode from Pinecone",
                    }
                ),
                500,
            )

        # Delete from database
        is_deleted_from_db = self.db_service.delete_episode(episode_id)

        if not is_deleted_from_db:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Failed to delete episode from database",
                    }
                ),
                500,
            )

        return (
            jsonify({"success": True, "message": "Episode deleted successfully"}),
            200,
        )

    def _validate_data(self, expert, data: Dict) -> Tuple[bool, str]:
        if not expert:
            return False, "Expert not found"
        if not data:
            return False, "No data provided"
        title = data.get("title", "").strip()
        content = data.get("content", "").strip()
        if not title:
            return False, "Episode title is required"
        if not content:
            return False, "Episode content is required"
        return True, ""
