import config
import streamlit as st

from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import ConversationalRetrievalChain

# from langchain.chains import RetrievalQA
# from langchain_core.runnables import RunnablePassthrough
# from langchain_core.output_parsers import StrOutputParser


@st.cache_resource
def get_chain():
    # """This is user defined type of LangChain"""
    # rag_chain = (
    #     {"context": retriever | _format_docs, "question": RunnablePassthrough()}
    #     | prompt
    #     | llm
    #     | StrOutputParser()
    # ) # This is the one approach that works good

    # """
    # RetrievalQA is a specialized type of Langchain chain designed specifically for question answering tasks.
    # RetrievalQA Prompt:
    #     prompt_template = '''Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

    #         {context}

    #         Question: {question}
    #         Helpful Answer:'''
    # """
    # qa = RetrievalQA.from_chain_type(llm, chain_type="stuff", retriever=retriever)
    # response = qa.invoke(query)

    # """
    # This specialized chain empowers you to build stateful chatbots that maintain a conversation history when passed explicitly.
    # ConversationalRetrievalChain Prompt: This prompt is more complex.
    #     _template = '''Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.

    #         Chat History:
    #         {chat_history}
    #         Follow Up Input: {question}
    #         Standalone question:''''
    #         CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)

    #         prompt_template = '''Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

    #         {context}

    #         Question: {question}
    #         Helpful Answer:'''
    # """
    llm = _get_llm()
    prompt = _get_prompt()
    retriever = _get_retriever()
    condense_question_prompt = _get_condense_prompt()

    qa = ConversationalRetrievalChain.from_llm(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        condense_question_prompt=condense_question_prompt,
        combine_docs_chain_kwargs={
            "prompt": prompt,
        },
    )
    return qa


def _get_llm():
    """Loads the GPT model."""
    return ChatOpenAI(
        model_name=config.OPEN_AI_MODEL,
        temperature=config.OPEN_AI_MODEL_TEMPERATURE,
        openai_api_key=config.OPENAI_API_KEY,
    )


def _get_prompt():
    # prompt = """You are an expert AI assistant trained to answer questions based on podcast episode content.
    #     Below is the context, which contains transcribed text from a podcast episode. Your task is to answer the question
    #     based on the information provided in the context. If the answer is not clear or the context does not provide
    #     sufficient information, please indicate that in your response.

    #     context = {context}

    #     question = {question}

    #     Please provide a clear, concise, and well-structured answer that directly addresses the user's question based
    #     on the podcast content. If applicable, include examples or details from the context to support your response.
    # """
    """
    The context below contains transcribed text from a podcast episode.
    Your goal is to answer the user's question using this context as the primary source of information.
    """
    prompt = """
        You are an AI expert trained to answer questions using the provided context. 
    
        If the context and chat history contain relevant information, use them as the primary source. 
        If the information is insufficient, rely on your general knowledge to provide the best possible answer.

        Chat History:
        {chat_history}

        Context:
        {context}

        Question:
        {question}

        
        If the context and chat history don't contain enough information to answer the question, politely inform the user.
    """
    # Please ensure the answer is clear, relevant, and directly derived from the provided context and chat history.
    return ChatPromptTemplate.from_template(prompt)


def _get_condense_prompt():
    condense_question_template = """
        Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.

        Chat History:
        {chat_history}
        Follow Up Input: {question}
        Standalone question:"""

    return ChatPromptTemplate.from_template(condense_question_template)


# This function is used if we decide to have user defined prompt
# def _format_docs(docs):
#     return "\n\n".join(doc.page_content for doc in docs)


@st.cache_resource
def _get_retriever():
    db = FAISS.load_local(
        config.DB_FAISS_PATH,
        config.EMBEDDINGS_MODEL,
        allow_dangerous_deserialization=True,
    )
    return db.as_retriever()
