import os
import config

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


def create_embeddings():
    """Loads podcast transcripts, generates embeddings in smaller batches, and stores them in FAISS."""
    embedding_model = OpenAIEmbeddings(
        model="text-embedding-ada-002", openai_api_key=config.OPENAI_API_KEY
    )
    # text-embedding-3-large
    # text-embedding-ada-002

    all_embeddings = []
    total_processed = 0

    for file in os.listdir(config.DATA_FOLDER):
        if file.endswith(".txt"):
            with open(
                os.path.join(config.DATA_FOLDER, file), "r", encoding="utf-8"
            ) as f:
                text = f.read()
                batch_embeddings = embedding_model.embed_documents([text])
                all_embeddings.extend(zip(text, batch_embeddings[0]))
                total_processed += 1
                print(f"Processed {total_processed} files")

    # Store embeddings in FAISS
    vector_store = FAISS.from_embeddings(all_embeddings, embedding_model)
    vector_store.save_local(config.FAISS_INDEX_PATH)
    print(f"✅ FAISS index saved at {config.FAISS_INDEX_PATH}")


def load_embeddings():
    """Loads the FAISS index and returns a retriever."""
    embedding_model = OpenAIEmbeddings(
        model="text-embedding-ada-002", openai_api_key=config.OPENAI_API_KEY
    )
    vector_store = FAISS.load_local(
        config.FAISS_INDEX_PATH, embedding_model, allow_dangerous_deserialization=True
    )
    return vector_store.as_retriever(search_kwargs={"k": config.TOP_K_RESULTS})
