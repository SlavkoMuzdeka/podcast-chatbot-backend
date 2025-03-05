import os

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()

TOP_K_RESULTS = 4  # This is a default value
DATA_FOLDER = "podcasts"
OPEN_AI_MODEL = "gpt-4o-mini"
DB_FAISS_PATH = "faiss_index"
OPEN_AI_MODEL_TEMPERATURE = 0.5
EMBEDDINGS_MODEL = "text-embedding-ada-002"  # text-embedding-3-large
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key")
EMBEDDINGS_MODEL = OpenAIEmbeddings(
    model=EMBEDDINGS_MODEL, openai_api_key=OPENAI_API_KEY
)
