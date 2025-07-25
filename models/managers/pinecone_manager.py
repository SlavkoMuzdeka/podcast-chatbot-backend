import os
import logging

from datetime import datetime
from dotenv import load_dotenv
from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv(override=True)
logger = logging.getLogger(__name__)


class PineconeManager:
    """Manager for Pinecone vector database operations"""

    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY", ""))
        self.index_name = os.getenv("PINECONE_INDEX", "podcast-chatbot")
        self.embeddings = OpenAIEmbeddings(
            model=os.getenv("OPENAI_EMBEDDINGS_MODEL", "text-embedding-3-large"),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=100, separators=["\n\n", "\n", ". ", " ", ""]
        )
        self._ensure_index_exists()

    def _ensure_index_exists(self):
        """Ensure the Pinecone index exists"""
        try:
            if self.index_name not in self.pc.list_indexes().names():
                logger.info(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=3072,  # text-embedding-3-large dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud=os.getenv("PINECONE_CLOUD", "aws"),
                        region=os.getenv("PINECONE_REGION", "us-east-1"),
                    ),
                )
                logger.info(f"Successfully created index: {self.index_name}")
        except Exception as e:
            logger.error(f"Error ensuring index exists: {str(e)}")
            raise

    def store_episode_content(
        self,
        episode_id: str,
        namespace: str,
        transcript: str,
        summary: str,
        metadata: Dict[str, Any],
    ) -> bool:
        """
        Store episode content in Pinecone

        Args:
            episode_id: Unique identifier for the episode
            namespace: Pinecone namespace (for expert or temporary storage)
            transcript: Episode transcript
            summary: Episode summary
            metadata: Additional metadata

        Returns:
            bool: Success status
        """
        try:
            index = self.pc.Index(self.index_name)

            # Combine transcript and summary for better context
            full_content = f"Summary: {summary}\n\nTranscript: {transcript}"

            # Split content into chunks
            chunks = self.text_splitter.split_text(full_content)

            # Generate embeddings
            embeddings = self.embeddings.embed_documents(chunks)

            # Prepare vectors for upsert
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = f"{episode_id}_chunk_{i}"
                vector_metadata = {
                    "episode_id": episode_id,
                    "chunk_index": i,
                    "text": chunk,
                    "content_type": "episode_content",
                    "created_at": datetime.now().isoformat(),
                    **metadata,
                }
                vectors.append(
                    {"id": vector_id, "values": embedding, "metadata": vector_metadata}
                )

            # Upsert vectors to Pinecone
            index.upsert(vectors=vectors, namespace=namespace)

            logger.info(
                f"Successfully stored {len(vectors)} chunks for episode {episode_id} in namespace {namespace}"
            )
            return True

        except Exception as e:
            logger.error(f"Error storing episode content: {str(e)}")
            return False

    def query_knowledge(
        self, query: str, namespace: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query the knowledge base for relevant content

        Args:
            query: Search query
            namespace: Pinecone namespace to search in
            top_k: Number of results to return

        Returns:
            List of relevant content chunks
        """
        try:
            index = self.pc.Index(self.index_name)

            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)

            # Search Pinecone
            results = index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=namespace,
            )

            # Extract and format results
            relevant_chunks = []
            for match in results.matches:
                relevant_chunks.append(
                    {
                        "text": match.metadata.get("text", ""),
                        "score": match.score,
                        "episode_id": match.metadata.get("episode_id", ""),
                        "metadata": match.metadata,
                    }
                )

            logger.info(
                f"Found {len(relevant_chunks)} relevant chunks for query in namespace {namespace}"
            )
            return relevant_chunks

        except Exception as e:
            logger.error(f"Error querying knowledge base: {str(e)}")
            return []

    def delete_episode_content(self, episode_id: str, namespace: str) -> bool:
        """
        Delete all content for a specific episode

        Args:
            episode_id: Episode identifier
            namespace: Pinecone namespace

        Returns:
            bool: Success status
        """
        try:
            index = self.pc.Index(self.index_name)

            # Query to find all vectors for this episode
            results = index.query(
                vector=[0] * 3072,  # Dummy vector for metadata filtering
                top_k=10000,  # Large number to get all chunks
                include_metadata=True,
                namespace=namespace,
                filter={"episode_id": episode_id},
            )

            # Extract vector IDs
            vector_ids = [match.id for match in results.matches]

            if vector_ids:
                # Delete vectors
                index.delete(ids=vector_ids, namespace=namespace)
                logger.info(
                    f"Deleted {len(vector_ids)} vectors for episode {episode_id}"
                )

            return True

        except Exception as e:
            logger.error(f"Error deleting episode content: {str(e)}")
            return False

    def delete_namespace(self, namespace: str) -> bool:
        """
        Delete an entire namespace (expert)

        Args:
            namespace: Namespace to delete

        Returns:
            bool: Success status
        """
        try:
            index = self.pc.Index(self.index_name)
            index.delete(delete_all=True, namespace=namespace)
            logger.info(f"Deleted namespace: {namespace}")
            return True

        except Exception as e:
            logger.error(f"Error deleting namespace {namespace}: {str(e)}")
            return False
