import logging

from typing import Dict
from flask import jsonify
from services.db_service import DatabaseService

logger = logging.getLogger(__name__)


class UserManager:
    """Manages user-related operations and statistics.
    
    This class handles operations related to user management, including retrieving
    user statistics and other user-specific data.
    """
    
    def __init__(self, db_service: DatabaseService):
        """Initialize the UserManager with required services.
        
        Args:
            db_service: Service for database operations
        """
        self.db_service = db_service

    def get_user_stats(self, user_id: str) -> tuple:
        """Retrieve dashboard statistics for a specific user.
        
        This method fetches various statistics related to the user's activity,
        such as the number of experts created, total episodes, and other relevant metrics.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            tuple: (JSON response, HTTP status code)
                On success: {"success": True, "data": {"stats": dict}} with status 200
                The stats dictionary contains various user-specific metrics
        """
        stats = self.db_service.get_user_stats(user_id)
        return jsonify({"success": True, "data": {"stats": stats}}), 200
