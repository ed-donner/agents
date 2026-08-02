import os
import uuid
import threading
from datetime import datetime, timezone
import gradio as gr
from dotenv import load_dotenv
from datetime import datetime
from pydantic import BaseModel
from typing import TypedDict, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.utilities import GoogleSerperAPIWrapper
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, RetryPolicy, interrupt
from langgraph.checkpoint.memory import MemorySaver

load_dotenv(override=True)

llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENROUTER_API_KEY"), base_url="https://openrouter.ai/api/v1")

class EvaluationResult(BaseModel):
    grade: Literal["pass", "fail"]
    feedback: str
    score: int

class State(TypedDict):
    raw_job_description: str
    raw_cv: str
    job_title: str | None
    company_name: str | None
    required_skills: list[str] | None
    job_type: Literal["technical", "creative", "management"] | None
    company_research: dict | None
    tailored_cv: str | None
    cover_letter: str | None
    evaluation: dict | None
    iteration_count: int
    human_approved: bool | None
    human_edits: str | None
    application_sent: bool | None
    sent_at: str | None

class ParsedJob(BaseModel):
    job_title: str
    company_name: str
    required_skills: list[str]  

class JobTypeClassification(BaseModel):
    job_type: Literal["technical", "creative", "management", "unknown"]

class TailoredCV(BaseModel):
    tailored_cv: str

class CoverLetter(BaseModel):
    cover_letter: str

def parse_job_description(state: State) -> State:
    llm_with_output = llm.with_structured_output(ParsedJob)
    system_message = """
    You are a job description parser.
    You are given a job description and you need to parse it into a structured format.
    The structured format is as follows:
    {ParsedJob.model_json_schema()}
    """
    messages = [
        SystemMessage(system_message),
        HumanMessage(state["raw_job_description"])
    ]
    parsed_job = llm_with_output.invoke(messages)
    return {
        "job_title": parsed_job.job_title,
        "company_name": parsed_job.company_name,
        "required_skills": parsed_job.required_skills,
    }

def classify_job_type(state: State) -> State:   
    llm_with_output = llm.with_structured_output(JobTypeClassification)
    system_message = """
    You are a job type classifier.
    You are given a job title and required skills and you need to classify it into a job type.
    The job types are: technical, creative, and management.
    If the job title and required skills are not clear, return "unknown". 
    The structured output is as follows:
    {JobTypeClassification.model_json_schema()}
    """
    messages = [
        SystemMessage(system_message),
        HumanMessage(f"Job title: {state['job_title']}\nRequired skills: {state['required_skills']}") 
    ]
    classified_job_type = llm_with_output.invoke(messages)
    return {
        "job_type": classified_job_type.job_type
    }

def research_company(state: State) -> State:
    serper = GoogleSerperAPIWrapper()
    queries = [
        f"{state['company_name']} mission values culture",
        f"{state['company_name']} news 2026",
        f"{state['company_name']} glassdoor reviews",
    ]

    if state["job_type"] == "technical":
        queries.append(f"{state['company_name']} engineering tech stack")
        queries.append(f"{state['company_name']} glassdoor culture engineering team")

    results = {}
    for query in queries:
        results[query] = serper.run(query)

    return {"company_research": results}

def tailor_cv(state: State) -> State:
    llm_with_output = llm.with_structured_output(TailoredCV)
    system_message = """
    You are a CV tailor.
    You are given the raw CV, job title, required skills, job type, and company research and you need to tailor a CV to the job description.
    The CV should be tailored to the job description.
    The structured output is as follows:
    {TailoredCV.model_json_schema()}
    """
    messages = [
        SystemMessage(system_message),
        HumanMessage(f"Raw CV: {state['raw_cv']}\nJob title: {state['job_title']}\nRequired skills: {state['required_skills']}\nJob type: {state['job_type']}\nCompany research: {state['company_research']}")
    ]
    tailored_cv = llm_with_output.invoke(messages)
    return {
        "tailored_cv": tailored_cv.tailored_cv
    }

def write_cover_letter(state: State) -> State:
    llm_with_output = llm.with_structured_output(CoverLetter)
    feedback_section = ""
    if state.get("evaluation"):
        evaluation = state["evaluation"]
        if evaluation["grade"] == "fail":
            feedback_section = f"""
            Previous attempt was rejected. Feedback to address:
            {evaluation["feedback"]}
            Score was: {evaluation["score"]}/100
            """
    system_message = """
    You are a cover letter writer.
    You are given the job title, company name, job type, required skills, company research, and tailored CV and you need to write a cover letter for the job.
    The cover letter should be tailored to the job description.
    The structured output is as follows:
    {CoverLetter.model_json_schema()}
    """
    user_message = f"""
    Write a cover letter for the following:

    Role: {state['job_title']} at {state['company_name']}
    Job Type: {state['job_type']}
    Required Skills: {', '.join(state['required_skills'])}
    
    Company context:
    {state['company_research']}
    
    Candidate CV summary:
    {state['tailored_cv']}
    
    {feedback_section}
    
    Tone guide:
    - technical: precise, stack-aware, results-driven
    - creative: warm, narrative, distinctive voice
    - management: strategic, leadership-focused, outcome-oriented
    """
    messages = [
        SystemMessage(system_message),
        HumanMessage(user_message)
    ]
    cover_letter = llm_with_output.invoke(messages)

    return {
        "cover_letter": cover_letter.cover_letter,
        "iteration_count": state.get("iteration_count", 0) + 1
    }

