import logging

from functools import wraps
from flask import request, jsonify, current_app

logger = logging.getLogger(__name__)


def jwt_required(f):
    """Decorator to require valid JWT token"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        payload = current_app.auth_manager.verify_token(token)

        if not payload:
            return jsonify({"error": "Token is invalid or expired"}), 401

        request.current_user = payload

        return f(*args, **kwargs)

    return decorated_function
