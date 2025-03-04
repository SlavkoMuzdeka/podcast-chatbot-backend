import os
import config

from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS


def main():
    """Loads podcast transcripts, generates embeddings in smaller batches, and stores them in FAISS."""
    total_processed = 0

    vector_store = None

    for file in os.listdir(config.DATA_FOLDER):
        if file.endswith(".txt"):
            with open(
                os.path.join(config.DATA_FOLDER, file), "r", encoding="utf-8"
            ) as f:
                text = f.read()

                document = Document(page_content=text)

                if vector_store is None:
                    # Convert chunks into Document format required by FAISS
                    vector_store = FAISS.from_documents(
                        [document], config.EMBEDDINGS_MODEL
                    )
                else:
                    vector_store.add_documents([document])

                total_processed += 1
                print(f"✅ Processed {file}. Total processed: {total_processed}")

    # Store embeddings in FAISS
    vector_store.save_local(config.DB_FAISS_PATH)
    print(f"✅ Processed {total_processed} files.")
    print(f"✅ FAISS index saved at {config.DB_FAISS_PATH}")


if __name__ == "__main__":
    main()
