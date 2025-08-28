import os

from dotenv import load_dotenv

load_dotenv(override=True)


class MyConfig:
    """Base configuration class"""

    # Flask Configuration
    FLASK_ENVIRONMENT = os.getenv("FLASK_ENV")
    DEBUG = FLASK_ENVIRONMENT == "development"

    # CORS Configuration
    CORS_ORIGIN = os.getenv("FRONTEND_URL")

    # Database Configuration
    SEED_DB = os.getenv("SEED_DB") == "True"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.7))
    OPENAI_EMBEDDINGS_MODEL = os.getenv(
        "OPENAI_EMBEDDINGS_MODEL", "text-embedding-3-large"
    )

    # Pinecone Configuration
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
    PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "podcast-chatbot")
    PINECONE_DIMENSION = int(os.getenv("PINECONE_DIMENSION", 3072))
    PINECONE_METRIC = os.getenv("PINECONE_METRIC", "cosine")

    # Authentication (Simple auth for demo)
    DEFAULT_DB_USERNAME = os.getenv("DEFAULT_DB_USERNAME")
    DEFAULT_DB_PASSWORD = os.getenv("DEFAULT_DB_PASSWORD")
    DEFAULT_DB_EMAIL = os.getenv("DEFAULT_DB_EMAIL")

    # Security Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
