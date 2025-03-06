import streamlit as st

from utils.chatbot_utils import get_chain

st.set_page_config(page_title="🤗💬 Podcaster")


with st.sidebar:
    st.title("🤗💬 Podcaster")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

chat_history = st.session_state.chat_history
qa = get_chain()

if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {"role": "assistant", "content": "How may I help you?"}
    ]


def generate_response(query):
    response = qa.invoke({"question": query, "chat_history": chat_history})
    answer = response.get("answer", "")
    chat_history.append((query, answer))

    return answer


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(prompt)
            st.write(response)
    message = {"role": "assistant", "content": response}
    st.session_state.messages.append(message)
