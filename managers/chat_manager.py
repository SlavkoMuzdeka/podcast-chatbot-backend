import json
import logging

from typing import List, Dict, Any, Optional
from services.db_service import DatabaseService
from managers.pinecone_manager import PineconeManager

logger = logging.getLogger(__name__)


class ChatManager:
    def __init__(self, db_service: DatabaseService, pinecone_manager: PineconeManager):
        """Initialize chat manager with Pinecone and Database integration"""
        self.pinecone_manager = pinecone_manager
        self.db_service = db_service

    # def create_episode_session(
    #     self, user_id: str, episode_id: str
    # ) -> Optional[Dict[str, Any]]:
    #     """Create a chat session for a single episode"""
    #     try:
    #         # Get episode from database
    #         episode = self.db_service.get_episode_by_id(episode_id)
    #         if not episode:
    #             logger.error(
    #                 f"Episode {json.dumps(episode.to_dict(), indent=2)} not found"
    #             )
    #             return None

    #         # Create chat session in database
    #         db_session = db_service.create_chat_session(
    #             user_id=user_id, session_type="episode", episode_id=episode_id
    #         )

    #         if not db_session:
    #             logger.error("Failed to create chat session in database")
    #             return None

    #         # For temporary episodes, use a temporary namespace
    #         temp_namespace = f"temp_{episode_id}"

    #         # Store episode content in temporary namespace if processed
    #         if db_episode.processing_status == "completed" and db_episode.transcript:
    #             metadata = {
    #                 "title": db_episode.title,
    #                 "url": db_episode.url,
    #                 "created_at": (
    #                     db_episode.created_at.isoformat()
    #                     if db_episode.created_at
    #                     else None
    #                 ),
    #             }
    #             self.pinecone_manager.store_episode_content(
    #                 episode_id,
    #                 temp_namespace,
    #                 db_episode.transcript,
    #                 db_episode.summary,
    #                 metadata,
    #             )

    #         session_data = {
    #             "session_id": str(db_session.id),
    #             "type": "episode",
    #             "episode_id": episode_id,
    #             "namespace": temp_namespace,
    #             "episode": {
    #                 "id": str(db_episode.id),
    #                 "title": db_episode.title,
    #                 "url": db_episode.url,
    #                 "processed": db_episode.processing_status == "completed",
    #             },
    #         }

    #         logger.info(f"Created episode chat session: {db_session.id}")
    #         return session_data

    #     except Exception as e:
    #         logger.error(f"Error creating episode session: {str(e)}")
    #         return None

    # def create_expert_session(
    #     self, user_id: str, expert_id: str
    # ) -> Optional[Dict[str, Any]]:
    #     """Create a chat session for an expert"""
    #     try:
    #         # Get expert from database
    #         db_expert = self.db_service.get_expert_by_id(expert_id)
    #         if not db_expert:
    #             logger.error(f"Expert {expert_id} not found")
    #             return None

    #         # Verify user owns this expert
    #         if str(db_expert.user_id) != user_id:
    #             logger.error(f"User {user_id} does not own expert {expert_id}")
    #             return None

    #         # Create chat session in database
    #         db_session = self.db_service.create_chat_session(
    #             user_id=user_id, session_type="expert", expert_id=expert_id
    #         )

    #         if not db_session:
    #             logger.error("Failed to create chat session in database")
    #             return None

    #         session_data = {
    #             "session_id": str(db_session.id),
    #             "type": "expert",
    #             "expert_id": expert_id,
    #             "namespace": db_expert.pinecone_namespace,
    #             "expert": {
    #                 "id": str(db_expert.id),
    #                 "name": db_expert.name,
    #                 "description": db_expert.description,
    #             },
    #         }

    #         logger.info(f"Created expert chat session: {db_session.id}")
    #         return session_data

    #     except Exception as e:
    #         logger.error(f"Error creating expert session: {str(e)}")
    #         return None

    # def add_message(
    #     self, session_id: str, role: str, content: str, metadata: Dict[str, Any] = None
    # ) -> bool:
    #     """Add a message to a chat session"""
    #     try:
    #         # Add message to database
    #         db_message = db_service.add_chat_message(
    #             session_id=session_id,
    #             role=role,
    #             content=content,
    #             message_metadata=metadata,  # Updated parameter name
    #         )

    #         if db_message:
    #             logger.info(f"Added message to session {session_id}")
    #             return True
    #         else:
    #             logger.error(f"Failed to add message to session {session_id}")
    #             return False

    #     except Exception as e:
    #         logger.error(f"Error adding message to session {session_id}: {str(e)}")
    #         return False

    # def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
    #     """Get a chat session"""
    #     try:
    #         db_session = db_service.get_chat_session(session_id)
    #         if not db_session:
    #             return None

    #         session_data = {
    #             "session_id": str(db_session.id),
    #             "type": db_session.session_type,
    #             "user_id": str(db_session.user_id),
    #             "created_at": db_session.created_at.isoformat(),
    #             "updated_at": db_session.updated_at.isoformat(),
    #         }

    #         if db_session.session_type == "episode" and db_session.episode_id:
    #             db_episode = db_service.get_episode_by_id(str(db_session.episode_id))
    #             if db_episode:
    #                 session_data.update(
    #                     {
    #                         "episode_id": str(db_episode.id),
    #                         "namespace": f"temp_{db_episode.id}",
    #                         "episode": {
    #                             "id": str(db_episode.id),
    #                             "title": db_episode.title,
    #                             "url": db_episode.url,
    #                             "processed": db_episode.processing_status
    #                             == "completed",
    #                         },
    #                     }
    #                 )

    #         elif db_session.session_type == "expert" and db_session.expert_id:
    #             db_expert = db_service.get_expert_by_id(str(db_session.expert_id))
    #             if db_expert:
    #                 session_data.update(
    #                     {
    #                         "expert_id": str(db_expert.id),
    #                         "namespace": db_expert.pinecone_namespace,
    #                         "expert": {
    #                             "id": str(db_expert.id),
    #                             "name": db_expert.name,
    #                             "description": db_expert.description,
    #                         },
    #                     }
    #                 )

    #         return session_data

    #     except Exception as e:
    #         logger.error(f"Error getting session {session_id}: {str(e)}")
    #         return None

    # def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
    #     """Get all messages for a chat session"""
    #     try:
    #         db_messages = db_service.get_chat_messages(session_id)
    #         messages = []

    #         for db_message in db_messages:
    #             message = {
    #                 "id": str(db_message.id),
    #                 "role": db_message.role,
    #                 "content": db_message.content,
    #                 "created_at": db_message.created_at.isoformat(),
    #                 "metadata": db_message.message_metadata
    #                 or {},  # Updated column name
    #             }
    #             messages.append(message)

    #         return messages

    #     except Exception as e:
    #         logger.error(f"Error getting messages for session {session_id}: {str(e)}")
    #         return []

    # def get_relevant_context(
    #     self, session_id: str, user_message: str, max_chunks: int = 5
    # ) -> str:
    #     """Get relevant context from Pinecone based on user message"""
    #     try:
    #         session_data = self.get_session(session_id)
    #         if not session_data:
    #             return ""

    #         namespace = session_data.get("namespace", "")
    #         if not namespace:
    #             return ""

    #         # Query Pinecone for relevant content
    #         relevant_chunks = self.pinecone_manager.query_knowledge(
    #             user_message, namespace, top_k=max_chunks
    #         )

    #         if not relevant_chunks:
    #             return ""

    #         # Combine relevant chunks into context
    #         context_parts = []
    #         for chunk in relevant_chunks:
    #             if chunk["score"] > 0.7:  # Only include high-relevance chunks
    #                 context_parts.append(chunk["text"])

    #         return "\n\n".join(context_parts) if context_parts else ""

    #     except Exception as e:
    #         logger.error(f"Error retrieving context for session {session_id}: {str(e)}")
    #         return ""

    # def generate_response(self, session_id: str, user_message: str) -> str:
    #     """Generate AI response using OpenAI with relevant context"""
    #     try:
    #         session_data = self.get_session(session_id)
    #         if not session_data:
    #             return "Session not found."

    #         # Get relevant context from Pinecone
    #         context = self.get_relevant_context(session_id, user_message)

    #         # This is where you would integrate with OpenAI
    #         # For now, returning a mock response with context awareness
    #         if session_data["type"] == "episode":
    #             episode = session_data.get("episode", {})
    #             if context:
    #                 return f"Based on the episode '{episode.get('title', 'Unknown')}', here's what I found relevant to your question '{user_message}': {context[:500]}..."
    #             else:
    #                 return f"I don't have enough context from the episode '{episode.get('title', 'Unknown')}' to answer your question about: {user_message}"
    #         else:
    #             expert = session_data.get("expert", {})
    #             if context:
    #                 return f"As {expert.get('name', 'AI Expert')}, based on my knowledge from the podcast episodes, here's my response to '{user_message}': {context[:500]}..."
    #             else:
    #                 return f"As {expert.get('name', 'AI Expert')}, I don't have specific information about '{user_message}' in my current knowledge base."

    #     except Exception as e:
    #         logger.error(
    #             f"Error generating response for session {session_id}: {str(e)}"
    #         )
    #         return "I'm sorry, I encountered an error while processing your request. Please try again."

    # def get_user_sessions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    #     """Get user's chat sessions"""
    #     try:
    #         db_sessions = db_service.get_user_chat_sessions(user_id, limit)
    #         sessions = []

    #         for db_session in db_sessions:
    #             session_data = {
    #                 "id": str(db_session.id),
    #                 "type": db_session.session_type,
    #                 "title": db_session.title,
    #                 "created_at": db_session.created_at.isoformat(),
    #                 "updated_at": db_session.updated_at.isoformat(),
    #                 "is_active": db_session.is_active,
    #             }

    #             # Add type-specific data
    #             if db_session.session_type == "episode" and db_session.episode:
    #                 session_data["episode"] = {
    #                     "title": db_session.episode.title,
    #                     "url": db_session.episode.url,
    #                 }
    #             elif db_session.session_type == "expert" and db_session.expert:
    #                 session_data["expert"] = {
    #                     "name": db_session.expert.name,
    #                     "description": db_session.expert.description,
    #                 }

    #             sessions.append(session_data)

    #         return sessions

    #     except Exception as e:
    #         logger.error(f"Error getting user sessions: {str(e)}")
    #         return []

    # def cleanup_temporary_session(self, session_id: str) -> bool:
    #     """Clean up temporary session and associated Pinecone data"""
    #     try:
    #         session_data = self.get_session(session_id)
    #         if not session_data:
    #             return False

    #         # If it's a temporary episode session, clean up the namespace
    #         if session_data["type"] == "episode" and session_data.get(
    #             "namespace", ""
    #         ).startswith("temp_"):
    #             self.pinecone_manager.delete_namespace(session_data["namespace"])

    #         logger.info(f"Cleaned up temporary session: {session_id}")
    #         return True

    #     except Exception as e:
    #         logger.error(f"Error cleaning up session {session_id}: {str(e)}")
    #         return False
