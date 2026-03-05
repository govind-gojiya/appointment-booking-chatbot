import uuid
import streamlit as st
# from agent import run_agent
# from agent_ollama import run_agent
from agent_huggingface import run_agent

st.set_page_config(page_title="Appointment Booking Assistant")
st.title("Appointment Booking Assistant")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.chat_history.append(("user", user_input))
    response = run_agent(user_input, st.session_state.thread_id)
    st.session_state.chat_history.append(("assistant", response))

for role, message in st.session_state.chat_history:
    avatar = role
    with st.chat_message(avatar):
        st.write(message)
