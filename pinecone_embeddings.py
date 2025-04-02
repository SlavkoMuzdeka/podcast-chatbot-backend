import os
import json
import time
import logging

from typing import List
from dotenv import load_dotenv
from pinecone.data import _Index
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv(override=True)


def _load_config() -> dict:
    """
    Loads configuration settings from `config.json`.

    Returns:
        dict: Configuration dictionary containing base_url, folder_name, and debug flag.
    """
    with open("config.json", "r") as f:
        config = json.load(f)
        return config["pinecone"]


def _get_processed_transcriptions(index: _Index, config: dict) -> List[str]:
    """
    Retrieves the list of already processed transcription files stored in Pinecone.

    Args:
        index (_Index): The Pinecone index object.
        config (dict): The configuration settings from `config.json`.

    Returns:
        List[str]: A list of filenames that have already been processed.
    """
    processed_transcriptions = set()

    for ids in index.list(namespace=config["namespace"]):
        for id in ids:
            base_name = id.rsplit("_", 1)[0]  # Extract base filename without chunk ID
            processed_transcriptions.add(base_name)

    processed_transcriptions = list(processed_transcriptions)

    if config["debug"]:
        logger.info(
            f"We have processed {len(processed_transcriptions)} transcriptions until now."
        )

    return processed_transcriptions


def create_or_retrieve_index(config: dict) -> Pinecone:
    """
    Creates a new Pinecone index if it does not already exist.

    Args:
        config (dict): Configuration settings from `config.json`.

    Returns:
        Pinecone: The Pinecone client object.
    """
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY", ""))
    spec = ServerlessSpec(cloud=config["cloud"], region=config["region"])

    if config["index_name"] in pc.list_indexes().names():
        if config["debug"]:
            logger.info("The index already exists.")
        return pc

    if config["debug"]:
        logger.info("Creating new index...")

    # Create a new Pinecone index with specified settings
    pc.create_index(
        spec=spec,
        metric=config["metric"],
        name=config["index_name"],
        dimension=config["embeddings_vector_length"],
    )

    # Wait for index to be ready
    while not pc.describe_index(config["index_name"]).status["ready"]:
        time.sleep(1)

    if config.DEBUG:
        logger.info("Successfully created new index.")

    return pc


def process_transcriptions(pc: Pinecone, config: dict) -> None:
    """
    Reads and processes transcription files from the specified folder,
    converts them into embeddings, and stores them in Pinecone.

    Args:
        pc (Pinecone): The Pinecone client object.
        config (dict): Configuration settings from `config.json`.
    """
    total_processed = 0
    embeddings_model = OpenAIEmbeddings(
        model=config["embeddings_model"],
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
    )
    index = pc.Index(config["index_name"])
    processed_transcriptions = _get_processed_transcriptions(index, config)

    # Initialize text splitter for chunking long documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config["chunk_size"], chunk_overlap=config["chunk_overlap"]
    )

    if config["debug"]:
        logger.info(
            f"📂 Processing text files from {config['transcriptions_folder']}..."
        )

    for file in os.listdir(config["transcriptions_folder"]):
        if file.endswith(".txt") and file not in processed_transcriptions:
            with open(
                os.path.join(config["transcriptions_folder"], file),
                "r",
                encoding="utf-8",
            ) as f:
                text = f.read()

            # Split text into smaller chunks
            chunks = splitter.split_text(text)

            # Generate embeddings for each chunk
            embeddings = embeddings_model.embed_documents(chunks)

            # Prepare data for insertion into Pinecone
            vectors = [
                {
                    "id": f"{file}_{i}",
                    "values": embeddings[i],
                    "metadata": {"text": chunks[i]},
                }
                for i in range(len(chunks))
            ]

            # Insert vectors into Pinecone index
            index.upsert(vectors=vectors, namespace=config["namespace"])

            total_processed += 1
            if config["debug"]:
                logger.info(f"✅ Processed {file}. Total processed: {total_processed}")

    if config["debug"]:
        if total_processed > 0:
            logger.info("All documents processed and stored in Pinecone.")
        else:
            logger.info("No documents to process.")


def main():
    """
    Main function to run the entire pipeline:
        1. Load configuration settings.
        2. Create or retrieve the Pinecone index.
        3. Process transcription files and store them in Pinecone.
    """
    config = _load_config()
    pc = create_or_retrieve_index(config)
    process_transcriptions(pc, config)


if __name__ == "__main__":
    main()
