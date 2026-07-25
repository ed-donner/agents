
import os
import json
import operator
from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

load_dotenv(override=True)


llm = ChatOpenAI(
    model="gpt-4o-mini",
    base_url=os.environ.get("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
    api_key=os.environ.get("API_TOKEN")
)


# State

class MeetingPrepState(TypedDict):
    person_name: str
    company: str
    meeting_purpose: str
    your_background: str

    person_research: str
    company_research: str

    talking_points: str
    agenda: str
    followup_email: str

    eval_score: int
    eval_feedback: str
    revision_count: int

    full_report: str
    messages: Annotated[list, operator.add]


# Nodes

def research_person(state: MeetingPrepState) -> dict:
    """Research the person you're meeting with."""
    prompt = f"""Research this person for a meeting prep:
Name: {state['person_name']}
Company: {state['company']}

Find out:
- Their role and responsibilities
- Their professional background
- Recent public activity (talks, articles, posts)
- What they likely care about professionally

Keep it factual and concise. 150 words max."""

    response = llm.invoke([SystemMessage(content="You are a meeting prep researcher. Be concise and factual."),
                           HumanMessage(content=prompt)])

    return {
        "person_research": response.content,
        "messages": [AIMessage(content=f"[Researcher] Researched {state['person_name']}")]
    }


def research_company(state: MeetingPrepState) -> dict:
    """Research the company."""
    prompt = f"""Research this company for a meeting prep:
Company: {state['company']}

Find out:
- What the company does
- Recent news or developments
- Their tech stack or approach (if relevant)
- Market position and competitors

Keep it factual. 150 words max."""

    response = llm.invoke([SystemMessage(content="You are a business researcher. Be specific, not generic."),
                           HumanMessage(content=prompt)])

    return {
        "company_research": response.content,
        "messages": [AIMessage(content=f"[Researcher] Researched {state['company']}")]
    }


def generate_talking_points(state: MeetingPrepState) -> dict:
    """Generate personalized talking points."""
    prompt = f"""Generate 5-7 talking points for this meeting.

Meeting with: {state['person_name']} at {state['company']}
Purpose: {state['meeting_purpose']}
Your background: {state['your_background']}

About them:
{state['person_research']}

About their company:
{state['company_research']}

Make talking points specific — connect YOUR skills to THEIR needs.
Not generic stuff like "show enthusiasm". Real, actionable points.
Number each one."""

    response = llm.invoke([
        SystemMessage(content="You generate sharp, specific talking points for meetings. No fluff."),
        HumanMessage(content=prompt)
    ])

    return {
        "talking_points": response.content,
        "messages": [AIMessage(content="[Prep Agent] Generated talking points")]
    }


def generate_agenda(state: MeetingPrepState) -> dict:
    """Generate a meeting agenda."""
    prompt = f"""Write a 30-minute meeting agenda for:

Meeting with: {state['person_name']} at {state['company']}
Purpose: {state['meeting_purpose']}

Talking points to cover:
{state['talking_points']}

Format:
- Time allocation for each section
- Who leads each section
- Key questions to ask
- One unexpected question that shows you did your homework

Keep it practical. This is a real agenda, not a template."""

    response = llm.invoke([
        SystemMessage(content="You write practical meeting agendas. Be specific with time allocations."),
        HumanMessage(content=prompt)
    ])

    return {
        "agenda": response.content,
        "messages": [AIMessage(content="[Prep Agent] Generated agenda")]
    }


def generate_followup(state: MeetingPrepState) -> dict:
    """Generate a follow-up email template."""
    prompt = f"""Write a follow-up email template for after this meeting.

Met with: {state['person_name']} at {state['company']}
Purpose: {state['meeting_purpose']}

Key talking points discussed:
{state['talking_points']}

The email should:
- Thank them specifically (not generically)
- Reference 1-2 specific things discussed
- Propose a clear next step
- Be under 150 words
- Sound human, not corporate

Write it ready to send — just needs personalizing with specifics from the actual meeting."""

    response = llm.invoke([
        SystemMessage(content="You write short, warm, professional follow-up emails. Not corporate speak."),
        HumanMessage(content=prompt)
    ])

    return {
        "followup_email": response.content,
        "messages": [AIMessage(content="[Prep Agent] Generated follow-up email template")]
    }


def evaluate_prep(state: MeetingPrepState) -> dict:
    """Evaluate the overall meeting prep quality."""
    prompt = f"""Evaluate this meeting prep package. Score it 1-10.

Meeting: {state['person_name']} at {state['company']} — {state['meeting_purpose']}

Talking Points:
{state['talking_points']}

Agenda:
{state['agenda']}

Follow-up Email:
{state['followup_email']}

Check:
1. Are talking points specific to THIS meeting or could they apply to any meeting?
2. Does the agenda have realistic time allocations?
3. Does the follow-up email sound human?
4. Is there evidence of actual research, not just generic advice?

Respond with ONLY JSON:
{{"score": 1-10, "feedback": "specific improvements needed"}}"""

    response = llm.invoke([
        SystemMessage(content="You evaluate meeting prep materials. Be tough but fair. Score >= 7 means good enough."),
        HumanMessage(content=prompt)
    ])

    try:
        raw = response.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)
        score = result.get("score", 5)
        feedback = result.get("feedback", "No specific feedback")
    except (json.JSONDecodeError, KeyError):
        score = 6
        feedback = "Could not parse evaluation — defaulting to revision"

    return {
        "eval_score": score,
        "eval_feedback": feedback,
        "revision_count": state.get("revision_count", 0) + 1,
        "messages": [AIMessage(content=f"[Evaluator] Score: {score}/10 — {feedback}")]
    }


