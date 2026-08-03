"""
Lifestyle coach graph: parse user context -> diet -> exercise -> study -> sleep -> final plan.
Educational only.
"""

from __future__ import annotations
from typing import TypedDict
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

class ParsedStudentProfile(BaseModel):
    budget: str = Field(description="Weekly or monthly budget for food and activities.")
    city: str = Field(description="City the student lives in.")
    school_hours: int = Field(default=7, description="Hours spent in school per day.")
    height: str = Field(default="", description="Height of the student.")
    weight: str = Field(default="", description="Weight of the student.")
    gender: str = Field(default="", description="Gender of the student.")
    subjects: str = Field(default="", description="Subjects the student is currently studying.")
    grades: str = Field(default="", description="Current grades in the subjects.")

class CoachState(TypedDict, total=False):
    raw_input: str
    parsed_text: str
    diet_plan: str
    exercise_plan: str
    study_plan: str
    sleep_plan: str
    final_plan: str

_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)
_structured = _llm.with_structured_output(ParsedStudentProfile)

def parse_user(state: CoachState) -> dict:
    text = state.get("raw_input", "")
    system = "Extract a structured profile for a student asking for a lifestyle coaching plan."
    parsed: ParsedStudentProfile = _structured.invoke(
        [SystemMessage(content=system), HumanMessage(content=text)],
    )
    summary = (
        f"Budget: {parsed.budget}\n"
        f"City: {parsed.city}\n"
        f"School hours per day: {parsed.school_hours}\n"
        f"Height: {parsed.height}\n"
        f"Weight: {parsed.weight}\n"
        f"Gender: {parsed.gender}\n"
        f"Subjects: {parsed.subjects}\n"
        f"Grades: {parsed.grades}"
    )
    return {"parsed_text": summary}

def plan_diet(state: CoachState) -> dict:
    prompt = (
        f"Profile:\n{state['parsed_text']}\n\n"
        "Provide a 3-5 point diet and nutrition plan suitable for a student in this city, respecting their budget, height, weight, and gender. Bullet markdown."
    )
    return {"diet_plan": _llm.invoke(prompt).content}

def plan_exercise(state: CoachState) -> dict:
    prompt = (
        f"Profile:\n{state['parsed_text']}\n\n"
        "Provide a 3-5 point exercise and physical activity plan for this student considering their height, weight, gender, and the time they spend in school. Bullet markdown."
    )
    return {"exercise_plan": _llm.invoke(prompt).content}

def plan_study(state: CoachState) -> dict:
    prompt = (
        f"Profile:\n{state['parsed_text']}\n\n"
        "Provide a realistic study schedule and strategies focused on their subjects and current grades, fitting around their school hours. Bullet markdown."
    )
    return {"study_plan": _llm.invoke(prompt).content}

def plan_sleep(state: CoachState) -> dict:
    prompt = (
        f"Profile:\n{state['parsed_text']}\n\n"
        "Provide a sleep schedule and habits to ensure adequate rest, considering their school hours and other activities. Bullet markdown."
    )
    return {"sleep_plan": _llm.invoke(prompt).content}

def finalize_plan(state: CoachState) -> dict:
    prompt = (
        "You are a student lifestyle coach. Combine the following into ONE supportive markdown plan with these sections:\n"
        "## Summary\n## Diet Plan\n## Exercise Plan\n## Study Plan\n## Sleep Schedule\n"
        f"Data:\n{state['parsed_text']}\n\n"
        f"Diet:\n{state.get('diet_plan', '')}\n\n"
        f"Exercise:\n{state.get('exercise_plan', '')}\n\n"
        f"Study:\n{state.get('study_plan', '')}\n\n"
        f"Sleep:\n{state.get('sleep_plan', '')}\n\n"
        "Tone: supportive, encouraging, realistic for a student. Add a quick disclaimer: educational only, not medical or academic advice."
    )
    return {"final_plan": _llm.invoke(prompt).content}

def build_graph():
    g = StateGraph(CoachState)
    g.add_node("parse_user", parse_user)
    g.add_node("diet", plan_diet)
    g.add_node("exercise", plan_exercise)
    g.add_node("study", plan_study)
    g.add_node("sleep", plan_sleep)
    g.add_node("finalize", finalize_plan)
    g.add_edge(START, "parse_user")
    g.add_edge("parse_user", "diet")
    g.add_edge("diet", "exercise")
    g.add_edge("exercise", "study")
    g.add_edge("study", "sleep")
    g.add_edge("sleep", "finalize")
    g.add_edge("finalize", END)
    return g.compile()

def run_coach(user_text: str) -> str:
    graph = build_graph()
    out = graph.invoke({"raw_input": user_text})
    return out.get("final_plan", "") or "No plan generated."
