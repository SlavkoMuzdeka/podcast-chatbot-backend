import os

from dotenv import load_dotenv

load_dotenv(override=True)

from functools import wraps
from flask_limiter import Limiter
from utils.app_utils import setup_logger
from datetime import datetime, timedelta
from flask_cors import CORS, cross_origin
from flask import Flask, jsonify, request, g
from services.database_service import db_service
from flask_limiter.util import get_remote_address
from models.managers.chat_manager import ChatManager
from models.managers.auth_manager import AuthManager
from models.managers.episode_manager import EpisodeManager
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    get_jwt_identity,
)

logger = setup_logger()

# Initialize components
auth_manager = AuthManager()
episode_manager = EpisodeManager()
chat_manager = ChatManager()

app = Flask(__name__)

# Security Configuration
app.config.update(
    JWT_SECRET_KEY=os.getenv(
        "JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production"
    ),
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=24),
    JWT_ALGORITHM="HS256",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24),
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# CORS Configuration
CORS(
    app,
    origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    supports_credentials=True,
)

# JWT Manager
jwt_manager = JWTManager(app)

# Rate Limiting
# limiter = Limiter(
#     key_func=get_remote_address,
#     app=app,
#     default_limits=["1000 per hour", "100 per minute"],
# )


# Security Headers Middleware
# @app.after_request
# def add_security_headers(response):
#     response.headers["X-Content-Type-Options"] = "nosniff"
#     response.headers["X-Frame-Options"] = "DENY"
#     response.headers["X-XSS-Protection"] = "1; mode=block"
#     response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
#     response.headers["Content-Security-Policy"] = (
#         "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
#     )
#     return response


# JWT Error Handlers
@jwt_manager.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return (
        jsonify(
            {"success": False, "error": "Token has expired", "code": "TOKEN_EXPIRED"}
        ),
        401,
    )


@jwt_manager.invalid_token_loader
def invalid_token_callback(error):
    return (
        jsonify({"success": False, "error": "Invalid token", "code": "INVALID_TOKEN"}),
        401,
    )


@jwt_manager.unauthorized_loader
def missing_token_callback(error):
    return (
        jsonify(
            {
                "success": False,
                "error": "Authorization token required",
                "code": "TOKEN_REQUIRED",
            }
        ),
        401,
    )


# Input Validation Decorator
def validate_json(*required_fields):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Content-Type must be application/json",
                        }
                    ),
                    400,
                )

            data = request.get_json()
            if not data:
                return (
                    jsonify({"success": False, "error": "Request body required"}),
                    400,
                )

            # Check required fields
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": f"Missing required fields: {', '.join(missing_fields)}",
                        }
                    ),
                    400,
                )

            # Sanitize string inputs
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = value.strip()[:1000]  # Limit length and trim

            g.request_data = data
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# Routes
@app.route("/")
@cross_origin()
def index():
    return jsonify(
        {"message": "Podcast Chatbot API", "version": "1.0.0", "status": "healthy"}
    )


@app.route("/api/auth/login", methods=["POST", "OPTIONS"])
@cross_origin()
# @limiter.limit("5 per minute")
@validate_json("username", "password")
def login():
    """Authenticate user and return JWT token"""
    try:
        data = g.request_data
        username = data["username"]
        password = data["password"]

        # Additional validation
        if len(username) < 3 or len(username) > 50:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Username must be between 3 and 50 characters",
                    }
                ),
                400,
            )

        if len(password) < 6:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401

        user_data = auth_manager.authenticate_user(username, password)
        if not user_data:
            return (
                jsonify({"success": False, "error": "Invalid username or password"}),
                401,
            )

        if not user_data.get("is_active", True):
            return jsonify({"success": False, "error": "Account is deactivated"}), 401

        token = auth_manager.create_token(user_data)
        if not token:
            return (
                jsonify(
                    {"success": False, "error": "Failed to create authentication token"}
                ),
                500,
            )

        # Log successful login
        db_service.log_usage(
            user_id=user_data["id"],
            action_type="login",
            metadata={  # Using the correct parameter name
                "ip_address": request.remote_addr,
                "user_agent": request.headers.get("User-Agent"),
            },
        )

        return jsonify(
            {
                "success": True,
                "token": token,
                "user": {
                    "id": user_data["id"],
                    "username": user_data["username"],
                    "email": user_data.get("email"),
                    "full_name": user_data.get("full_name"),
                    "role": user_data["role"],
                    "is_active": user_data["is_active"],
                },
                "message": "Login successful",
            }
        )

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@app.route("/api/auth/verify", methods=["POST"])
@jwt_required()
@cross_origin()
def verify_token():
    """Verify JWT token and return user info"""
    try:
        user_id = get_jwt_identity()
        user_data = auth_manager.get_user_by_id(user_id)

        if not user_data or not user_data.get("is_active", True):
            return jsonify({"success": False, "error": "Invalid or inactive user"}), 401

        return jsonify(
            {
                "success": True,
                "user": {
                    "id": user_data["id"],
                    "username": user_data["username"],
                    "email": user_data.get("email"),
                    "full_name": user_data.get("full_name"),
                    "role": user_data["role"],
                    "is_active": user_data["is_active"],
                },
            }
        )

    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return jsonify({"success": False, "error": "Token verification failed"}), 401


