import config
import streamlit as st


from langchain_openai import ChatOpenAI
from langchain_core.messages import trim_messages
from langchain_community.vectorstores import FAISS
from langchain.callbacks import StdOutCallbackHandler
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import ConversationalRetrievalChain


@st.cache_resource
def get_chain():
    """
    Returns a cached ConversationalRetrievalChain using the LLM, retriever, and prompt.
    If debugging is enabled, adds callback to print debug info.
    """
    callbacks = []

    if config.DEBUG:
        callbacks = [StdOutCallbackHandler()]

    return ConversationalRetrievalChain.from_llm(
        llm=_get_llm(),
        chain_type="stuff",
        retriever=_get_retriever().as_retriever(),
        combine_docs_chain_kwargs={
            "prompt": _get_prompt(),
        },
        callbacks=callbacks,
    )


def trim_chat_history(chat_history):
    """
    Trims chat history to fit within the max token limit.
    """
    return trim_messages(
        chat_history,
        max_tokens=config.MAX_TOKENS,
        strategy="last",
        token_counter=ChatOpenAI(model=config.OPEN_AI_MODEL),
        start_on="human",
        include_system=True,
    )


def _get_llm():
    """
    Returns the configured GPT language model.
    """
    return ChatOpenAI(
        model_name=config.OPEN_AI_MODEL,
        temperature=config.OPEN_AI_MODEL_TEMPERATURE,
        openai_api_key=config.OPENAI_API_KEY,
    )


@st.cache_resource
def _get_retriever():
    """
    Loads and returns the FAISS retriever from local storage.
    """
    return FAISS.load_local(
        config.DB_FAISS_PATH,
        config.EMBEDDINGS_MODEL,
        allow_dangerous_deserialization=True,
    )


def _get_prompt():
    """
    Returns the chat prompt template.
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful AI bot named Podcaster. "
                "You are an AI expert trained to answer questions. "
                "If the context and chat history contain relevant information, use them as the primary source. "
                "If the information is insufficient, rely on your general knowledge to provide the best possible answer.",
            ),
            ("system", "Context is\n{context}"),
            ("human", "Chat history is\n{chat_history}"),
            ("human", "Question is\n{question}"),
        ]
    )
