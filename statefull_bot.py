import os
import config

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain_community.chat_models import ChatOpenAI
from langchain_pinecone import PineconeVectorStore

load_dotenv()

# EXAMPLE OF A STATEFUL BOT

chat_history = []

if __name__ == "__main__":
    vectorstore = PineconeVectorStore(
        index_name=os.environ["INDEX_NAME"], embedding=config.EMBEDDINGS_MODEL
    )

    chat = ChatOpenAI(verbose=True, temperature=0, model_name="gpt-3.5-turbo")

    qa = ConversationalRetrievalChain.from_llm(
        llm=chat, chain_type="stuff", retriever=vectorstore.as_retriever()
    )

    res = qa(
        {
            "question": "What are the applications of generative AI according the the paper? Please number each application.",
            "chat_history": chat_history,
        }
    )
    print(res)

    history = (res["question"], res["answer"])
    chat_history.append(history)

    res = qa(
        {
            "question": "Can you please elaborate more on application number 2?",
            "chat_history": chat_history,
        }
    )
    print(res)
