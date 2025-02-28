import os
from dotenv import load_dotenv

load_dotenv()

TOP_K_RESULTS = 3
DATA_FOLDER = "podcasts"
FAISS_INDEX_PATH = "faiss_index_pom"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key")
