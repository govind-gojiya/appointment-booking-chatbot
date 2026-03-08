import os
from dotenv import load_dotenv
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.messages import HumanMessage, AIMessageChunk
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from tools import ALL_TOOLS
from prompts import SYSTEM_PROMPT

load_dotenv()

endpoint = HuggingFaceEndpoint(
    repo_id="Qwen/Qwen2.5-72B-Instruct",
    task="text-generation",
    max_new_tokens=1024,
    temperature=0.3,
    streaming=True,
    huggingfacehub_api_token=os.environ["HUGGINGFACEHUB_API_TOKEN"],
)

llm = ChatHuggingFace(llm=endpoint)
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
    for chunk, _ in agent.stream(
        {"messages": [HumanMessage(content=user_input)]},
        config=config,
        stream_mode="messages",
    ):
        if isinstance(chunk, AIMessageChunk) and chunk.content:
            yield chunk.content
