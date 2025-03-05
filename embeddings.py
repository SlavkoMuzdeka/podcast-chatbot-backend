import os
import config

from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter


def main():
    """Loads podcast transcripts, splits them into chunks, generates embeddings, and stores them in FAISS."""
    total_processed = 0
    vector_store = None

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

    for file in os.listdir(config.DATA_FOLDER):
        if file.endswith(".txt"):
            with open(
                os.path.join(config.DATA_FOLDER, file), "r", encoding="utf-8"
            ) as f:
                text = f.read()

                # Split into chunks
                chunks = splitter.split_text(text)
                documents = [Document(page_content=chunk) for chunk in chunks]

                if vector_store is None:
                    vector_store = FAISS.from_documents(
                        documents, config.EMBEDDINGS_MODEL
                    )
                else:
                    vector_store.add_documents(documents)

                total_processed += 1
                print(f"✅ Processed {file}. Total processed: {total_processed}")

    # Store embeddings in FAISS
    if vector_store:
        vector_store.save_local(config.DB_FAISS_PATH)
        print(f"✅ FAISS index saved at {config.DB_FAISS_PATH}")
    else:
        print("⚠️ No valid documents found to index.")


if __name__ == "__main__":
    main()
