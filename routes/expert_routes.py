import logging

from middleware.auth_middleware import jwt_required
from flask import Blueprint, request, jsonify, current_app


logger = logging.getLogger(__name__)
expert_bp = Blueprint("experts", __name__)


@expert_bp.route("/", methods=["POST"])
@jwt_required
def create_expert():
    """Create a new expert with manual content"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        # Validate required fields
        expert_name = data.get("name", "").strip()
        expert_description = data.get("description", "").strip()
        episodes = data.get("episodes", [])

        if not expert_name:
            return jsonify({"success": False, "error": "Expert name is required"}), 400

        if not expert_description:
            return (
                jsonify({"success": False, "error": "Expert description is required"}),
                400,
            )

        if not episodes or len(episodes) == 0:
            return (
                jsonify(
                    {"success": False, "error": "At least one episode is required"}
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
                        "error": "At least one episode with title and content is required",
                    }
                ),
                400,
            )

        # Get user ID from auth middleware
        user_id = request.current_user["user_id"]

        # Create expert using episode manager
        expert = current_app.expert_manager.create_expert_with_content(
            user_id=user_id,
            expert_name=expert_name,
            expert_description=expert_description,
            episodes=valid_episodes,
        )

        if expert:
            return (
                jsonify({"success": True}),
                201,
            )

        return jsonify({"success": False, "error": "Failed to create expert"}), 500

    except Exception as e:
        logger.error(f"Error creating expert: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@expert_bp.route("/", methods=["GET"])
@jwt_required
def get_user_experts():
    """Get all experts for the authenticated user"""
    try:
        user_id = request.current_user["user_id"]

        user_experts = current_app.expert_manager.get_user_experts(user_id)

        experts_data = []
        for expert in user_experts:
            experts_data.append(
                {
                    "id": expert.id,
                    "name": expert.name,
                    "description": expert.description,
                    "updatedAt": (
                        expert.updated_at.isoformat() if expert.updated_at else None
                    ),
                }
            )

        return jsonify({"success": True, "data": {"experts": experts_data}}), 200

    except Exception as e:
        logger.error(f"Error getting user experts: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


# @expert_bp.route("/<expert_id>", methods=["GET"])
# @require_auth
# def get_expert(expert_id):
#     """Get a specific expert with episodes"""
#     try:
#         expert = current_app.episode_manager.get_expert(expert_id)

#         if not expert:
#             return jsonify({"success": False, "error": "Expert not found"}), 404

#         # Verify ownership
#         user_id = request.user_id
#         if expert.user_id != user_id:
#             return jsonify({"success": False, "error": "Access denied"}), 403

#         expert_data = {
#             "id": expert.id,
#             "name": expert.name,
#             "description": expert.description,
#             "namespace": expert.namespace,
#             "created_at": expert.created_at.isoformat() if expert.created_at else None,
#             "updated_at": expert.updated_at.isoformat() if expert.updated_at else None,
#             "episodes": [],
#         }

#         if expert.episodes:
#             for episode in expert.episodes:
#                 expert_data["episodes"].append(
#                     {
#                         "id": episode.id,
#                         "title": episode.title,
#                         "summary": episode.summary,
#                         "duration": episode.duration,
#                         "created_at": (
#                             episode.created_at.isoformat()
#                             if episode.created_at
#                             else None
#                         ),
#                         "processed": episode.processed,
#                     }
#                 )

#         return jsonify({"success": True, "expert": expert_data}), 200

#     except Exception as e:
#         logger.error(f"Error getting expert {expert_id}: {str(e)}")
#         return jsonify({"success": False, "error": "Internal server error"}), 500


# @expert_bp.route("/<expert_id>", methods=["DELETE"])
# @require_auth
# def delete_expert(expert_id):
#     """Delete an expert"""
#     try:
#         user_id = request.user_id

#         success = current_app.episode_manager.delete_expert(expert_id, user_id)

#         if success:
#             return (
#                 jsonify({"success": True, "message": "Expert deleted successfully"}),
#                 200,
#             )
#         else:
#             return (
#                 jsonify(
#                     {"success": False, "error": "Expert not found or access denied"}
#                 ),
#                 404,
#             )

#     except Exception as e:
#         logger.error(f"Error deleting expert {expert_id}: {str(e)}")
#         return jsonify({"success": False, "error": "Internal server error"}), 500


# @expert_bp.route("/<expert_id>/episodes", methods=["POST"])
# @require_auth
# def add_episode_content(expert_id):
#     """Add new episode content to existing expert"""
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({"success": False, "error": "No data provided"}), 400

#         title = data.get("title", "").strip()
#         content = data.get("content", "").strip()

#         if not title:
#             return (
#                 jsonify({"success": False, "error": "Episode title is required"}),
#                 400,
#             )

#         if not content:
#             return (
#                 jsonify({"success": False, "error": "Episode content is required"}),
#                 400,
#             )

#         # Verify expert exists and user has access
#         expert = current_app.episode_manager.get_expert(expert_id)
#         if not expert:
#             return jsonify({"success": False, "error": "Expert not found"}), 404

#         user_id = request.user_id
#         if expert.user_id != user_id:
#             return jsonify({"success": False, "error": "Access denied"}), 403

#         # Add episode content
#         success = current_app.episode_manager.add_episode_content(
#             expert_id, title, content
#         )

#         if success:
#             return (
#                 jsonify(
#                     {"success": True, "message": "Episode content added successfully"}
#                 ),
#                 201,
#             )
#         else:
#             return (
#                 jsonify({"success": False, "error": "Failed to add episode content"}),
#                 500,
#             )

#     except Exception as e:
#         logger.error(f"Error adding episode content to expert {expert_id}: {str(e)}")
#         return jsonify({"success": False, "error": "Internal server error"}), 500
