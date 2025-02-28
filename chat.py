import config
import embeddings

from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA


def get_relevant_chunks(query):
    """Retrieves relevant podcast chunks for a given user query."""
    retriever = embeddings.load_embeddings()
    results = retriever.get_relevant_documents(query)
    return [doc.page_content for doc in results]


def get_response(query):
    """Retrieves relevant chunks and generates a response using GPT-4."""
    retrieved_chunks = get_relevant_chunks(query)
    context = "\n\n".join(retrieved_chunks)

    llm = ChatOpenAI(model_name="gpt-4", openai_api_key=config.OPENAI_API_KEY)

    # Create QA chain with retriever
    qa_chain = RetrievalQA.from_chain_type(llm)

    return qa_chain.invoke(context + "\n\n" + query)["result"]
