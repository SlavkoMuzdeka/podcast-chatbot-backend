import streamlit as st

from utils.chatbot_utils import get_chain, trim_chat_history
from langchain.schema import AIMessage, HumanMessage

st.set_page_config(page_title="🤗💬 Podcaster")

# Sidebar setup for the app
with st.sidebar:
    st.title("🤗💬 Podcaster")

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

chat_history = st.session_state.chat_history
qa = get_chain()

# Initialize messages if not present
if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {"role": "assistant", "content": "How may I help you?"}
    ]


def generate_response(query):
    """
    Generates a response for a user's query by invoking the QA chain and updating chat history.

    Args:
        query (str): The user's input query.

    Returns:
        str: The generated response from the assistant.
    """
    chat_messages = trim_chat_history(chat_history)
    response = qa.invoke({"question": query, "chat_history": chat_messages})
    answer = response.get("answer", "")
    chat_history.append(HumanMessage(content=query))
    chat_history.append(AIMessage(content=answer))

    return answer


# Display previous messages in the chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Process user input and generate a response
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Generate assistant's response if the last message isn't from the assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(prompt)
            st.write(response)
    message = {"role": "assistant", "content": response}
    st.session_state.messages.append(message)
