import os
import logging

from config import MyConfig
from dotenv import load_dotenv
from typing import List, Dict, Any
from database.db_models import Episode
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


load_dotenv(override=True)
logger = logging.getLogger(__name__)


class PineconeService:
    """Service for managing vector database operations with Pinecone.
    
    This class handles all interactions with Pinecone's vector database, including
    creating indexes, storing episode content as vector embeddings, and performing
    similarity searches.
    
    Attributes:
        config: Application configuration object
        pc: Pinecone client instance
        index_name: Name of the Pinecone index
        embeddings: OpenAI embeddings model instance
        text_splitter: Text splitter for chunking content
    """

    def __init__(self, config: MyConfig):
        """Initialize the PineconeService with configuration.
        
        Args:
            config: Application configuration object containing API keys and settings
            
        Initializes the Pinecone client, embeddings model, and ensures the index exists.
        """
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
        """Ensure the Pinecone index exists, create it if it doesn't.
        
        Creates a new serverless Pinecone index with the configured settings
        if it doesn't already exist.
        
        Raises:
            Exception: If there's an error creating the index
        """
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
        """Store episode content as vector embeddings in Pinecone.

        Processes the episode content by splitting it into chunks, generating
        embeddings for each chunk, and storing them in the Pinecone index.

        Args:
            episode: Episode object containing content to be stored
            db_expert_name: Name of the expert (used as Pinecone namespace)

        Returns:
            bool: True if storage was successful, False otherwise
            
        Note:
            The content is split into chunks of 1000 characters with 100 character
            overlap between chunks for better context retention.
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
        self, query: str, namespace: str, include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """Search the knowledge base for content relevant to the query.
        
        Converts the query to an embedding and searches the Pinecone index
        for the most similar content chunks within the specified namespace.

        Args:
            query: The search query string
            namespace: Pinecone namespace to search within
            include_metadata: Whether to include metadata in results (default: True)

        Returns:
            List[Dict[str, Any]]: List of relevant content chunks, each containing:
                - text: The chunk text
                - score: Similarity score (0-1)
                - episode_title: Title of the source episode
                - episode_id: ID of the source episode
                - metadata: Additional metadata
                
        Note:
            The number of results is limited by PINECONE_TOP_K configuration.
        """
        try:
            index = self.pc.Index(self.index_name)

            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)

            # Search Pinecone
            results = index.query(
                vector=query_embedding,
                top_k=self.config.PINECONE_TOP_K,
                include_metadata=include_metadata,
                namespace=namespace,
            )

            # Extract and format results
            relevant_chunks = []
            for match in results.matches:
                relevant_chunks.append(
                    {
                        "text": match.metadata.get("text", ""),
                        "score": match.score,
                        "episode_title": match.metadata.get("episode_title", ""),
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
        """Delete all vector embeddings for a specific episode.
        
        Args:
            episode_id: Unique identifier of the episode to delete
            namespace: Pinecone namespace where the episode is stored
            
        Returns:
            bool: True if deletion was successful, False otherwise
            
        Note:
            This performs a query to find all vectors associated with the episode
            and then deletes them in a batch operation.
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
        """Delete an entire namespace (expert) and all its vectors.
        
        Args:
            namespace: Pinecone namespace to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
            
        Warning:
            This will permanently remove all vectors in the specified namespace.
            Use with caution as this operation cannot be undone.
        """
        try:
            index = self.pc.Index(self.index_name)
            index.delete(delete_all=True, namespace=namespace.lower().replace(" ", "_"))
            logger.info(f"Deleted namespace: {namespace.lower().replace(' ', '_')}")
            return True

        except Exception as e:
            logger.error(f"Error deleting namespace {namespace}: {str(e)}")
            return False
