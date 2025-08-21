import os
import logging

from app import create_app
from dotenv import load_dotenv
from database.db_models import db, User
from werkzeug.security import generate_password_hash


load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s"
)
logger = logging.getLogger("init_db")


def init_database():
    """Create tables (if missing) and seed default admin user."""
    app = create_app()

    admin_username = os.getenv("DEFAULT_DB_USERNAME")
    admin_password = os.getenv("DEFAULT_DB_PASSWORD")
    admin_email = os.getenv("DEFAULT_DB_EMAIL")

    with app.app_context():

        try:
            logger.info("Checking for default admin user...")
            existing = (
                db.session.query(User).filter(User.username == admin_username).first()
            )

            if existing:
                logger.info(
                    f"Admin user '{admin_username}' already exists. Skipping creation."
                )
            else:
                logger.info(f"Creating admin user '{admin_username}' ...")
                admin_user = User(
                    username=admin_username,
                    email=admin_email,
                    password_hash=generate_password_hash(admin_password),
                    full_name="System Administrator",
                    is_active=True,
                )
                db.session.add(admin_user)
                db.session.commit()
                logger.info(f"Admin user created: {admin_username}")

            logger.info("Database initialization finished successfully.")
        except Exception as e:
            logger.exception(f"Error while creating tables or seeding DB: {e}")
            db.session.rollback()
            raise


if __name__ == "__main__":
    init_database()
