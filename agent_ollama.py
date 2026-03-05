import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from tools import ALL_TOOLS
from prompts import SYSTEM_PROMPT

load_dotenv()

llm = ChatOllama(
    model="qwen2:7b",
    temperature=0.3,
)

checkpointer = MemorySaver()

agent = create_agent(
    model=llm,
    tools=ALL_TOOLS,
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

def run_agent(user_input: str, thread_id: str = "default"):
    config = {
        "recursion_limit": 20,
        "configurable": {"thread_id": thread_id},
    }
    result = agent.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config=config,
    )
    return result["messages"][-1].content
