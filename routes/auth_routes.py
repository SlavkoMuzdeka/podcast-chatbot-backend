import logging

from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate a user and return JWT tokens if successful.

    This endpoint handles user authentication by validating the provided username and password.
    On successful authentication, it returns access and refresh tokens.
    """
    try:
        data = request.get_json()
        if not data or "username" not in data or "password" not in data:
            return (
                jsonify({"success": False, "error": "Username and password required"}),
                400,
            )

        result = current_app.auth_manager.authenticate_user(
            data["username"], data["password"]
        )

        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 401

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"success": False, "error": "Login failed"}), 500
