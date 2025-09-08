import logging

from middleware.auth_middleware import jwt_required
from flask import Blueprint, jsonify, current_app


logger = logging.getLogger(__name__)
user_bp = Blueprint("users", __name__)


@user_bp.route("/<user_id>/stats", methods=["GET"])
@jwt_required
def get_user_stats(user_id):
    """Get dashboard statistics for the authenticated user"""
    try:
        return current_app.user_manager.get_user_stats(user_id)
    except Exception as e:
        logger.error(f"Error getting user stats: {str(e)}")
        return jsonify({"success": False, "error": "Error getting user stats"}), 500