@app.route("/api/auth/logout", methods=["POST"])
@jwt_required()
@cross_origin()
def logout():
    """Logout user and invalidate token"""
    try:
        user_id = get_jwt_identity()

        # Log logout
        db_service.log_usage(
            user_id=user_id,
            action_type="logout",
            metadata={
                "ip_address": request.remote_addr
            },  # Using the correct parameter name
        )

        return jsonify({"success": True, "message": "Logged out successfully"})

    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({"success": False, "error": "Logout failed"}), 500


# Episode Chat Endpoints
@app.route("/api/episodes/chat/start", methods=["POST"])
@jwt_required()
@cross_origin()
# @limiter.limit("10 per minute")
@validate_json("url")
def start_episode_chat():
    """Start a chat session with a single episode"""
    try:
        user_id = get_jwt_identity()
        data = g.request_data
        episode_url = data["url"]

        # Validate URL format
        if not episode_url.startswith(("http://", "https://")):
            return jsonify({"success": False, "error": "Invalid URL format"}), 400

        if len(episode_url) > 2000:
            return jsonify({"success": False, "error": "URL too long"}), 400

        # Create temporary episode
        episode = episode_manager.create_temporary_episode(episode_url)
        if not episode:
            return jsonify({"success": False, "error": "Failed to create episode"}), 500

        # Process episode (simulate for now)
        success = episode_manager.process_episode_with_product_a(episode.id)
        if not success:
            logger.warning(f"Episode processing failed for {episode.id}")

        # Create chat session
        session_data = chat_manager.create_episode_session(user_id, episode.id)
        if not session_data:
            return (
                jsonify({"success": False, "error": "Failed to create chat session"}),
                500,
            )

        # Log usage
        db_service.log_usage(
            user_id=user_id,
            action_type="episode_chat_start",
            session_id=session_data["session_id"],
            metadata={"episode_url": episode_url},  # Using the correct parameter name
        )

        return jsonify(
            {
                "success": True,
                "session_id": session_data["session_id"],
                "episode": session_data["episode"],
            }
        )

    except Exception as e:
        logger.error(f"Start episode chat error: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@app.route("/api/chat/<session_id>/message", methods=["POST"])
@jwt_required()
@cross_origin()
# @limiter.limit("30 per minute")
@validate_json("message")
def send_chat_message(session_id):
    """Send a message in a chat session"""
    try:
        user_id = get_jwt_identity()
        data = g.request_data
        message = data["message"]

        # Validate session ownership
        session_data = chat_manager.get_session(session_id)
        if not session_data or session_data.get("user_id") != user_id:
            return (
                jsonify(
                    {"success": False, "error": "Session not found or access denied"}
                ),
                404,
            )

        # Validate message
        if len(message) > 2000:
            return jsonify({"success": False, "error": "Message too long"}), 400

        # Add user message
        chat_manager.add_message(session_id, "user", message)

        # Generate AI response
        response = chat_manager.generate_response(session_id, message)

        # Add AI response
        chat_manager.add_message(session_id, "assistant", response)

        # Log usage
        db_service.log_usage(
            user_id=user_id,
            action_type="chat_message",
            session_id=session_id,
            metadata={
                "message_length": len(message),
                "response_length": len(response),
            },  # Using the correct parameter name
        )

        return jsonify({"success": True, "response": response})

    except Exception as e:
        logger.error(f"Send chat message error: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


# Expert Management Endpoints
@app.route("/api/experts", methods=["GET"])
@jwt_required()
@cross_origin()
def get_experts():
    """Get all experts for the current user"""
    try:
        user_id = get_jwt_identity()
        experts = episode_manager.get_user_experts(user_id)

        experts_data = []
        for expert in experts:
            experts_data.append(
                {
                    "id": expert.id,
                    "name": expert.name,
                    "description": expert.description,
                    "episode_count": len(expert.episodes),
                    "created_at": (
                        expert.created_at.isoformat() if expert.created_at else None
                    ),
                    "updated_at": (
                        expert.updated_at.isoformat() if expert.updated_at else None
                    ),
                }
            )

        return jsonify({"success": True, "experts": experts_data})

    except Exception as e:
        logger.error(f"Get experts error: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@app.route("/api/experts", methods=["POST"])
@jwt_required()
@cross_origin()
# @limiter.limit("5 per hour")  # Limit expert creation
@validate_json("name", "episode_urls")
def create_expert():
    """Create a new expert"""
    try:
        user_id = get_jwt_identity()
        data = g.request_data

        name = data["name"]
        description = data.get("description", "")
        episode_urls = data["episode_urls"]

        # Validation
        if len(name) < 3 or len(name) > 100:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Name must be between 3 and 100 characters",
                    }
                ),
                400,
            )

        if len(description) > 500:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Description must be less than 500 characters",
                    }
                ),
                400,
            )

        if not isinstance(episode_urls, list) or len(episode_urls) == 0:
            return (
                jsonify(
                    {"success": False, "error": "At least one episode URL is required"}
                ),
                400,
            )

        if len(episode_urls) > 50:  # Limit number of episodes
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Maximum 50 episodes allowed per expert",
                    }
                ),
                400,
            )

        # Validate URLs
        for url in episode_urls:
            if not isinstance(url, str) or not url.startswith(("http://", "https://")):
                return jsonify({"success": False, "error": "Invalid URL format"}), 400
            if len(url) > 2000:
                return jsonify({"success": False, "error": "URL too long"}), 400

        expert = episode_manager.create_expert(user_id, name, description, episode_urls)
        if not expert:
            return jsonify({"success": False, "error": "Failed to create expert"}), 500

        # Log usage
        db_service.log_usage(
            user_id=user_id,
            action_type="expert_creation",
            metadata={
                "expert_name": name,
                "episode_count": len(episode_urls),
            },  # Using the correct parameter name
        )

        return jsonify(
            {
                "success": True,
                "expert": {
                    "id": expert.id,
                    "name": expert.name,
                    "description": expert.description,
                    "episode_count": len(expert.episodes),
                    "created_at": expert.created_at.isoformat(),
                    "updated_at": expert.updated_at.isoformat(),
                },
            }
        )

    except Exception as e:
        logger.error(f"Create expert error: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@app.route("/api/experts/<expert_id>/chat/start", methods=["POST"])
@jwt_required()
@cross_origin()
# @limiter.limit("20 per minute")
def start_expert_chat(expert_id):
    """Start a chat session with an expert"""
    try:
        user_id = get_jwt_identity()

        # Validate expert ownership
        expert = episode_manager.get_expert(expert_id)
        if not expert or expert.user_id != user_id:
            return (
                jsonify(
                    {"success": False, "error": "Expert not found or access denied"}
                ),
                404,
            )

        session_data = chat_manager.create_expert_session(user_id, expert_id)
        if not session_data:
            return (
                jsonify({"success": False, "error": "Failed to create chat session"}),
                500,
            )

        # Log usage
        db_service.log_usage(
            user_id=user_id,
            action_type="expert_chat_start",
            session_id=session_data["session_id"],
            metadata={
                "expert_id": expert_id,
                "expert_name": expert.name,
            },  # Using the correct parameter name
        )

        return jsonify(
            {
                "success": True,
                "session_id": session_data["session_id"],
                "expert": session_data["expert"],
            }
        )

    except Exception as e:
        logger.error(f"Start expert chat error: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@app.route("/api/experts/<expert_id>", methods=["DELETE"])
@jwt_required()
@cross_origin()
def delete_expert(expert_id):
    """Delete an expert"""
    try:
        user_id = get_jwt_identity()
        success = episode_manager.delete_expert(expert_id, user_id)

        if not success:
            return (
                jsonify(
                    {"success": False, "error": "Expert not found or access denied"}
                ),
                404,
            )

        # Log usage
        db_service.log_usage(
            user_id=user_id,
            action_type="expert_deletion",
            metadata={"expert_id": expert_id},  # Using the correct parameter name
        )

        return jsonify({"success": True, "message": "Expert deleted successfully"})

    except Exception as e:
        logger.error(f"Delete expert error: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@app.route("/api/health")
@cross_origin()
def health():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "message": "Podcast Chatbot API is running",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"success": False, "error": "Method not allowed"}), 405


@app.errorhandler(429)
def ratelimit_handler(e):
    return (
        jsonify(
            {"success": False, "error": "Rate limit exceeded. Please try again later."}
        ),
        429,
    )


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"success": False, "error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_ENV") == "development")
