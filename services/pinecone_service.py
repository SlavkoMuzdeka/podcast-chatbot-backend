import os
import logging

from datetime import datetime
from dotenv import load_dotenv
from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import MyConfig
from database.db_models import Episode

load_dotenv(override=True)
logger = logging.getLogger(__name__)


class PineconeService:
    """Manager for Pinecone vector database operations"""

    def __init__(self, config: MyConfig):
        self.config = config
        self.pc = Pinecone(api_key=self.config.PINECONE_API_KEY)
        self.index_name = self.config.PINECONE_INDEX_NAME
        self.embeddings = OpenAIEmbeddings(
            model=self.config.OPENAI_EMBEDDINGS_MODEL,
            openai_api_key=self.config.OPENAI_API_KEY,
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
                    dimension=self.config.PINECONE_DIMENSION,
                    metric=self.config.PINECONE_METRIC,
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
        episode: Episode,
        db_expert_name: str,
    ) -> bool:
        """
        Store episode content in Pinecone

        Args:
            episode: Episode object containing all relevant data
            db_expert_name: Name of the expert (for Pinecone)

        Returns:
            bool: Success status
        """
        try:
            index = self.pc.Index(self.index_name)

            # Combine content for better context
            full_content = f"Content: {episode.content}"

            # Split content into chunks
            chunks = self.text_splitter.split_text(full_content)

            # Generate embeddings
            embeddings = self.embeddings.embed_documents(chunks)

            # Prepare vectors for upsert
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = f"{episode.id}_chunk_{i}"
                vector_metadata = {
                    "episode_id": str(episode.id),
                    "episode_title": episode.title,
                    "chunk_index": i,
                    "text": chunk,
                }
                vectors.append(
                    {"id": vector_id, "values": embedding, "metadata": vector_metadata}
                )

            # Upsert vectors to Pinecone
            index.upsert(
                vectors=vectors, namespace=db_expert_name.lower().replace(" ", "_")
            )

            logger.info(
                f"Successfully stored {len(vectors)} chunks for episode {episode.title} in namespace {db_expert_name.lower().replace(' ', '_')}"
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

    def delete_episode(self, episode_id: str, namespace: str) -> bool:
        """
        Delete specified episode

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
                vector=[0] * int(self.config.PINECONE_DIMENSION),
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
            index.delete(delete_all=True, namespace=namespace.lower().replace(" ", "_"))
            logger.info(f"Deleted namespace: {namespace.lower().replace(' ', '_')}")
            return True

        except Exception as e:
            logger.error(f"Error deleting namespace {namespace}: {str(e)}")
            return False