def evaluate_quality(state: State) -> Command[Literal["human_review", "write_cover_letter"]]:
    llm_with_output = llm.with_structured_output(EvaluationResult)
    if state.get("iteration_count", 0) >= 3:
        return Command(
            update={
                "evaluation": {
                    "grade": "fail",
                    "feedback": "Max iterations reached without passing.",
                    "score": state["evaluation"]["score"]
                }
            },
            goto="human_review"
        )

    system_message = """
    You are a cover letter evaluator.
    You are given a cover letter and you need to evaluate it against the following criteria:
    1. Relevance — does it address the role and required skills?
    2. Personalization — is {state['company_name']} specifically referenced
       in a meaningful way, not just name-dropped?
    3. Tone match — is the tone appropriate for a {state['job_type']} role?
    4. No generic filler — penalize phrases like "I am a passionate 
       self-starter" or "I work well in teams"
    The structured output is as follows:
    {EvaluationResult.model_json_schema()}
    """

    user_message = f"""
    Evaluate this cover letter strictly against these criteria:

    1. Relevance — does it address the role and required skills?
       Role: {state['job_title']}
       Required skills: {', '.join(state['required_skills'])}

    2. Personalization — is {state['company_name']} specifically referenced
       in a meaningful way, not just name-dropped?

    3. Tone match — is the tone appropriate for a {state['job_type']} role?

    4. No generic filler — penalize phrases like "I am a passionate 
       self-starter" or "I work well in teams"

    Cover letter to evaluate:
    {state['cover_letter']}

    Return a grade (pass/fail), a score out of 100, and specific 
    actionable feedback if failing.
    """

    messages = [
        SystemMessage(system_message),
        HumanMessage(user_message)
    ]

    evaluation = llm_with_output.invoke(messages)
    goto = "human_review" if evaluation.grade == "pass" else "write_cover_letter"
    
    return Command(
        update={
            "evaluation": {
                "grade": evaluation.grade,
                "feedback": evaluation.feedback,
                "score": evaluation.score,
            }
        },
        goto=goto,
    )

def human_review(state: State) -> Command[Literal["send_application", END]]:
    human_decision = interrupt({
        "job_title": state["job_title"],
        "company_name": state["company_name"],
        "cover_letter": state["cover_letter"],
        "tailored_cv": state["tailored_cv"],
        "evaluation_score": state["evaluation"]["score"],
        "evaluation_feedback": state["evaluation"]["feedback"],
        "iteration_count": state["iteration_count"],
        "warning": "Max iterations reached — manual review required"
                   if state["iteration_count"] >= 3 else None,
        "action": "Review and approve, edit, or reject this application"
    })

    if human_decision.get("approved"):
        return Command(
            update={
                "human_approved": True,
                "human_edits": human_decision.get("edited_letter", None),
            },
            goto="send_application",
        )
    else:
        return Command(
            update={"human_approved": False},
            goto=END,
        )

def send_application(state: State) -> dict:
    final_letter = state.get("human_edits") or state["cover_letter"]

    print("=" * 60)
    print(f"Sending application to: {state['company_name']}")
    print(f"Role: {state['job_title']}")
    print(f"\n--- Cover Letter ---\n{final_letter}")
    print(f"\n--- Tailored CV ---\n{state['tailored_cv']}")
    print("=" * 60)

    return {
        "application_sent": True,
        "sent_at": datetime.now().isoformat()
    }

def build_graph():
    workflow = StateGraph(State)
 
    workflow.add_node("parse_job_description", parse_job_description)
    workflow.add_node("classify_job_type",     classify_job_type)
    workflow.add_node("research_company", research_company, retry_policy=RetryPolicy(max_attempts=3, initial_interval=1.0))
    workflow.add_node("tailor_cv",           tailor_cv)
    workflow.add_node("write_cover_letter",  write_cover_letter)
    workflow.add_node("evaluate_quality",    evaluate_quality)
    workflow.add_node("human_review",        human_review)
    workflow.add_node("send_application", send_application, retry_policy=RetryPolicy(max_attempts=3, initial_interval=1.0))
 
    workflow.add_edge(START, "parse_job_description")
    workflow.add_edge("parse_job_description", "classify_job_type")
    workflow.add_edge("classify_job_type", "research_company")
    workflow.add_edge("research_company", "tailor_cv")
    workflow.add_edge("tailor_cv", "write_cover_letter")
    workflow.add_edge("write_cover_letter", "evaluate_quality")
    workflow.add_edge("send_application", END)
 
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)

