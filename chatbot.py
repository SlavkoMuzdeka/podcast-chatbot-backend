import config
import streamlit as st

from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


st.title("🎙️ Podcast AI Chatbot")
st.write("Ask any question about the podcast episodes.")


def _get_llm():
    """Loads the GPT model."""
    return ChatOpenAI(
        model_name=config.OPEN_AI_MODEL,
        temperature=config.OPEN_AI_MODEL_TEMPERATURE,
        openai_api_key=config.OPENAI_API_KEY,
    )


@st.cache_resource
def get_prompt():
    prompt = """ You need to answer the question . 
        Given below is the context and question of the user.
        context = {context}
        question = {question}
        """
    prompt = ChatPromptTemplate.from_template(prompt)
    return prompt


def _format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


@st.cache_resource
def load_knowledgeBase():
    db = FAISS.load_local(
        config.DB_FAISS_PATH,
        config.EMBEDDINGS_MODEL,
        allow_dangerous_deserialization=True,
    )
    return db


prompt = get_prompt()
knowledgeBase = load_knowledgeBase()

query = st.text_input("🔍 Type your question here...")

if st.button("Ask"):
    if query:
        similar_embeddings = knowledgeBase.similarity_search(query)
        similar_embeddings = FAISS.from_documents(
            documents=similar_embeddings,
            embedding=config.EMBEDDINGS_MODEL,
        )

        # Creating the chain for integrating llm, prompt, stroutputparser
        retriever = similar_embeddings.as_retriever()
        rag_chain = (
            {"context": retriever | _format_docs, "question": RunnablePassthrough()}
            | prompt
            | _get_llm()
            | StrOutputParser()
        )

        response = rag_chain.invoke(query)
        st.write("🗣️ **Bot:**", response)
