import logging

from middleware.auth_middleware import jwt_required
from flask import Blueprint, request, jsonify, current_app


logger = logging.getLogger(__name__)
expert_bp = Blueprint("experts", __name__)


@expert_bp.route("/", methods=["GET"])
@jwt_required
def get_experts():
    """Retrieve all experts associated with the authenticated user.
    
    Returns:
        JSON: List of expert objects on success, error message on failure.
        Status codes: 200 (success), 500 (server error)
    """
    try:
        return current_app.expert_manager.get_experts(request.current_user["user_id"])
    except Exception as e:
        logger.error(f"Error getting user experts: {str(e)}")
        return jsonify({"success": False, "error": "Error getting user experts"}), 500


@expert_bp.route("/", methods=["POST"])
@jwt_required
def create_expert():
    """Create a new expert with the provided data.
    
    Request body should contain expert details.
    
    Returns:
        JSON: Created expert object on success, error message on failure.
        Status codes: 200 (success), 500 (server error)
    """
    try:
        return current_app.expert_manager.create_expert(
            user_id=request.current_user["user_id"], data=request.get_json()
        )
    except Exception as e:
        logger.error(f"Error creating expert: {str(e)}")
        return jsonify({"success": False, "error": "Error creating expert"}), 500


@expert_bp.route("/<expert_id>", methods=["DELETE"])
@jwt_required
def delete_expert(expert_id):
    """Delete an expert by ID.
    
    Args:
        expert_id (str): The ID of the expert to delete.
        
    Returns:
        JSON: Success/error message.
        Status codes: 200 (success), 500 (server error)
    """
    try:
        return current_app.expert_manager.delete_expert(
            expert_id, request.current_user["user_id"]
        )
    except Exception as e:
        logger.error(f"Error deleting expert {expert_id}: {str(e)}")
        return jsonify({"success": False, "error": "Error deleting expert"}), 500


@expert_bp.route("/<expert_id>/episodes", methods=["POST"])
@jwt_required
def create_episode(expert_id):
    """Create a new episode for the specified expert.
    
    Args:
        expert_id (str): The ID of the expert.
        
    Returns:
        JSON: Created episode object on success, error message on failure.
        Status codes: 200 (success), 500 (server error)
    """
    try:
        return current_app.episode_manager.create_episode(expert_id, request.get_json())
    except Exception as e:
        logger.error(f"Error creating episode for expert {expert_id}: {str(e)}")
        return jsonify({"success": False, "error": "Error creating episode"}), 500


@expert_bp.route("/<expert_id>/episodes", methods=["GET"])
@jwt_required
def get_episodes(expert_id):
    """Retrieve all episodes for a specific expert.
    
    Args:
        expert_id (str): The ID of the expert.
        
    Returns:
        JSON: List of episode objects on success, error message on failure.
        Status codes: 200 (success), 500 (server error)
    """
    try:
        return current_app.episode_manager.get_episodes(expert_id)
    except Exception as e:
        logger.error(f"Error getting episodes for expert {expert_id}: {str(e)}")
        return jsonify({"success": False, "error": "Error getting episodes"}), 500


@expert_bp.route("/<expert_id>/episodes/<episode_id>", methods=["PUT"])
@jwt_required
def update_episode(expert_id, episode_id):
    """Update an existing episode's information.
    
    Args:
        expert_id (str): The ID of the expert.
        episode_id (str): The ID of the episode to update.
        
    Returns:
        JSON: Updated episode object on success, error message on failure.
        Status codes: 200 (success), 500 (server error)
    """
    try:
        return current_app.episode_manager.update_episode(
            expert_id,
            episode_id,
            data=request.get_json(),
        )
    except Exception as e:
        logger.error(f"Error updating episode {episode_id}: {str(e)}")
        return jsonify({"success": False, "error": "Error updating episode"}), 500


@expert_bp.route("/<expert_id>/episodes/<episode_id>", methods=["DELETE"])
@jwt_required
def delete_episode(expert_id, episode_id):
    """Delete a specific episode.
    
    Args:
        expert_id (str): The ID of the expert.
        episode_id (str): The ID of the episode to delete.
        
    Returns:
        JSON: Success/error message.
        Status codes: 200 (success), 500 (server error)
    """
    try:
        return current_app.episode_manager.delete_episode(
            expert_id,
            episode_id,
        )
    except Exception as e:
        logger.error(f"Error deleting episode {episode_id}: {str(e)}")
        return jsonify({"success": False, "error": "Error deleting episode"}), 500


@expert_bp.route("/chat", methods=["POST"])
@jwt_required
def chat_with_expert():
    """Initiate a non-streaming chat session with an expert.
    
    Request body should contain the message and expert ID.
    
    Returns:
        JSON: Expert's response or error message.
        Status codes: 200 (success), 500 (server error)
    """
    try:
        return current_app.chat_manager.chat_with_expert(request.get_json())
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        return jsonify({"success": False, "error": "Error generating response"}), 500


@expert_bp.route("/chat/stream", methods=["POST"])
@jwt_required
def chat_with_expert_stream():
    """Initiate a streaming chat session with an expert.
    
    Request body should contain the message and expert ID.
    
    Returns:
        Streaming response with chunks of the expert's response.
        Status codes: 200 (success), 500 (server error)
    """
    try:
        return current_app.chat_manager.chat_with_expert_stream(request.get_json())
    except Exception as e:
        logger.error(f"Error in streaming chat: {str(e)}")
        return jsonify({"success": False, "error": "Error generating response"}), 500
