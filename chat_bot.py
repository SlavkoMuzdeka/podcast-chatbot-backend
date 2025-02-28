import chat
import streamlit as st

st.title("🎙️ Podcast AI Chatbot")
st.write("Ask any question about the podcast episodes.")

user_input = st.text_input("🔍 Type your question here...")
if st.button("Ask"):
    if user_input:
        response = chat.get_response(user_input)
        st.write("🗣️ **Bot:**", response)
