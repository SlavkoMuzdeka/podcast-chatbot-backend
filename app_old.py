import logging

from dotenv import load_dotenv

load_dotenv(override=True)

from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

from database.managers.auth_manager import AuthManager
from database.managers.episode_manager import EpisodeManager
from database.managers.chat_manager import ChatManager

from flask_jwt_extended import jwt_required

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

# Initialize managers
auth_manager = AuthManager()
episode_manager = EpisodeManager()
chat_manager = ChatManager()


@app.route("/api/auth/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        print(f"DATA IS: {data}")
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return (
                jsonify(
                    {"success": False, "error": "Username and password are required"}
                ),
                400,
            )

        user = auth_manager.authenticate_user(username, password)
        if user:
            token = auth_manager.generate_token(user.id)
            return jsonify(
                {
                    "success": True,
                    "user": {
                        "id": str(user.id),
                        "username": user.username,
                        "email": user.email,
                        "full_name": user.full_name,
                        "role": user.role,
                    },
                    "token": token,
                }
            )
        else:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401

    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        return jsonify({"success": False, "error": "Login failed"}), 500


@app.route("/api/experts", methods=["GET"])
@jwt_required
def get_experts():
    try:
        user_id = request.user_id
        experts = episode_manager.get_user_experts(user_id)

        experts_data = []
        for expert in experts:
            experts_data.append(
                {
                    "id": expert.id,
                    "name": expert.name,
                    "description": expert.description,
                    "episode_count": (
                        len(expert.episodes) if hasattr(expert, "episodes") else 0
                    ),
                    "created_at": (
                        expert.created_at.isoformat()
                        if expert.created_at
                        else datetime.utcnow().isoformat()
                    ),
                    "updated_at": (
                        expert.updated_at.isoformat()
                        if expert.updated_at
                        else datetime.utcnow().isoformat()
                    ),
                    "namespace": expert.namespace,
                    "processing_status": "completed",
                }
            )

        return jsonify({"success": True, "experts": experts_data})

    except Exception as e:
        logger.error(f"Failed to fetch experts: {str(e)}")
        return jsonify({"success": False, "error": "Failed to fetch experts"}), 500


@app.route("/api/experts", methods=["POST"])
@jwt_required
def create_expert():
    try:
        user_id = request.user_id
        data = request.get_json()

        name = data.get("name", "").strip()
        description = data.get("description", "").strip()
        episodes = data.get("episodes", [])

        if not name:
            return jsonify({"success": False, "error": "Expert name is required"}), 400

        if not description:
            return (
                jsonify({"success": False, "error": "Expert description is required"}),
                400,
            )

        if not episodes:
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

        if not valid_episodes:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "At least one episode with title and content is required",
                    }
                ),
                400,
            )

        expert = episode_manager.create_expert_with_content(
            user_id=user_id, name=name, description=description, episodes=valid_episodes
        )

        if expert:
            return jsonify(
                {
                    "success": True,
                    "expert": {
                        "id": expert.id,
                        "name": expert.name,
                        "description": expert.description,
                        "namespace": expert.namespace,
                    },
                }
            )
        else:
            return jsonify({"success": False, "error": "Failed to create expert"}), 500

    except Exception as e:
        logger.error(f"Failed to create expert: {str(e)}")
        return jsonify({"success": False, "error": "Failed to create expert"}), 500


@app.route("/api/experts/<expert_id>/episodes", methods=["POST"])
@jwt_required
def add_episode_to_expert(expert_id):
    try:
        data = request.get_json()
        title = data.get("title", "").strip()
        content = data.get("content", "").strip()

        if not title:
            return (
                jsonify({"success": False, "error": "Episode title is required"}),
                400,
            )

        if not content:
            return (
                jsonify({"success": False, "error": "Episode content is required"}),
                400,
            )

        success = episode_manager.add_episode_content(expert_id, title, content)

        if success:
            return jsonify({"success": True, "message": "Episode added successfully"})
        else:
            return jsonify({"success": False, "error": "Failed to add episode"}), 500

    except Exception as e:
        logger.error(f"Failed to add episode: {str(e)}")
        return jsonify({"success": False, "error": "Failed to add episode"}), 500


@app.route("/api/experts/<expert_id>", methods=["DELETE"])
@jwt_required
def delete_expert(expert_id):
    try:
        user_id = request.user_id
        success = episode_manager.delete_expert(expert_id, user_id)

        if success:
            return jsonify({"success": True, "message": "Expert deleted successfully"})
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Failed to delete expert or expert not found",
                    }
                ),
                404,
            )

    except Exception as e:
        logger.error(f"Failed to delete expert: {str(e)}")
        return jsonify({"success": False, "error": "Failed to delete expert"}), 500


@app.route("/api/experts/<expert_id>/chat/start", methods=["POST"])
@jwt_required
def start_expert_chat(expert_id):
    try:
        user_id = request.user_id

        # Get expert details
        expert = episode_manager.get_expert(expert_id)
        if not expert or expert.user_id != user_id:
            return jsonify({"success": False, "error": "Expert not found"}), 404

        # Create chat session
        session_id = chat_manager.create_chat_session(user_id, expert_id)

        return jsonify(
            {
                "success": True,
                "session_id": session_id,
                "expert": {
                    "id": expert.id,
                    "name": expert.name,
                    "description": expert.description,
                    "episode_count": len(expert.episodes),
                    "namespace": expert.namespace,
                },
            }
        )

    except Exception as e:
        logger.error(f"Failed to start chat: {str(e)}")
        return jsonify({"success": False, "error": "Failed to start chat"}), 500


@app.route("/api/experts/<expert_id>/chat", methods=["POST"])
@jwt_required
def chat_with_expert(expert_id):
    try:
        user_id = request.user_id
        data = request.get_json()

        message = data.get("message", "").strip()
        session_id = data.get("session_id")

        if not message:
            return jsonify({"success": False, "error": "Message is required"}), 400

        if not session_id:
            return jsonify({"success": False, "error": "Session ID is required"}), 400

        # Get expert
        expert = episode_manager.get_expert(expert_id)
        if not expert or expert.user_id != user_id:
            return jsonify({"success": False, "error": "Expert not found"}), 404

        # Generate response
        response = chat_manager.generate_response(
            session_id=session_id,
            expert_id=expert_id,
            namespace=expert.namespace,
            message=message,
        )

        if response:
            return jsonify({"success": True, "response": response})
        else:
            return (
                jsonify({"success": False, "error": "Failed to generate response"}),
                500,
            )

    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        return jsonify({"success": False, "error": "Chat failed"}), 500


@app.route("/api/dashboard/stats", methods=["GET"])
@jwt_required
def get_dashboard_stats():
    try:
        user_id = request.user_id
        experts = episode_manager.get_user_experts(user_id)

        total_experts = len(experts)
        total_episodes = sum(
            len(expert.episodes) if hasattr(expert, "episodes") else 0
            for expert in experts
        )
        total_chats = chat_manager.get_user_chat_count(user_id)
        recent_activity = chat_manager.get_recent_activity_count(user_id, days=7)

        return jsonify(
            {
                "success": True,
                "stats": {
                    "total_experts": total_experts,
                    "total_episodes": total_episodes,
                    "total_chats": total_chats,
                    "recent_activity": recent_activity,
                },
            }
        )

    except Exception as e:
        logger.error(f"Failed to fetch dashboard stats: {str(e)}")
        return (
            jsonify({"success": False, "error": "Failed to fetch dashboard stats"}),
            500,
        )


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


if __name__ == "__main__":
    app.run()
