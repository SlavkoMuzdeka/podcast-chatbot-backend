import json
import openai
import logging

from config import MyConfig
from typing import Generator
from database.db_models import Expert
from services.db_service import DatabaseService
from services.pinecone_service import PineconeService
from flask import jsonify, Response, stream_with_context

logger = logging.getLogger(__name__)


class ChatManager:
    def __init__(
        self,
        config: MyConfig,
        db_service: DatabaseService,
        pinecone_service: PineconeService,
    ):
        """Initialize the ChatManager with required services.

        Args:
            config: Application configuration object
            db_service: Service for database operations
            pinecone_service: Service for vector similarity search
        """
        self.config = config
        self.db_service = db_service
        self.pinecone_service = pinecone_service
        self.openai_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)

    def chat_with_expert(self, data: dict) -> tuple:
        """Handle a non-streaming chat request with an expert.

        Args:
            data: Dictionary containing:
                - expertId: ID of the expert to chat with
                - message: User's message

        Returns:
            tuple: (JSON response, HTTP status code)
                  On success: {"success": True, "data": {"response": str, "expertId": str}}
                  On error: {"success": False, "error": str}
        """
        is_valid, resp_mess, resp_status_code = self._validate_request_data(data)

        if not is_valid:
            return jsonify({"success": False, "error": resp_mess}), resp_status_code

        # Generate response using RAG
        response = self._generate_response(
            self.db_service.get_expert_by_id(data["expertId"]), data["message"]
        )

        return (
            jsonify(
                {
                    "success": True,
                    "data": {"response": response, "expertId": data["expertId"]},
                }
            ),
            200,
        )

    def chat_with_expert_stream(self, data: dict) -> Response:
        """Handle a streaming chat request with an expert using Server-Sent Events (SSE).

        Args:
            data: Dictionary containing:
                - expertId: ID of the expert to chat with
                - message: User's message

        Returns:
            Response: Flask Response object with streaming content
                    On success: Stream of tokens in format: data: {'token': str}
                    On error: data: {'error': str}
                    End of stream: data: [DONE]
        """
        is_valid, resp_mess, resp_status_code = self._validate_request_data(data)

        if not is_valid:
            return jsonify({"success": False, "error": resp_mess}), resp_status_code

        message = data["message"]
        expert = self.db_service.get_expert_by_id(data["expertId"])

        def generate():
            try:
                for token in self._generate_response_stream(expert, message):
                    yield f"data: {json.dumps({'token': token})}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"Error in streaming: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            },
        )

    def _get_relevant_context(
        self, expert: Expert, query: str, include_metadata: bool = True
    ) -> str:
        """Retrieve relevant context from Pinecone for the expert.

        Args:
            expert: Expert object containing expert information
            query: User's query to find relevant context for
            include_metadata: Whether to include metadata in the Pinecone query

        Returns:
            str: Formatted context string with relevant information from podcast episodes,
                 or an error message if no relevant context is found
        """
        try:
            namespace = expert.name.lower().replace(" ", "_")

            # Query Pinecone for relevant chunks
            chunks = self.pinecone_service.query_knowledge(
                query=query, namespace=namespace, include_metadata=include_metadata
            )

            if not chunks:
                return "No relevant context found."

            # Filter by relevance score and extract context
            relevant_chunks = []
            for chunk in chunks:
                if chunk.get("score", 0) > self.config.PINECONE_SCORE_THRESHOLD:
                    metadata = chunk.get("metadata", {})
                    chunk_text = metadata["text"]
                    episode_title = metadata["episode_title"]

                    if chunk_text:
                        relevant_chunks.append(f"From '{episode_title}': {chunk_text}")

            if not relevant_chunks:
                return "No highly relevant context found for your question."

            return "\n\n".join(relevant_chunks)

        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return "Error retrieving context from knowledge base."

    def create_system_prompt(self, expert_name: str) -> str:
        """Create a system prompt for the expert.

        Args:
            expert_name: Name of the expert to create the prompt for

        Returns:
            str: Formatted system prompt combining the expert's name with the base system prompt
        """
        return f"You are {expert_name}. {self.config.SYSTEM_PROMPT}"

    def _generate_response(self, expert: Expert, message: str) -> str:
        """Generate a non-streaming response using RAG.

        Args:
            expert: Expert object containing expert information
            message: User's message to generate a response for

        Returns:
            str: Generated response from the AI model
        """
        try:
            # Get relevant context
            context = self._get_relevant_context(expert, message)

            # Create system prompt
            system_prompt = self.create_system_prompt(expert.name)

            # Create user prompt with context
            user_prompt = f"""Context from podcast episodes:
                    {context}

                    User question: {message}

                    Please answer the question based on the provided context."""

            # Generate response
            response = self.openai_client.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.config.OPENAI_TEMPERATURE,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error while processing your request. Please try again."

    def _generate_response_stream(
        self, expert: Expert, message: str
    ) -> Generator[str, None, None]:
        """Generate a streaming response using RAG.

        Args:
            expert: Expert object containing expert information
            message: User's message to generate a response for

        Yields:
            str: Chunks of the generated response
        """
        try:
            # Get relevant context
            context = self._get_relevant_context(expert, message)

            # Create system prompt
            system_prompt = self.create_system_prompt(expert.name)

            # Create user prompt with context
            user_prompt = f"""Context from podcast episodes:
                    {context}

                    User question: {message}

                    Please answer the question based on the provided context."""

            # Generate streaming response
            stream = self.openai_client.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.config.OPENAI_TEMPERATURE,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Error generating streaming response: {str(e)}")
            yield "I apologize, but I encountered an error while processing your request. Please try again."

    def _validate_request_data(self, data: dict) -> tuple[bool, str, int]:
        """Validate the incoming chat request data.

        Args:
            data: Request data to validate

        Returns:
            tuple: (is_valid: bool, error_message: str, status_code: int)
                - is_valid: True if data is valid, False otherwise
                - error_message: Empty string if valid, otherwise describes the error
                - status_code: HTTP status code (400 for bad request, 404 for not found, etc.)
        """
        if not data:
            return False, "No data.", 400

        expert_id = data.get("expertId")
        message = data.get("message")

        if not expert_id:
            return False, "Expert ID is required", 400

        if not message:
            return False, "Message is required", 400

        if not self.db_service.get_expert_by_id(expert_id):
            return False, "Expert not found", 404

        return True, "", 200
