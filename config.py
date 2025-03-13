import os

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv(override=True)

# GENERAL CONFIG
DEBUG = True  # Debug mode flag
MAX_TOKENS = 20_000  # Max tokens for chat history to prevent exceeding the model's context window
DATA_FOLDERS = ["podcasts", "bitwise_articles"]  # Folders where data is stored
EMBEDDINGS_MODEL = "text-embedding-3-large"  # Embeddings model for vector retrieval -> Alternative: "text-embedding-ada-002"
EMBEDDINGS_VECTOR_LENGTH = 3072  # This is value for `text-embedding-3-large` model. For `text-embedding-ada-002` is 1536.

# OPENAI CONFIG
OPEN_AI_MODEL = "gpt-4o-mini"  # OpenAI model configuration
OPEN_AI_MODEL_TEMPERATURE = 1  # OpenAI model configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # OpenAI API key

# FAISS CONFIG
FAISS_INDEX_NAME = "faiss_index"  # FAISS index path for vector storage

# PINECONE CONFIG
PINECONE_CLOUD = "aws"
PINECONE_METRIC = "cosine"
PINECONE_REGION = "us-east-1"
PINECONE_NAMESPACE = "podcaster"
PINECONE_INDEX_NAME = "pinecone-index"  # Pinecone index path for vector storage
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")  # Pinecone API key

# Initialize OpenAI embeddings with the selected model and API key
EMBEDDINGS_MODEL = OpenAIEmbeddings(
    model=EMBEDDINGS_MODEL, openai_api_key=OPENAI_API_KEY
)
