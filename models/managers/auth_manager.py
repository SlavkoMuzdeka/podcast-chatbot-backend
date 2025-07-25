import logging

from typing import Optional, Dict, Any
from services.database_service import db_service
from flask_jwt_extended import create_access_token

logger = logging.getLogger(__name__)


class AuthManager:
    def __init__(self):
        """Initialize JWT authentication manager with database"""
        pass

    def authenticate_user(
        self, username: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user with database credentials"""
        try:
            user = db_service.authenticate_user(username, password)
            if user:
                return {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": "admin" if user.is_admin else "user",
                    "is_active": user.is_active,
                }
            return None

        except Exception as e:
            logger.error(f"Error authenticating user {username}: {str(e)}")
            return None

    def create_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT token for authenticated user"""
        try:
            # Include user info in token
            token_data = {
                "user_id": user_data["id"],
                "username": user_data["username"],
                "role": user_data["role"],
            }
            return create_access_token(
                identity=user_data["id"], additional_claims=token_data
            )

        except Exception as e:
            logger.error(f"Error creating token: {str(e)}")
            return ""

    def register_user(
        self, username: str, password: str, email: str = None, full_name: str = None
    ) -> Optional[Dict[str, Any]]:
        """Register a new user"""
        try:
            user = db_service.create_user(
                username=username, password=password, email=email, full_name=full_name
            )

            if user:
                return {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": "admin" if user.is_admin else "user",
                    "is_active": user.is_active,
                }
            return None

        except Exception as e:
            logger.error(f"Error registering user {username}: {str(e)}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            user = db_service.get_user_by_id(user_id)
            if user:
                return {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": "admin" if user.is_admin else "user",
                    "is_active": user.is_active,
                }
            return None

        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {str(e)}")
            return None
