"""
Database initialization script
Creates tables and inserts initial data
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv(override=True)

from utils.app_utils import setup_logger
from werkzeug.security import generate_password_hash
from models.database import create_tables, SessionLocal, User, SystemConfig


logger = setup_logger()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def init_database():
    """Initialize database with tables and default data"""
    logger.info("🗄️  Creating database tables...")
    create_tables()

    db = SessionLocal()
    try:
        logger.info("👤 Checking for default admin user...")
        admin_username = os.getenv("DEFAULT_DB_USERNAME", "admin")
        admin_password = os.getenv("DEFAULT_DB_PASSWORD", "password123")

        existing_admin = db.query(User).filter(User.username == admin_username).first()
        if not existing_admin:
            admin_user = User(
                username=admin_username,
                email="admin@example.com",
                password_hash=generate_password_hash(admin_password),
                full_name="System Administrator",
                is_admin=True,
                is_active=True,
            )
            db.add(admin_user)
            logger.info(f"✅ Created admin user: {admin_username}")
        else:
            logger.info(f"ℹ️  Admin user already exists: {admin_username}")

        default_configs = [
            {
                "key": "app_name",
                "value": "Podcast Chatbot",
                "description": "Application name",
            },
            {
                "key": "app_version",
                "value": "1.0.0",
                "description": "Application version",
            },
            {
                "key": "max_episodes_per_expert",
                "value": "50",
                "description": "Maximum number of episodes per expert",
            },
            {
                "key": "max_experts_per_user",
                "value": "10",
                "description": "Maximum number of experts per user",
            },
            {
                "key": "episode_processing_timeout",
                "value": "300",
                "description": "Episode processing timeout in seconds",
            },
        ]

        for config_data in default_configs:
            existing_config = (
                db.query(SystemConfig)
                .filter(SystemConfig.key == config_data["key"])
                .first()
            )

            if not existing_config:
                config = SystemConfig(**config_data)
                db.add(config)
                logger.info(f"✅ Created system config: {config_data['key']}")

        db.commit()
        logger.info("🎉 Database initialization completed successfully!")

    except Exception as e:
        logger.error(f"❌ Error initializing database: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
