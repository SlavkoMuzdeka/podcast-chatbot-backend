import logging

from flask import jsonify
from typing import Dict, Tuple
from services.db_service import DatabaseService
from services.pinecone_service import PineconeService

logger = logging.getLogger(__name__)


class EpisodeManager:
    """Manages podcast episode operations including CRUD and vector storage.

    This class handles all operations related to podcast episodes including creation,
    retrieval, updating, and deletion, while maintaining consistency between the
    database and vector storage (Pinecone).
    """

    def __init__(self, db_service: DatabaseService, pinecone_service: PineconeService):
        """Initialize the EpisodeManager with required services.

        Args:
            db_service: Service for database operations
            pinecone_service: Service for vector storage operations
        """
        self.db_service = db_service
        self.pinecone_service = pinecone_service

    def create_episode(self, expert_id: str, data: Dict) -> tuple:
        """Create a new episode for an expert.

        This method creates a new episode in the database and stores its content in Pinecone
        for vector search capabilities.

        Args:
            expert_id: ID of the expert who owns the episode
            data: Dictionary containing episode data with keys:
                - title: Episode title (required)
                - content: Episode content/transcript (required)

        Returns:
            tuple: (JSON response, HTTP status code)
                On success: {"success": True, "data": {"episode": dict}} with status 201
                On error: {"success": False, "error": str} with appropriate status code
        """
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

    def get_episodes(self, expert_id: str) -> tuple:
        """Retrieve all episodes for a specific expert.

        Args:
            expert_id: ID of the expert whose episodes to retrieve

        Returns:
            tuple: (JSON response, HTTP status code)
                On success: {"success": True, "data": {"episodes": list[dict]}} with status 200
                Each episode dict contains the episode's details including id, title, and content
        """
        db_episodes = self.db_service.get_episodes(expert_id)
        episodes = []

        for db_episode in db_episodes:
            episodes.append(db_episode.to_dict())

        return jsonify({"success": True, "data": {"episodes": episodes}}), 200

    def update_episode(self, expert_id: str, episode_id: str, data: Dict) -> tuple:
        """Update an existing episode's metadata and content.

        This method updates both the database record and the corresponding
        vector embeddings in Pinecone. It first validates the input data,
        then updates the database, and finally updates the vector storage.

        Args:
            expert_id: ID of the expert who owns the episode
            episode_id: ID of the episode to update
            data: Dictionary containing update data with keys:
                - title: New episode title (required)
                - content: New episode content/transcript (required)

        Returns:
            tuple: (JSON response, HTTP status code)
                On success: {"success": True} with status 200
                On error: {"success": False, "error": str} with appropriate status code
        """
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

    def delete_episode(self, expert_id: str, episode_id: str) -> tuple:
        """Delete an episode and its associated vector embeddings.

        This method performs a cascading delete, removing the episode from both
        the database and Pinecone vector storage. It first verifies the expert
        and episode exist, then deletes from Pinecone before removing from the database.

        Args:
            expert_id: ID of the expert who owns the episode
            episode_id: ID of the episode to delete

        Returns:
            tuple: (JSON response, HTTP status code)
                On success: {"success": True, "message": str} with status 200
                On error: {"success": False, "error": str} with appropriate status code
        """
        expert = self.db_service.get_expert_by_id(expert_id)
        if not expert:
            return (
                jsonify({"success": False, "error": "Expert not found"}),
                404,
            )

        # Verify episode exists
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
        """Validate episode data before processing.

        This helper method checks that all required fields are present and non-empty.
        It's used by both create and update operations to ensure data consistency.

        Args:
            expert: Expert object or None if expert not found
            data: Dictionary containing episode data to validate

        Returns:
            tuple: (is_valid: bool, error_message: str)
                - is_valid: True if data is valid, False otherwise
                - error_message: Empty string if valid, otherwise describes the error
        """
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
