import logging

from middleware.auth_middleware import jwt_required
from flask import Blueprint, request, jsonify, current_app


logger = logging.getLogger(__name__)
expert_bp = Blueprint("experts", __name__)


@expert_bp.route("/", methods=["GET"])
@jwt_required
def get_experts():
    """Get all experts for the authenticated user"""
    try:
        return current_app.expert_manager.get_experts(request.current_user["user_id"])
    except Exception as e:
        logger.error(f"Error getting user experts: {str(e)}")
        return jsonify({"success": False, "error": "Error getting user experts"}), 500


@expert_bp.route("/", methods=["POST"])
@jwt_required
def create_expert():
    """Create a new expert with manual content"""
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
    """Delete an expert"""
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
    """Create a new episode for an expert"""
    try:
        return current_app.episode_manager.create_episode(expert_id, request.get_json())
    except Exception as e:
        logger.error(f"Error creating episode for expert {expert_id}: {str(e)}")
        return jsonify({"success": False, "error": "Error creating episode"}), 500


@expert_bp.route("/<expert_id>/episodes", methods=["GET"])
@jwt_required
def get_episodes(expert_id):
    """Get all episodes for a specific expert"""
    try:
        return current_app.episode_manager.get_episodes(expert_id)
    except Exception as e:
        logger.error(f"Error getting episodes for expert {expert_id}: {str(e)}")
        return jsonify({"success": False, "error": "Error getting episodes"}), 500


@expert_bp.route("/<expert_id>/episodes/<episode_id>", methods=["PUT"])
@jwt_required
def update_episode(expert_id, episode_id):
    """Update an existing episode"""
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
    """Delete an episode"""
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
    """Chat with a specific expert (non-streaming)"""
    try:
        return current_app.chat_manager.chat_with_expert(request.get_json())
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        return jsonify({"success": False, "error": "Error generating response"}), 500


@expert_bp.route("/chat/stream", methods=["POST"])
@jwt_required
def chat_with_expert_stream():
    """Chat with a specific expert (streaming)"""
    try:
        return current_app.chat_manager.chat_with_expert_stream(request.get_json())
    except Exception as e:
        logger.error(f"Error in streaming chat: {str(e)}")
        return jsonify({"success": False, "error": "Error generating response"}), 500