def revise_talking_points(state: MeetingPrepState) -> dict:
    """Revise talking points based on evaluator feedback."""
    prompt = f"""Revise these talking points based on feedback.

Current talking points:
{state['talking_points']}

Evaluator feedback:
{state['eval_feedback']}

Meeting context: {state['person_name']} at {state['company']} — {state['meeting_purpose']}

Make them more specific and actionable. Address the feedback directly."""

    response = llm.invoke([
        SystemMessage(content="Improve these talking points based on feedback. Be more specific."),
        HumanMessage(content=prompt)
    ])

    return {
        "talking_points": response.content,
        "messages": [AIMessage(content="[Prep Agent] Revised talking points based on feedback")]
    }


def compile_report(state: MeetingPrepState) -> dict:
    """Compile everything into a final report."""
    report = f"""# Meeting Prep: {state['person_name']} at {state['company']}

## Purpose
{state['meeting_purpose']}

## About {state['person_name']}
{state['person_research']}

## About {state['company']}
{state['company_research']}

## Talking Points
{state['talking_points']}

## Meeting Agenda
{state['agenda']}

## Follow-up Email Template
{state['followup_email']}

---
*Prep quality score: {state['eval_score']}/10*
*Revisions: {state.get('revision_count', 0)}*
"""

    # Save to file
    filename = f"meeting_prep_{state['person_name'].lower().replace(' ', '_')}.md"
    with open(filename, "w") as f:
        f.write(report)

    return {
        "full_report": report,
        "messages": [AIMessage(content=f"[Compiler] Report saved to {filename}")]
    }


# Routing

def should_revise(state: MeetingPrepState) -> Literal["revise", "compile"]:
    """Decide whether to revise or move to final compilation."""
    if state.get("eval_score", 0) >= 7:
        return "compile"
    if state.get("revision_count", 0) >= 2:
        return "compile"
    return "revise"


# Build Graph

def build_graph():
    graph = StateGraph(MeetingPrepState)

    graph.add_node("research_person", research_person)
    graph.add_node("research_company", research_company)
    graph.add_node("talking_points", generate_talking_points)
    graph.add_node("agenda", generate_agenda)
    graph.add_node("followup", generate_followup)
    graph.add_node("evaluate", evaluate_prep)
    graph.add_node("revise", revise_talking_points)
    graph.add_node("compile", compile_report)

    
    graph.set_entry_point("research_person")

    
    graph.add_edge("research_person", "research_company")
    graph.add_edge("research_company", "talking_points")
    graph.add_edge("talking_points", "agenda")
    graph.add_edge("agenda", "followup")
    graph.add_edge("followup", "evaluate")

    
    graph.add_conditional_edges("evaluate", should_revise, {
        "revise": "revise",
        "compile": "compile"
    })

   
    graph.add_edge("revise", "evaluate")

   
    graph.add_edge("compile", END)

    
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


