import jwt
import logging

from config import MyConfig
from database.db_models import User
from typing import Optional, Dict, Any
from services.db_service import DatabaseService
from werkzeug.security import check_password_hash
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class AuthManager:
    def __init__(self, db_service: DatabaseService, config: MyConfig):
        self.config = config
        self.db_service = db_service

    def authenticate_user(
        self, username: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user with database credentials"""
        try:
            user = self.db_service.get_user_by_username(username)

            if not user or not check_password_hash(user.password_hash, password):
                logger.warning(f"Failed login attempt: {username}")
                return {
                    "success": False,
                    "error": "Invalid username or password. Please try again.",
                }

            if not user.is_active:
                return {"success": False, "error": "Account is deactivated"}

            # Update last login
            user.last_login = datetime.now(timezone.utc)
            self.db_service.db.session.commit()

            # Generate JWT tokens
            tokens = self.generate_token(user)

            logger.info(f"User authenticated: {user.email}")

            return {
                "success": True,
                "data": {"user": user.to_dict(), "tokens": tokens},
            }

        except Exception as e:
            logger.error(f"Error authenticating user {username}: {str(e)}")
            return {"success": False, "error": "Internal server error"}

    def generate_token(self, user: User) -> str:
        """Create JWT token for authenticated user"""
        try:
            access_payload = {
                "user_id": str(user.id),
                "email": user.email,
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
                "iat": datetime.now(timezone.utc),
                "type": "access",
            }

            access_token = jwt.encode(
                access_payload, self.config.JWT_SECRET_KEY, algorithm="HS256"
            )
            return {"access_token": access_token}

        except Exception as e:
            logger.error(f"Error creating token: {str(e)}")
            raise

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token, self.config.JWT_SECRET_KEY, algorithms=["HS256"]
            )

            if payload.get("type") != "access":
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            return None
