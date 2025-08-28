import logging

from config import MyConfig
from flask_cors import CORS
from datetime import datetime
from seed_db import init_database
from database.db_models import db
from routes.auth_routes import auth_bp
from utils.app_utils import setup_logging
from routes.expert_routes import expert_bp
from managers.auth_manager import AuthManager
from flask import Flask, app, request, jsonify
from services.db_service import DatabaseService
from managers.expert_manager import ExpertManager
from managers.episode_manager import EpisodeManager
from services.pinecone_service import PineconeService
from sqlalchemy_utils import database_exists, create_database


def create_app():
    """Application factory pattern"""
    app = Flask(__name__)

    # Configuration
    app_config = MyConfig()
    app.config.from_object(app_config)

    # Setup logging
    setup_logging(app_config)
    logger = logging.getLogger(__name__)

    # Setup CORS
    CORS(app, resources={r"/api/*": {"origins": app_config.CORS_ORIGIN}})

    # Initialize database
    db.init_app(app)

    # Initialize services
    db_service = DatabaseService(db)
    pinecone_service = PineconeService(app_config)

    auth_manager = AuthManager(db_service, app_config)
    expert_manager = ExpertManager(db_service, pinecone_service)
    episode_manager = EpisodeManager(db_service, pinecone_service)

    # Store services in app context
    app.auth_manager = auth_manager
    app.expert_manager = expert_manager
    app.episode_manager = episode_manager

    # Create tables and demo data
    with app.app_context():
        if not database_exists(db.engine.url):
            create_database(db.engine.url)
            logger.info(f"Database {db.engine.url.database} created!")

        db.create_all()

        if app_config.SEED_DB:
            init_database()
        logger.info("Database initialized successfully")

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(expert_bp, url_prefix="/api/experts")

    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Health check endpoint"""
        return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

    @app.before_request
    def log_request():
        params = request.args.to_dict()
        if params:
            logger.info(f"Request: {request.method} {request.path} | Params: {params}")
        else:
            logger.info(f"Request: {request.method} {request.path}")

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin and origin == app.config["CORS_ORIGIN"]:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization"
            )
            response.headers["Access-Control-Allow-Methods"] = (
                "OPTIONS, POST, GET, PUT, DELETE"
            )
        return response

    logger.info("Knowledge Hub API initialized successfully")
    return app


app = create_app()

if __name__ == "__main__":

    logger = logging.getLogger(__name__)
    logger.info("Starting Podcast Chatbot server...")
    logger.info("Demo users:")
    logger.info(
        f"  - user: {app.config['DEFAULT_DB_USERNAME']} / password: ({app.config['DEFAULT_DB_PASSWORD']})"
    )
    logger.info("------------------------------------------------------------")
    app.run(debug=app.config["DEBUG"], threaded=True)