# Gradio UI

def build_ui():
    import gradio as gr

    app_graph = build_graph()

    def run_prep(person_name, company, purpose, your_background):
        if not person_name or not company or not purpose:
            return "Please fill in all required fields.", ""

        config = {"configurable": {"thread_id": f"meeting_{person_name.lower().replace(' ', '_')}"}}

        initial_state = {
            "person_name": person_name,
            "company": company,
            "meeting_purpose": purpose,
            "your_background": your_background or "AI/ML Engineer with experience in Python, deep learning, and agentic AI systems.",
            "person_research": "",
            "company_research": "",
            "talking_points": "",
            "agenda": "",
            "followup_email": "",
            "eval_score": 0,
            "eval_feedback": "",
            "revision_count": 0,
            "full_report": "",
            "messages": []
        }

      
        final_state = None
        for state in app_graph.stream(initial_state, config):
            final_state = state

        
        result = app_graph.get_state(config)
        values = result.values

        report = values.get("full_report", "Report generation failed.")
        log_messages = values.get("messages", [])
        log = "\n".join([m.content for m in log_messages if hasattr(m, "content")])

        return report, log

    with gr.Blocks(title="Meeting Prep Sidekick") as app:
        gr.Markdown(
            """
            # Meeting Prep Sidekick
            Enter who you're meeting, where they work, and why — the agent
            researches them, generates talking points, writes an agenda,
            and prepares a follow-up email. An evaluator checks everything.
            """
        )

        with gr.Row():
            with gr.Column(scale=2):
                person_input = gr.Textbox(label="Who are you meeting?", placeholder="e.g. Ed Donner")
                company_input = gr.Textbox(label="Their company", placeholder="e.g. Nebula.io")
                purpose_input = gr.Textbox(label="Meeting purpose", placeholder="e.g. Discussing an ML Engineer role")
                background_input = gr.Textbox(
                    label="Your background (optional)",
                    placeholder="e.g. ML Engineer with 2 years experience in computer vision and deepfake detection",
                    lines=2
                )
                run_btn = gr.Button("Prepare for Meeting", variant="primary")

            with gr.Column(scale=3):
                report_output = gr.Markdown(label="Meeting Prep Report")
                log_output = gr.Textbox(label="Agent Activity Log", lines=8, interactive=False)

        run_btn.click(
            fn=run_prep,
            inputs=[person_input, company_input, purpose_input, background_input],
            outputs=[report_output, log_output]
        )

    return app




if __name__ == "__main__":
    import sys

    if "--ui" in sys.argv:
        app = build_ui()
        app.launch()
    else:
        # Terminal mode
        graph = build_graph()

        initial_state = {
            "person_name": "Mirack",
            "company": "Xapo Bank",
            "meeting_purpose": "Discussing AI Engineer role and showing my portfolio of agent projects",
            "your_background": "ML Engineer with experience in deepfake detection, computer vision, LLM engineering, and building multi-agent systems. Built 8 projects in Ed's LLM course.",
            "person_research": "",
            "company_research": "",
            "talking_points": "",
            "agenda": "",
            "followup_email": "",
            "eval_score": 0,
            "eval_feedback": "",
            "revision_count": 0,
            "full_report": "",
            "messages": []
        }

        config = {"configurable": {"thread_id": "meeting_ed_donner"}}

        print("Running Meeting Prep Sidekick...\n")

        for state in graph.stream(initial_state, config):
            node_name = list(state.keys())[0]
            node_output = state[node_name]
            if "messages" in node_output:
                for msg in node_output["messages"]:
                    print(msg.content)

        final = graph.get_state(config)
        print("\n" + "=" * 50)
        print(final.values.get("full_report", "No report generated"))
