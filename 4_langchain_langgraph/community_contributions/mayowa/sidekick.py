import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, Optional

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from typing_extensions import NotRequired, TypedDict

from sidekick_tools import medical_tools, playwright_tools

load_dotenv(override=True)

CHECKPOINT_DB = Path(__file__).resolve().parent / "mayowa_medical_memory.db"
MAX_CLARIFYING_QUESTIONS = 2
GRAPH_RECURSION_LIMIT = 80


class ClarifyingQuestion(BaseModel):
    question: str = Field(
        description="One short medical clarifying question that helps narrow the answer."
    )


class MedicalContextSummary(BaseModel):
    patient_summary: str = Field(description="Short plain-English summary of the case.")
    main_concerns: List[str] = Field(description="Top symptoms, concerns, or questions.")
    risk_factors: List[str] = Field(description="Relevant risk factors or medical background.")
    missing_information: List[str] = Field(
        description="Information gaps that still matter after the clarification phase."
    )
    urgency_assessment: str = Field(
        description="Initial triage impression: routine, urgent, or emergency."
    )


class CarePlan(BaseModel):
    reasoning_focus: List[str] = Field(
        description="Topics the medical assistant should focus on in the next step."
    )
    research_queries: List[str] = Field(
        description="Possible searches or knowledge checks to run before answering."
    )
    response_requirements: List[str] = Field(
        description="Requirements the final answer should satisfy."
    )


class SafetyReviewOutput(BaseModel):
    safe_response: str = Field(
        description="A medically cautious user-facing response ready to send."
    )
    safety_notes: str = Field(
        description="Internal safety notes about risks, red flags, or uncertainty."
    )
    urgency_level: Literal["routine", "urgent", "emergency"] = Field(
        description="Overall urgency after safety review."
    )


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on how to improve the answer.")
    success_criteria_met: bool = Field(description="Whether the answer is good enough to stop.")
    user_input_needed: bool = Field(
        description="Whether the assistant should pause and wait for more user input."
    )


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    final_response: Optional[str]
    safety_notes: Optional[str]
    medical_summary: Optional[str]
    care_plan: Optional[str]
    clarification_complete: NotRequired[bool]
    clarification_questions_asked: NotRequired[int]
    clarification_transcript: NotRequired[str]
    clarification_task_snapshot: NotRequired[str]
    clarification_summary: NotRequired[str]


