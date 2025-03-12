import os

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()

DEBUG = True  # Debug mode flag
TOP_K_RESULTS = 4  # Number of top search results to retrieve
MAX_TOKENS = 20_000  # Max tokens for chat history to prevent exceeding the model's context window
DATA_FOLDER = "podcasts"  # Folder where podcast data is stored
OPEN_AI_MODEL = "gpt-4o-mini"  # OpenAI model configuration
OPEN_AI_MODEL_TEMPERATURE = 1  # OpenAI model configuration
DB_FAISS_PATH = "faiss_index"  # FAISS index path for vector storage
EMBEDDINGS_MODEL = "text-embedding-ada-002"  # Embeddings model for vector retrieval -> Alternative: "text-embedding-3-large"
OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY", ""
)  # OpenAI API key (fallback value for local testing)

# Initialize OpenAI embeddings with the selected model and API key
EMBEDDINGS_MODEL = OpenAIEmbeddings(
    model=EMBEDDINGS_MODEL, openai_api_key=OPENAI_API_KEY
)
