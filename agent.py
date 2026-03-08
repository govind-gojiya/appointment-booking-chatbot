import sqlite3
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk, SystemMessage
from langchain.agents import create_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from tools import ALL_TOOLS
from prompts import SYSTEM_PROMPT

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    max_retries=2,
)

_conn = sqlite3.connect("appointments.db", check_same_thread=False)
_conn.execute("PRAGMA journal_mode=WAL")
checkpointer = SqliteSaver(_conn)

agent = create_agent(
    model=llm,
    tools=ALL_TOOLS,
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

def run_agent(user_input: str, thread_id: str, user_name: str):
    config = {
        "recursion_limit": 20,
        "configurable": {"thread_id": thread_id},
    }
    
    state = agent.get_state(config)
    is_new = len(state.values.get("messages", [])) == 0

    messages = []
    if is_new:
        messages.append(SystemMessage(
            content=(
                f"The user's name is {user_name}. Use this name throughout "
                "the conversation. When the user asks to list their bookings, "
                f"use '{user_name}' as the name automatically without asking."
            )
        ))

    messages.append(HumanMessage(content=user_input))

    for chunk, _ in agent.stream( {"messages": messages}, config=config, stream_mode="messages"):
        if isinstance(chunk, AIMessageChunk) and chunk.content:
            yield chunk.content

def get_history(thread_id: str) -> list:
    config = {"configurable": {"thread_id": thread_id}}
    state = agent.get_state(config)
    history = []

    for msg in state.values.get("messages", []):
        if isinstance(msg, HumanMessage) and msg.content:
            history.append(("user", msg.content))
        elif isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            history.append(("assistant", msg.content))

    return history
