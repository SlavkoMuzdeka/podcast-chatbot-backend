import logging

from typing import Dict
from flask import jsonify
from services.db_service import DatabaseService

logger = logging.getLogger(__name__)


class UserManager:
    def __init__(self, db_service: DatabaseService):
        """Initialize episode manager with Pinecone and Database"""
        self.db_service = db_service

    def get_user_stats(self, user_id: str) -> Dict:
        """Get dashboard statistics for a user"""
        stats = self.db_service.get_user_stats(user_id)
        return jsonify({"success": True, "data": {"stats": stats}}), 200
