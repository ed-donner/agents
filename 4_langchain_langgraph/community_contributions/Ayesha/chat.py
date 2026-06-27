import gradio as gr
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

from dotenv import load_dotenv
import os

from prompts import SYSTEM_PROMPT


load_dotenv()


class State(TypedDict):
    messages: Annotated[list, add_messages]
    mistakes: dict  



llm = ChatOpenAI(
    model="openai/gpt-4o-mini",
    temperature=0.7,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_api_base=os.getenv("OPENAI_BASE_URL"),
    default_headers={
        "HTTP-Referer": "http://localhost:7860",
    }
)
# Correction tool
@tool
def correct_french(text: str) -> str:
    """Correct the mistake in the French sentence and explain briefly in both English and French."""
    prompt = f"""
    Correct this French sentence:
    {text}

    Return:
    - Correct sentence
    - Short explanation in both English and French
    """
    return llm.invoke(prompt).content


tools = [correct_french]

llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    messages = state["messages"]

   
    if len(messages) == 1:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}


def update_memory(state: State):
    messages = state["messages"]

    if len(messages) < 2:
        return {"mistakes": state.get("mistakes", {})}

    last_user_msg = messages[-2].content.lower()

    mistakes = state.get("mistakes", {})

    prompt = f"""
    Analyze the user's message and identify mistake types.

    Sentence: {last_user_msg}

    Possible mistake types:
    - Gender mistake
    - Number mistake
    - Pronoun mistake
    - Verb tense mistake
    - Adjective mistake
    - Adverb mistake
    - Preposition mistake
    - Conjunction mistake
    - Interjection mistake

    Return ONLY a comma-seperated list.
    """
    response = llm.invoke(prompt).content.lower()

    if "gender" in last_user_msg:
        mistakes["gender_errors"] = mistakes.get("gender_errors", 0) + 1
    if "number" in last_user_msg:
        mistakes["number_errors"] = mistakes.get("number_errors", 0) + 1
    if "pronoun" in last_user_msg:
        mistakes["pronoun_errors"] = mistakes.get("pronoun_errors", 0) + 1
    if "verb tense" in last_user_msg:
        mistakes["verb_tense_errors"] = mistakes.get("verb_tense_errors", 0) + 1
    if "adjective" in last_user_msg:
        mistakes["adjective_errors"] = mistakes.get("adjective_errors", 0) + 1
    if "adverb" in last_user_msg:
        mistakes["adverb_errors"] = mistakes.get("adverb_errors", 0) + 1
    if "preposition" in last_user_msg:
        mistakes["preposition_errors"] = mistakes.get("preposition_errors", 0) + 1
    if "conjunction" in last_user_msg:
        mistakes["conjunction_errors"] = mistakes.get("conjunction_errors", 0) + 1
    if "interjection" in last_user_msg:
        mistakes["interjection_errors"] = mistakes.get("interjection_errors", 0) + 1


    return {"mistakes": mistakes}



graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode(tools=tools))
graph_builder.add_node("memory", update_memory)


graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
    {
        "tools": "tools",
        "__end__": "memory"
    }
)
graph_builder.add_edge("tools", "chatbot")

graph_builder.add_edge("chatbot", "memory")  
# graph_builder.add_edge("memory", "chatbot")

graph_builder.add_edge(START, "chatbot")
graph_builder.set_finish_point("memory")

memory = MemorySaver()

graph = graph_builder.compile(checkpointer=memory)


config = {"configurable": {"thread_id": "french-session"}}


# gradio function
async def chat(user_input, history):
    result = await graph.ainvoke(
        {
            "messages": [{"role": "user", "content": user_input}],
            "mistakes": {}
        },
        config=config
    )

    return result["messages"][-1].content



gr.ChatInterface(
    chat,
    type="messages",
    title="French Study Buddy",
    description="A study buddy for French learners."
).launch()