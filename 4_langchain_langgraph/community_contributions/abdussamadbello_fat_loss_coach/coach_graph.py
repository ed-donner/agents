"""
Fat loss coach graph: parse user context → exercise options → nutrition options
→ budget alignment → single weekly-style plan. Educational only; not medical advice.
"""

from __future__ import annotations

from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field


class ParsedProfile(BaseModel):
    """Structured intake from free-form user text."""

    goal: str = Field(description="Fat loss or recomposition goal in plain language.")
    weekly_food_budget_usd: float | None = Field(
        default=None, description="Approximate weekly food budget in USD if stated."
    )
    gym_budget_usd: float | None = Field(
        default=None, description="Monthly gym/tools budget if stated, else null."
    )
    minutes_per_day: int = Field(
        default=30, description="Realistic daily minutes for movement/meal prep."
    )
    dietary_notes: str = Field(default="", description="Preferences, allergies, cultural foods.")
    lifestyle: str = Field(description="Work schedule, stress, sleep, steps, home vs travel.")
    constraints: str = Field(
        default="", description="Injuries, equipment limits, foods to avoid, doctor limits."
    )


class CoachState(TypedDict, total=False):
    raw_input: str
    parsed_text: str
    exercise_options: str
    nutrition_options: str
    budget_aligned: str
    final_plan: str


_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)
_structured = _llm.with_structured_output(ParsedProfile)


def parse_user(state: CoachState) -> dict:
    text = state.get("raw_input", "")
    system = (
        "Extract a structured profile for someone asking for fat-loss coaching. "
        "Infer reasonable numbers if ranges are given; use null if unknown."
    )
    parsed: ParsedProfile = _structured.invoke(
        [SystemMessage(content=system), HumanMessage(content=text)],
    )
    summary = (
        f"Goal: {parsed.goal}\n"
        f"Weekly food budget (USD): {parsed.weekly_food_budget_usd}\n"
        f"Gym/equipment budget (USD/mo): {parsed.gym_budget_usd}\n"
        f"Time per day (min): {parsed.minutes_per_day}\n"
        f"Diet: {parsed.dietary_notes}\n"
        f"Lifestyle: {parsed.lifestyle}\n"
        f"Constraints: {parsed.constraints}"
    )
    return {"parsed_text": summary}


def coach_exercise(state: CoachState) -> dict:
    prompt = (
        f"Profile:\n{state['parsed_text']}\n\n"
        "List 3–5 concrete exercise strategies (fat loss, sustainable). "
        "Include options for: gym, home minimal equipment, and walking-only. "
        "Respect time budget and injuries. Bullet markdown."
    )
    out = _llm.invoke(prompt).content
    return {"exercise_options": str(out)}


def coach_nutrition(state: CoachState) -> dict:
    prompt = (
        f"Profile:\n{state['parsed_text']}\n\n"
        "List 3–5 nutrition approaches (calorie deficit, protein, meal prep patterns). "
        "Offer budget-friendly swaps and one 'flexible' option. Bullet markdown. "
        "No extreme restriction; mention medical dietitian if medical conditions."
    )
    out = _llm.invoke(prompt).content
    return {"nutrition_options": str(out)}


def align_budget(state: CoachState) -> dict:
    prompt = (
        f"Profile:\n{state['parsed_text']}\n\n"
        "Exercise ideas:\n"
        f"{state.get('exercise_options', '')}\n\n"
        "Nutrition ideas:\n"
        f"{state.get('nutrition_options', '')}\n\n"
        "Trim and prioritize what fits the stated food and gym budgets. "
        "If budget is missing, give low / medium / high cost tiers. Short markdown."
    )
    out = _llm.invoke(prompt).content
    return {"budget_aligned": str(out)}


def finalize_plan(state: CoachState) -> dict:
    prompt = (
        "You are a coaching planner. Combine into ONE markdown plan with sections:\n"
        "## Summary\n## Week 1 focus\n## Training (3–4 sessions)\n## Nutrition habits\n"
        "## Budget notes\n## Risks / when to ask a professional\n\n"
        f"Data:\n{state['parsed_text']}\n\n"
        f"Exercise:\n{state.get('exercise_options', '')}\n\n"
        f"Nutrition:\n{state.get('nutrition_options', '')}\n\n"
        f"Budget fit:\n{state.get('budget_aligned', '')}\n\n"
        "Tone: supportive, specific, no medical diagnosis. "
        "Add disclaimer: educational only, not medical advice."
    )
    out = _llm.invoke(prompt).content
    return {"final_plan": str(out)}


def build_graph():
    g = StateGraph(CoachState)
    g.add_node("parse_user", parse_user)
    g.add_node("exercise", coach_exercise)
    g.add_node("nutrition", coach_nutrition)
    g.add_node("budget", align_budget)
    g.add_node("finalize", finalize_plan)
    g.add_edge(START, "parse_user")
    g.add_edge("parse_user", "exercise")
    g.add_edge("exercise", "nutrition")
    g.add_edge("nutrition", "budget")
    g.add_edge("budget", "finalize")
    g.add_edge("finalize", END)
    return g.compile()


def run_coach(user_text: str) -> str:
    graph = build_graph()
    out = graph.invoke({"raw_input": user_text})
    return out.get("final_plan", "") or "No plan generated."
