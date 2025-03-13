import os
import time
import config

from pinecone import Pinecone, ServerlessSpec
from langchain_text_splitters import RecursiveCharacterTextSplitter


def main():
    pc = create_pinecone_index()

    total_processed = 0
    embedding_model = config.EMBEDDINGS_MODEL

    # Connect to the existing Pinecone index
    index = pc.Index(config.PINECONE_INDEX_NAME)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

    for folder in config.DATA_FOLDERS:
        if config.DEBUG:
            print(f"📂 Processing text files from {folder}...")

        for file in os.listdir(folder):
            if file.endswith(".txt"):
                with open(os.path.join(folder, file), "r", encoding="utf-8") as f:
                    text = f.read()

                # Split text into chunks
                chunks = splitter.split_text(text)

                # Generate embeddings
                embeddings = embedding_model.embed_documents(chunks)

                # Prepare data for Pinecone
                vectors = [
                    {
                        "id": f"{file}_{i}",
                        "values": embeddings[i],
                    }
                    for i in range(len(chunks))
                ]

                # Insert into Pinecone
                index.upsert(vectors=vectors, namespace=config.PINECONE_NAMESPACE)

                total_processed += 1
                if config.DEBUG:
                    print(f"✅ Processed {file}. Total processed: {total_processed}")

    if config.DEBUG:
        print("🚀 All documents processed and stored in Pinecone!")


def create_pinecone_index():
    pc = Pinecone(api_key=config.PINECONE_API_KEY)
    spec = ServerlessSpec(cloud=config.PINECONE_CLOUD, region=config.PINECONE_REGION)

    index_name = config.PINECONE_INDEX_NAME

    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=config.EMBEDDINGS_VECTOR_LENGTH,
            metric=config.PINECONE_METRIC,
            spec=spec,
        )

        # Wait for index to be ready
        while not pc.describe_index(index_name).status["ready"]:
            time.sleep(1)

        # See that it is empty
        if config.DEBUG:
            print("Index before upsert:")
            print(pc.Index(index_name).describe_index_stats())
            print("Successfully created new index.")
    else:
        if config.DEBUG:
            print("The index already exists.")
        pass

    return pc


if __name__ == "__main__":
    main()
