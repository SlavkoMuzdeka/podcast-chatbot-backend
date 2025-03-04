import os
import config

from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

load_dotenv()

# EXAMPLE CODE FOR INGESTING DATA INTO PINECONE

if __name__ == "__main__":
    print("ingesting data...")

    # load pdf document
    loader = PyPDFLoader("example.pdf")
    document = loader.load()

    # split entire documents into chunks
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(document)
    print(f"created {len(texts)} chunks")

    # create vector embeddings and save it in pinecone database
    PineconeVectorStore.from_documents(
        texts, config.EMBEDDINGS_MODEL, index_name="ENTER INDEX NAME"
    )