graph = build_graph()

def run_agent(jd: str, cv: str):
    if not jd.strip() or not cv.strip():
        raise gr.Error("Please fill in both fields before running.")
 
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
 
    initial_state = {
        "raw_job_description": jd,
        "raw_cv": cv,
        "job_title": None, "company_name": None, "required_skills": None,
        "seniority_level": None, "tone": None, "job_type": None,
        "company_research": None, "tailored_cv": None, "cover_letter": None,
        "iteration_count": 0, "evaluation": None, "human_approved": None,
        "human_edits": None, "application_sent": None, "sent_at": None,
    }
 
    graph.invoke(initial_state, config)
    sv = graph.get_state(config).values
 
    evaluation = sv.get("evaluation") or {}
    score    = evaluation.get("score", 0)
    grade    = evaluation.get("grade", "—").upper()
    feedback = evaluation.get("feedback", "No feedback provided.")
    icount   = sv.get("iteration_count", 0)
 
    if icount >= 3:
        feedback += "\n\nMax iterations reached — manual review required."
 
    return (
        thread_id,
        sv.get("cover_letter", ""),
        sv.get("tailored_cv", ""),
        f"{score}/100  —  {grade}",
        feedback,
        sv.get("cover_letter", ""),
        gr.update(visible=False),
        gr.update(visible=True),
    )
 
def approve(thread_id: str, edited_letter: str):
    config = {"configurable": {"thread_id": thread_id}}
    graph.invoke(
        Command(resume={"approved": True, "edited_letter": edited_letter or None}),
        config,
    )
    return (
        gr.update(visible=False),
        gr.update(visible=True),
        "Application sent successfully!",
    )
        
def reject(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    graph.invoke(Command(resume={"approved": False}), config)
    return (
        gr.update(visible=False),
        gr.update(visible=True),
        "Application rejected. Graph ended.",
    )
 
def reset():
    return (
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        "", "",                    
        "", "", "", "", "",
    )
 
with gr.Blocks(title="Job Application Assistant") as demo:
 
    thread_id_state = gr.State("")
 
    gr.Markdown("# AI Job Application Assistant")
    gr.Markdown(
        "Paste a job description and your CV. "
        "The agent will tailor your application and pause for your review before sending."
    )
 
    with gr.Group() as input_section:
        with gr.Row():
            jd_input = gr.Textbox(
                label="Job Description",
                lines=12,
                placeholder="Paste the job description here…",
            )
            cv_input = gr.Textbox(
                label="Your CV",
                lines=12,
                placeholder="Paste your CV here…",
            )
        run_btn = gr.Button("▶  Run Agent", variant="primary", size="lg")
 
    with gr.Group(visible=False) as review_section:
        gr.Markdown("## Review Your Application")
        gr.Markdown(
            "The agent has finished drafting. "
            "Review the output below, optionally edit the cover letter, then approve or reject."
        )
 
        with gr.Row():
            score_box    = gr.Textbox(label="Quality Score", interactive=False, scale=1)
            feedback_box = gr.Textbox(label="Evaluator Feedback", interactive=False,
                                      lines=3, scale=3)
 
        with gr.Tabs():
            with gr.Tab("Cover Letter"):
                cover_letter_box = gr.Textbox(
                    label="Generated Cover Letter (read-only)",
                    lines=14, interactive=False,
                )
            with gr.Tab("Tailored CV"):
                tailored_cv_box = gr.Textbox(
                    label="Tailored CV (read-only)",
                    lines=14, interactive=False,
                )
            with gr.Tab("Edit Before Sending"):
                editable_letter = gr.Textbox(
                    label="Edit cover letter (leave unchanged to use AI draft)",
                    lines=14, interactive=True,
                )
 
        with gr.Row():
            approve_btn = gr.Button("Approve & Send", variant="primary")
            reject_btn  = gr.Button("Reject",         variant="stop")
 
    with gr.Group(visible=False) as done_section:
        done_msg    = gr.Markdown("")
        restart_btn = gr.Button("Start a new application")
 
    run_btn.click(
        fn=run_agent,
        inputs=[jd_input, cv_input],
        outputs=[
            thread_id_state,
            cover_letter_box, tailored_cv_box,
            score_box, feedback_box,
            editable_letter,
            input_section, review_section,
        ],
    )
 
    approve_btn.click(
        fn=approve,
        inputs=[thread_id_state, editable_letter],
        outputs=[review_section, done_section, done_msg],
    )
 
    reject_btn.click(
        fn=reject,
        inputs=[thread_id_state],
        outputs=[review_section, done_section, done_msg],
    )
 
    restart_btn.click(
        fn=reset,
        inputs=[],
        outputs=[
            input_section, review_section, done_section,
            jd_input, cv_input,
            cover_letter_box, tailored_cv_box,
            score_box, feedback_box, editable_letter,
        ],
    )
 
if __name__ == "__main__":
    demo.launch(show_error=True)