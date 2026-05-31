from __future__ import annotations

from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field


class BarInventory(BaseModel):
    spirits: list[str] = Field(default_factory=list, description="Vodka, rum, gin, whiskey...")

    mixers: list[str] = Field(default_factory=list, description="Tonic, soda, juice, syrup...")

    fresh: list[str] = Field(default_factory=list, description="Limes, mint, berries...")

    tools: list[str] = Field(default_factory=list, description="Shaker, blender...")
    
    vibe: str = Field(default="", description="What kind of drinks they want tonight.")


class BarState(TypedDict, total=False):
    raw_input: str
    inventory: str
    available_drinks: str
    stretch_drinks: str
    menu: str


_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.6)
_parser = _llm.with_structured_output(BarInventory)


def parse_bar(state: BarState) -> dict:
    text = state.get("raw_input", "")
    result: BarInventory = _parser.invoke([
        SystemMessage(content=(
            "Pull out what this person has in their home bar. "
            "Spirits, mixers, fresh ingredients, bar tools and what kind of drinks they like. "
            "If something's vague just make a reasonable guess."
        )),
        HumanMessage(content=text),
    ])


    summary = (
        f"Spirits: {', '.join(result.spirits) or 'none listed'}\n"
        f"Mixers: {', '.join(result.mixers) or 'none listed'}\n"
        f"Fresh: {', '.join(result.fresh) or 'none listed'}\n"
        f"Tools: {', '.join(result.tools) or 'just glasses'}\n"
        f"Vibe: {result.vibe or 'open to anything'}"
    )

    return {"inventory": summary}


def mix_now(state: BarState) -> dict:
    prompt = (
        f"Home bar inventory:\n{state['inventory']}\n\n"
        "Suggest 3-4 cocktails they can make RIGHT NOW with only what's listed. "
        "For each one give the name, ingredients with rough amounts and how to make it. "
        "Don't sneak in anything they don't have. "
        "If the bar is bare just suggest highballs or neat pours."
    )
    return {"available_drinks": _llm.invoke(prompt).content}


def mix_soon(state: BarState) -> dict:
    prompt = (
        f"Home bar inventory:\n{state['inventory']}\n\n"
        f"Already suggested these:\n{state.get('available_drinks', '')}\n\n"
        "Now suggest 2-3 more drinks they could make if they picked up "
        "1-2 extra things each. List what they'd need to buy. "
        "Keep it to cheap, easy-to-find stuff."
    )


    return {"stretch_drinks": _llm.invoke(prompt).content}


def build_menu(state: BarState) -> dict:
    prompt = (
        "Put together a drink menu. Use these sections:\n"
        "## Tonight's Menu\n(what they can make now)\n\n"
        "## Worth a Store Run\n(drinks needing 1-2 extra ingredients + what to grab)\n\n"
        "## Quick Shopping List\n(all missing ingredients in one spot)\n\n"
        f"Inventory:\n{state['inventory']}\n\n"
        f"Ready now:\n{state.get('available_drinks', '')}\n\n"
        f"With extras:\n{state.get('stretch_drinks', '')}\n\n"
        "Sound like a friend who knows drinks, not a cocktail textbook."
    )


    return {"menu": _llm.invoke(prompt).content}



def build_graph():
    g = StateGraph(BarState)
    g.add_node("parse_bar", parse_bar)
    g.add_node("mix_now", mix_now)
    g.add_node("mix_soon", mix_soon)
    g.add_node("build_menu", build_menu)
    g.add_edge(START, "parse_bar")
    g.add_edge("parse_bar", "mix_now")
    g.add_edge("mix_now", "mix_soon")
    g.add_edge("mix_soon", "build_menu")
    g.add_edge("build_menu", END)
    return g.compile()


def run_bartender(user_text: str) -> str:
    graph = build_graph()
    result = graph.invoke({"raw_input": user_text})
    return result.get("menu", "Couldn't put a menu together. Try again?")
