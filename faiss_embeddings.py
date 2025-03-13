import os
import config

from langchain_community.vectorstores import FAISS

# TODO Test with this one ->
from langchain_core.documents import Document

# TODO Try with this splitter ->
from langchain_text_splitters import RecursiveCharacterTextSplitter

# from langchain.docstore.document import Document
# from langchain.text_splitter import RecursiveCharacterTextSplitter


def main():
    """
    Loads podcast transcripts, splits them into chunks, generates embeddings, and stores them in FAISS.

    - Reads all `.txt` files from the specified data folder.
    - Splits each transcript into smaller chunks for efficient retrieval.
    - Generates embeddings for each chunk using OpenAI's embedding model.
    - Stores the embeddings in a FAISS vector database.
    """
    total_processed = 0
    vector_store = None

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

    for folder in config.DATA_FOLDERS:
        if config.DEBUG:
            print(f"📂 Processing text files from {folder}...")

        for file in os.listdir(folder):
            if file.endswith(".txt"):
                with open(os.path.join(folder, file), "r", encoding="utf-8") as f:
                    text = f.read()

                    chunks = splitter.split_text(text)
                    documents = splitter.create_documents(chunks)

                    if vector_store is None:
                        vector_store = FAISS.from_documents(
                            documents, config.EMBEDDINGS_MODEL
                        )
                    else:
                        vector_store.add_documents(documents)

                    total_processed += 1

                    if config.DEBUG:
                        print(
                            f"✅ Processed {file}. Total processed: {total_processed}"
                        )

    # Store embeddings in FAISS
    if vector_store:
        vector_store.save_local(config.FAISS_INDEX_NAME)

        if config.DEBUG:
            print(f"✅ FAISS index saved at {config.FAISS_INDEX_NAME}")
    else:
        print("⚠️ No valid documents found to index.")


if __name__ == "__main__":
    main()
