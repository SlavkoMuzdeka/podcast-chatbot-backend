import logging

from middleware.auth_middleware import jwt_required
from flask import Blueprint, request, jsonify, current_app


logger = logging.getLogger(__name__)
episode_bp = Blueprint("episodes", __name__)


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
