"""
Study quiz from your notes — LangGraph with conditional routing:
generate questions → evaluate answers → wrong (first time) → hint → retry;
wrong (after hint) or correct → next question.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, List, Literal, Optional, TypedDict

from dotenv import load_dotenv
import gradio as gr
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field


# Repo root first, then this folder — same key in both: root wins (avoids a stale local key masking agents/.env).
_here = Path(__file__).resolve().parent
_repo_root = _here.parent.parent.parent
load_dotenv(_repo_root / ".env", override=False)
load_dotenv(_here / ".env", override=False)


def _gemini_api_key() -> str | None:
    raw = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    # .env mistakes: wrapped in quotes, trailing spaces, placeholder left in place
    key = raw.strip().strip('"').strip("'")
    if key.lower() in ("", "your-gemini-key-here", "none"):
        return None
    return key or None


def _llm() -> ChatGoogleGenerativeAI:
    key = _gemini_api_key()
    # gemini-1.5-* IDs often 404 on current API; stable text model per Google docs is 2.5 Flash.
    model = (os.getenv("GEMINI_MODEL") or "gemini-2.5-flash").strip()
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=0,
        google_api_key=key,
    )


def _api_err_message(exc: BaseException) -> str:
    text = str(exc).lower()
    if (
        "api_key_invalid" in text
        or "api key not valid" in text
        or ("invalid_argument" in text and "api key" in text)
    ):
        return (
            "Google rejected the API key (API_KEY_INVALID). "
            "Create a new key at https://aistudio.google.com/apikey (Generative Language API), "
            "put it in GEMINI_API_KEY or GOOGLE_API_KEY with no spaces or extra quotes, "
            "restart the app, and ensure you are not using a different Google Cloud key type."
        )
    if "404" in str(exc) or "not_found" in text:
        return (
            "Model not found for this API (often retired name). "
            "Set GEMINI_MODEL=gemini-2.5-flash or gemini-flash-latest in .env, "
            "or see https://ai.google.dev/gemini-api/docs/models"
        )
    if "429" in str(exc) or "resource_exhausted" in text or "quota" in text:
        return (
            "Gemini quota or rate limit hit. Wait and retry, try GEMINI_MODEL=gemini-2.5-flash-lite, "
            "or check https://ai.dev/rate-limit and billing in Google AI Studio."
        )
    return f"Model API error: {exc}"[:800]


class QuizItem(BaseModel):
    question: str = Field(description="Clear exam-style question from the notes.")
    model_answer: str = Field(
        description="Ideal short answer the student should approximate."
    )


class QuizBatch(BaseModel):
    items: List[QuizItem] = Field(
        min_length=3,
        max_length=3,
        description="Exactly three questions based only on the notes.",
    )


class GradeResult(BaseModel):
    is_correct: bool = Field(
        description="True if the student's answer is substantially correct."
    )
    short_feedback: str = Field(description="One sentence for the student.")
    hint_if_wrong: Optional[str] = Field(
        default=None,
        description="If wrong, a nudge without giving away the full answer.",
    )


class QuizState(TypedDict, total=False):
    notes: str
    questions: List[dict]
    q_index: int
    user_answer: str
    hints_for_current: int
    score: int
    log: str
    feedback: str
    finished: bool


def generate_questions_node(state: QuizState) -> dict[str, Any]:
    notes = (state.get("notes") or "").strip()
    if len(notes) < 80:
        return {
            "questions": [],
            "log": "Please paste at least a few sentences of notes (80+ characters).",
            "feedback": "",
            "finished": False,
        }
    llm = _llm().with_structured_output(QuizBatch)
    msg = HumanMessage(
        content=(
            "Create exactly 3 study questions that can be answered using ONLY the notes below. "
            "Vary difficulty slightly. For each, include a concise model_answer.\n\n"
            f"NOTES:\n{notes}"
        )
    )
    try:
        batch = llm.invoke([msg])
    except Exception as e:
        return {
            "questions": [],
            "log": _api_err_message(e),
            "feedback": "",
            "finished": False,
        }
    items = [q.model_dump() for q in batch.items]
    return {
        "questions": items,
        "q_index": 0,
        "hints_for_current": 0,
        "score": 0,
        "finished": False,
        "user_answer": "",
        "log": f"Generated {len(items)} questions from your notes.",
        "feedback": "Quiz ready — answer the first question and click Submit answer.",
    }


def evaluate_node(state: QuizState) -> dict[str, Any]:
    questions = state.get("questions") or []
    idx = int(state.get("q_index") or 0)
    if idx >= len(questions):
        return {
            "log": "No active question.",
            "feedback": "",
            "finished": True,
            "_eval_skipped": True,
        }
    q = questions[idx]
    user_ans = (state.get("user_answer") or "").strip()
    if not user_ans:
        return {
            "log": "Type an answer before submitting.",
            "feedback": "Enter your answer in the box below.",
            "_eval_skipped": True,
        }

    llm = _llm().with_structured_output(GradeResult)
    msg = HumanMessage(
        content=(
            f"Question: {q['question']}\n"
            f"Reference answer: {q['model_answer']}\n"
            f"Student answer: {user_ans}\n\n"
            "Decide if the student is substantially correct. "
            "If wrong, set hint_if_wrong to a small hint (not the full answer)."
        )
    )
    try:
        grade = llm.invoke([msg])
    except Exception as e:
        return {
            "log": _api_err_message(e),
            "feedback": "Could not grade this answer. Check log and try again.",
            "_eval_skipped": True,
        }
    log = (
        f"Q{idx + 1}: {'Correct' if grade.is_correct else 'Incorrect'} — "
        f"{grade.short_feedback}"
    )
    return {
        "log": log,
        "feedback": grade.short_feedback,
        "_last_is_correct": grade.is_correct,
        "_hint_if_wrong": grade.hint_if_wrong or "",
        "_eval_skipped": False,
    }


def give_hint_node(state: QuizState) -> dict[str, Any]:
    hints = int(state.get("hints_for_current") or 0)
    hint = (state.get("_hint_if_wrong") or "").strip() or "Re-read the question and try again."
    return {
        "hints_for_current": hints + 1,
        "feedback": f"Hint: {hint}",
        "log": f"[HINT] {hint}",
    }


def next_question_node(state: QuizState) -> dict[str, Any]:
    questions = state.get("questions") or []
    idx = int(state.get("q_index") or 0)
    hints = int(state.get("hints_for_current") or 0)
    last_correct = bool(state.get("_last_is_correct"))

    score = int(state.get("score") or 0)
    if last_correct:
        score += 1

    next_idx = idx + 1
    if next_idx >= len(questions):
        return {
            "q_index": next_idx,
            "hints_for_current": 0,
            "score": score,
            "finished": True,
            "user_answer": "",
            "feedback": f"Finished! Score: {score}/{len(questions)}",
            "log": f"Quiz complete. Final score: {score}/{len(questions)}.",
            "_last_is_correct": False,
        }

    return {
        "q_index": next_idx,
        "hints_for_current": 0,
        "score": score,
        "finished": False,
        "user_answer": "",
        "feedback": f"Next question ({next_idx + 1}/{len(questions)}).",
        "log": f"Moving to question {next_idx + 1} of {len(questions)}.",
        "_last_is_correct": False,
    }


def route_start(state: QuizState) -> Literal["generate", "evaluate"]:
    if not state.get("questions"):
        return "generate"
    return "evaluate"


def route_after_evaluate(
    state: QuizState,
) -> Literal["give_hint", "next_question", "done"]:
    if state.get("_eval_skipped") or state.get("finished"):
        return "done"
    questions = state.get("questions") or []
    idx = int(state.get("q_index") or 0)
    if idx >= len(questions):
        return "done"
    if state.get("_last_is_correct") is True:
        return "next_question"
    hints = int(state.get("hints_for_current") or 0)
    if hints == 0:
        return "give_hint"
    return "next_question"


def build_graph():
    g = StateGraph(QuizState)
    g.add_node("generate", generate_questions_node)
    g.add_node("evaluate", evaluate_node)
    g.add_node("give_hint", give_hint_node)
    g.add_node("next_question", next_question_node)

    g.add_conditional_edges(
        START,
        route_start,
        {"generate": "generate", "evaluate": "evaluate"},
    )
    g.add_edge("generate", END)
    g.add_conditional_edges(
        "evaluate",
        route_after_evaluate,
        {
            "give_hint": "give_hint",
            "next_question": "next_question",
            "done": END,
        },
    )
    g.add_edge("give_hint", END)
    g.add_edge("next_question", END)
    return g.compile()


GRAPH = build_graph()


def _current_question_text(state: dict) -> str:
    qs = state.get("questions") or []
    idx = int(state.get("q_index") or 0)
    if not qs or idx >= len(qs):
        return ""
    return f"**Question {idx + 1} of {len(qs)}**\n\n{qs[idx]['question']}"


def run_generate(notes: str):
    if not _gemini_api_key():
        yield (
            "Set GEMINI_API_KEY or GOOGLE_API_KEY in .env or your environment.",
            "",
            "",
            gr.update(interactive=False),
            gr.update(interactive=False),
            {},
        )
        return
    try:
        out = GRAPH.invoke(
            {
                "notes": notes,
                "questions": [],
                "q_index": 0,
                "user_answer": "",
                "hints_for_current": 0,
                "score": 0,
                "log": "",
                "feedback": "",
                "finished": False,
            }
        )
    except Exception as e:
        yield (
            _api_err_message(e),
            "",
            "",
            gr.update(interactive=False),
            gr.update(interactive=False),
            {},
        )
        return
    st = dict(out)
    qs = st.get("questions") or []
    has_quiz = len(qs) > 0
    yield (
        st.get("log", ""),
        st.get("feedback", ""),
        _current_question_text(st),
        gr.update(interactive=has_quiz and not st.get("finished")),
        gr.update(interactive=has_quiz),
        st,
    )


def run_submit_answer(answer: str, state_dict: dict):
    if not _gemini_api_key():
        yield (
            "Set GEMINI_API_KEY or GOOGLE_API_KEY in .env or your environment.",
            "",
            _current_question_text(state_dict or {}),
            gr.update(interactive=False),
            state_dict or {},
        )
        return
    if not state_dict or not state_dict.get("questions"):
        yield (
            "Generate a quiz first.",
            "",
            "",
            gr.update(interactive=False),
            state_dict or {},
        )
        return
    if state_dict.get("finished"):
        yield (
            state_dict.get("log", ""),
            state_dict.get("feedback", "Quiz already finished. Generate a new one."),
            _current_question_text(state_dict),
            gr.update(interactive=False),
            state_dict,
        )
        return

    merged = {**state_dict, "user_answer": answer}
    try:
        out = GRAPH.invoke(merged)
    except Exception as e:
        yield (
            _api_err_message(e),
            "Request failed — see log.",
            _current_question_text(merged),
            gr.update(interactive=True),
            merged,
        )
        return
    st = {**merged, **dict(out)}
    finished = bool(st.get("finished"))
    can_answer = not finished and bool(st.get("questions"))
    yield (
        st.get("log", ""),
        st.get("feedback", ""),
        _current_question_text(st),
        gr.update(interactive=can_answer),
        st,
    )


def main():
    if not _gemini_api_key():
        print("Warning: GEMINI_API_KEY / GOOGLE_API_KEY is not set. Add it to .env or the environment.")

    with gr.Blocks(title="Study Quiz from Notes") as demo:
        gr.Markdown(
            "## Study quiz from your notes\n"
            "Paste notes → generate 3 questions → answer each. "
            "**Wrong once** → you get a **hint**; **wrong again** (or correct) → next question."
        )
        session = gr.State({})

        notes = gr.Textbox(
            label="Your notes",
            lines=12,
            placeholder="Paste lecture notes, a textbook section, or bullet points…",
        )
        gen_btn = gr.Button("Generate quiz", variant="primary")

        log_box = gr.Textbox(label="Log", lines=6, interactive=False)
        feedback = gr.Textbox(label="Feedback", lines=3, interactive=False)
        q_display = gr.Markdown("")

        ans = gr.Textbox(label="Your answer", lines=3, interactive=False)
        sub_btn = gr.Button("Submit answer", variant="secondary", interactive=False)

        gen_btn.click(
            run_generate,
            [notes],
            [log_box, feedback, q_display, ans, sub_btn, session],
        )
        sub_btn.click(
            run_submit_answer,
            [ans, session],
            [log_box, feedback, q_display, sub_btn, session],
        )

    demo.launch(
        inbrowser=True,
        theme=gr.themes.Default(primary_hue="teal"),
    )


if __name__ == "__main__":
    main()
