import uuid
import streamlit as st
import chat_store
# from agent import run_agent, get_history
# from agent_ollama import run_agent, get_history
from agent_huggingface import run_agent, get_history


st.set_page_config(
    page_title="Appointment Booking Assistant",
    layout="wide",
)

if "current_thread_id" not in st.session_state:
    st.session_state.current_thread_id = None
if "pending_new_chat" not in st.session_state:
    st.session_state.pending_new_chat = False

with st.sidebar:
    st.title("Chats")

    if st.button("New Chat", use_container_width=True, type="primary"):
        st.session_state.pending_new_chat = True
        st.session_state.current_thread_id = None
        st.rerun()

    st.divider()

    chats = chat_store.get_all_chats()
    if not chats:
        st.caption("No chats yet. Click 'New Chat' to start.")

    for chat in chats:
        is_active = st.session_state.current_thread_id == chat["thread_id"]
        label = f"{chat['user_name']} — {chat['title']}"
        if st.button(
            label,
            key=f"chat_{chat['thread_id']}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.current_thread_id = chat["thread_id"]
            st.session_state.pending_new_chat = False
            st.rerun()

st.title("Appointment Booking Assistant")

if st.session_state.pending_new_chat:
    st.subheader("Start a new chat")
    st.caption("Please enter your name. It will be used for booking appointments in this conversation.")

    with st.form("name_form", clear_on_submit=True):
        user_name = st.text_input("Your name", placeholder="e.g. Govind Gojiya")
        submitted = st.form_submit_button("Start Chat", type="primary")

    if submitted:
        if user_name.strip():
            thread_id = str(uuid.uuid4())
            chat_store.create_chat(thread_id, user_name.strip())
            st.session_state.current_thread_id = thread_id
            st.session_state.pending_new_chat = False
            st.rerun()
        else:
            st.error("Please enter your name to start a chat.")

elif st.session_state.current_thread_id:
    thread_id = st.session_state.current_thread_id
    chat_info = chat_store.get_chat(thread_id)

    if not chat_info:
        st.error("Chat not found. Please start a new chat.")
    else:
        st.caption(f"Chatting as **{chat_info['user_name']}**")

        for role, content in get_history(thread_id):
            with st.chat_message(role):
                st.write(content)

        user_input = st.chat_input("Type your message...")

        if user_input:
            user_name = chat_info["user_name"]

            with st.chat_message("user"):
                st.write(user_input)

            with st.chat_message("assistant"):
                response = st.write_stream(
                    run_agent(user_input, thread_id, user_name)
                )

            if chat_info["title"] == "New Chat":
                title = user_input[:40] + ("..." if len(user_input) > 40 else "")
                chat_store.update_title(thread_id, title)

            st.rerun()

else:
    st.info("Select a chat from the sidebar or click 'New Chat' to begin.")