class MedicalSidekick:
    def __init__(self):
        self.graph = None
        self.tools = None
        self.browser = None
        self.playwright = None
        self.memory = None
        self.memory_context = None
        self.sidekick_id = str(uuid.uuid4())
        self.clarifier_llm = None
        self.summarizer_llm = None
        self.planner_llm = None
        self.researcher_llm_with_tools = None
        self.safety_llm = None
        self.evaluator_llm = None

    async def setup(self):
        if self.memory is None:
            self.memory_context = AsyncSqliteSaver.from_conn_string(str(CHECKPOINT_DB))
            self.memory = await self.memory_context.__aenter__()

        browser_tools, self.browser, self.playwright = await playwright_tools()
        self.tools = browser_tools + await medical_tools()

        base_llm = ChatOpenAI(model="gpt-4o-mini")
        self.clarifier_llm = base_llm.with_structured_output(ClarifyingQuestion)
        self.summarizer_llm = base_llm.with_structured_output(MedicalContextSummary)
        self.planner_llm = base_llm.with_structured_output(CarePlan)
        self.researcher_llm_with_tools = base_llm.bind_tools(self.tools)
        self.safety_llm = base_llm.with_structured_output(SafetyReviewOutput)
        self.evaluator_llm = base_llm.with_structured_output(EvaluatorOutput)

        await self.build_graph()

    @staticmethod
    def _message_text(content: Any) -> str:
        return content if isinstance(content, str) else str(content)

    @staticmethod
    def _format_conversation(messages: List[Any]) -> str:
        lines = []
        for message in messages:
            if isinstance(message, HumanMessage):
                lines.append(f"User: {MedicalSidekick._message_text(message.content)}")
            elif isinstance(message, AIMessage):
                text = MedicalSidekick._message_text(message.content)
                if text:
                    lines.append(f"Assistant: {text}")
        return "\n".join(lines)

    @staticmethod
    def _latest_human_text(messages: List[Any]) -> str:
        for message in reversed(messages):
            if isinstance(message, HumanMessage):
                return MedicalSidekick._message_text(message.content)
        return ""

    @staticmethod
    def _latest_ai_text(messages: List[Any]) -> str:
        for message in reversed(messages):
            if isinstance(message, AIMessage):
                text = MedicalSidekick._message_text(message.content)
                if text:
                    return text
        return ""

    def route_entry(self, state: State) -> Literal["clarifier", "context_summarizer"]:
        if state.get("clarification_complete"):
            return "context_summarizer"
        return "clarifier"

    def clarification_router(
        self, state: State
    ) -> Literal["context_summarizer", "END"]:
        if state.get("clarification_complete"):
            return "context_summarizer"
        return "END"

    def researcher_router(self, state: State) -> Literal["tools", "safety_checker"]:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "safety_checker"

    def evaluation_router(self, state: State) -> Literal["researcher", "END"]:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        return "researcher"

    def clarifier(self, state: State) -> Dict[str, Any]:
        asked = state.get("clarification_questions_asked", 0)
        transcript = state.get("clarification_transcript", "")
        criteria = state["success_criteria"]

        if asked == 0:
            task = self._latest_human_text(state["messages"])
            system = """You are a medical intake assistant.
Ask exactly one short clarifying question before any medical reasoning starts.
Prefer questions about symptoms, duration, severity, age group, relevant conditions, medicines,
pregnancy status when relevant, and urgent red flags. Do not answer the medical question yet."""
            human = f"""Medical question:
{task}

Desired outcome:
{criteria}

Ask question 1 of {MAX_CLARIFYING_QUESTIONS}. Make it the single highest-value question."""
            result = self.clarifier_llm.invoke(
                [SystemMessage(content=system), HumanMessage(content=human)]
            )
            return {
                "messages": [AIMessage(content=f"Before I answer, {result.question}")],
                "clarification_questions_asked": 1,
                "clarification_task_snapshot": task,
                "clarification_transcript": transcript,
            }

        last_answer = self._latest_human_text(state["messages"])
        last_question = self._latest_ai_text(state["messages"])
        updated_transcript = (
            f"{transcript}Question {asked}: {last_question}\nAnswer {asked}: {last_answer}\n"
        )

        if asked >= MAX_CLARIFYING_QUESTIONS:
            task = state.get("clarification_task_snapshot", "")
            summary = (
                "Original medical question:\n"
                f"{task}\n\n"
                "Clarifying answers to use in the rest of the workflow:\n"
                f"{updated_transcript}"
            )
            return {
                "clarification_complete": True,
                "clarification_transcript": updated_transcript,
                "clarification_summary": summary,
            }

        system = """You are a medical intake assistant.
Ask exactly one additional clarifying question. It must build on the prior answer and reduce uncertainty.
Do not answer the medical question yet."""
        human = f"""Use the original question and transcript below.

Original question:
{state.get("clarification_task_snapshot", "")}

Desired outcome:
{criteria}

Transcript:
{updated_transcript}

Ask question {asked + 1} of {MAX_CLARIFYING_QUESTIONS}. Make it different from earlier questions."""
        result = self.clarifier_llm.invoke(
            [SystemMessage(content=system), HumanMessage(content=human)]
        )
        return {
            "messages": [AIMessage(content=f"Thanks. {result.question}")],
            "clarification_questions_asked": asked + 1,
            "clarification_transcript": updated_transcript,
        }

    def context_summarizer(self, state: State) -> Dict[str, Any]:
        system = """You are summarizing a short medical intake conversation for a clinical-style assistant.
Be concise, avoid diagnosing with certainty, and note uncertainty clearly."""
        human = f"""Conversation:
{self._format_conversation(state["messages"])}

Clarification summary:
{state.get("clarification_summary", "None")}
"""
        summary = self.summarizer_llm.invoke(
            [SystemMessage(content=system), HumanMessage(content=human)]
        )
        medical_summary = (
            f"Patient summary: {summary.patient_summary}\n"
            f"Main concerns: {', '.join(summary.main_concerns) or 'None noted'}\n"
            f"Risk factors: {', '.join(summary.risk_factors) or 'None noted'}\n"
            f"Missing info: {', '.join(summary.missing_information) or 'None noted'}\n"
            f"Urgency assessment: {summary.urgency_assessment}"
        )
        return {"medical_summary": medical_summary}

    def care_planner(self, state: State) -> Dict[str, Any]:
        system = """You are designing a lightweight medical reasoning and research plan.
Focus on triage, likely explanation categories, safe self-care advice, and when to seek care."""
        human = f"""Medical summary:
{state.get("medical_summary", "")}

Desired outcome:
{state["success_criteria"]}
"""
        plan = self.planner_llm.invoke(
            [SystemMessage(content=system), HumanMessage(content=human)]
        )
        care_plan = (
            f"Reasoning focus: {', '.join(plan.reasoning_focus)}\n"
            f"Research queries: {', '.join(plan.research_queries)}\n"
            f"Response requirements: {', '.join(plan.response_requirements)}"
        )
        return {"care_plan": care_plan}

    def researcher(self, state: State) -> Dict[str, Any]:
        system = f"""You are a careful medical sidekick, not a replacement for a doctor.
Use tools when needed to gather reliable context, especially for up-to-date guidance.
You must:
- use the clarification answers and medical summary
- avoid giving a certain diagnosis
- mention red flags and when to seek urgent or emergency care
- keep advice general and safety-conscious
- say when professional evaluation is important

Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Medical summary:
{state.get("medical_summary", "")}

Care plan:
{state.get("care_plan", "")}

Success criteria:
{state["success_criteria"]}
"""
        if state.get("feedback_on_work"):
            system += f"""

Evaluator feedback to address before finishing:
{state["feedback_on_work"]}
"""

        messages = state["messages"]
        has_system = False
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system
                has_system = True
                break
        if not has_system:
            messages = [SystemMessage(content=system)] + messages

        response = self.researcher_llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def safety_checker(self, state: State) -> Dict[str, Any]:
        draft = self._latest_ai_text(state["messages"])
        system = """You are a medical safety reviewer.
Rewrite the assistant's draft into a safer user-facing answer.
The final answer must be helpful, calm, and explicit about red flags.
If the situation sounds emergent, tell the user to seek emergency care now.
Do not claim certainty when the information is limited."""
        human = f"""Conversation:
{self._format_conversation(state["messages"])}

Medical summary:
{state.get("medical_summary", "")}

Draft answer to review:
{draft}
"""
        reviewed = self.safety_llm.invoke(
            [SystemMessage(content=system), HumanMessage(content=human)]
        )
        return {
            "messages": [AIMessage(content=reviewed.safe_response)],
            "final_response": reviewed.safe_response,
            "safety_notes": (
                f"Urgency: {reviewed.urgency_level}. Notes: {reviewed.safety_notes}"
            ),
        }

    def evaluator(self, state: State) -> Dict[str, Any]:
        system = """You evaluate whether a medical assistant response is ready to send.
Approve answers that are clear, medically cautious, practical, and matched to the user's question.
Request more user input only when the assistant is explicitly asking for it or is missing critical details."""
        human = f"""Conversation:
{self._format_conversation(state["messages"])}

Success criteria:
{state["success_criteria"]}

Medical summary:
{state.get("medical_summary", "")}

Safety notes:
{state.get("safety_notes", "")}

Final response under review:
{state.get("final_response", "")}
"""
        result = self.evaluator_llm.invoke(
            [SystemMessage(content=system), HumanMessage(content=human)]
        )
        return {
            "feedback_on_work": result.feedback,
            "success_criteria_met": result.success_criteria_met,
            "user_input_needed": result.user_input_needed,
        }

    async def build_graph(self):
        builder = StateGraph(State)
        builder.add_node("clarifier", self.clarifier)
        builder.add_node("context_summarizer", self.context_summarizer)
        builder.add_node("care_planner", self.care_planner)
        builder.add_node("researcher", self.researcher)
        builder.add_node("tools", ToolNode(tools=self.tools))
        builder.add_node("safety_checker", self.safety_checker)
        builder.add_node("evaluator", self.evaluator)

        builder.add_conditional_edges(
            START,
            self.route_entry,
            {
                "clarifier": "clarifier",
                "context_summarizer": "context_summarizer",
            },
        )
        builder.add_conditional_edges(
            "clarifier",
            self.clarification_router,
            {
                "context_summarizer": "context_summarizer",
                "END": END,
            },
        )
        builder.add_edge("context_summarizer", "care_planner")
        builder.add_edge("care_planner", "researcher")
        builder.add_conditional_edges(
            "researcher",
            self.researcher_router,
            {
                "tools": "tools",
                "safety_checker": "safety_checker",
            },
        )
        builder.add_edge("tools", "researcher")
        builder.add_edge("safety_checker", "evaluator")
        builder.add_conditional_edges(
            "evaluator",
            self.evaluation_router,
            {
                "researcher": "researcher",
                "END": END,
            },
        )

        self.graph = builder.compile(checkpointer=self.memory)

    async def run_superstep(
        self, message: str, success_criteria: str, history: Optional[List[Dict[str, str]]]
    ):
        history = history or []
        state = {
            "messages": [HumanMessage(content=message)],
            "success_criteria": success_criteria
            or (
                "Give a medically cautious explanation, helpful next steps, red flags, "
                "and say when to seek professional care."
            ),
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "final_response": None,
            "safety_notes": None,
            "medical_summary": None,
            "care_plan": None,
        }
        config = {
            "configurable": {"thread_id": self.sidekick_id},
            "recursion_limit": GRAPH_RECURSION_LIMIT,
        }
        result = await self.graph.ainvoke(state, config=config)
        assistant_reply = result.get("final_response") or self._latest_ai_text(result["messages"])
        return history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": assistant_reply},
        ]

    async def _cleanup_async(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        if self.memory_context:
            await self.memory_context.__aexit__(None, None, None)
            self.memory_context = None
            self.memory = None

    def cleanup(self):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._cleanup_async())
        except RuntimeError:
            asyncio.run(self._cleanup_async())
