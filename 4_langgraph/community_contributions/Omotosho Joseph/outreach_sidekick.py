from typing import Annotated, List, Any, Optional, Dict
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from outreach_tools import get_all_tools
import uuid
from datetime import datetime

load_dotenv(override=True)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class OutreachState(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    policy_violated: bool
    policy_reason: Optional[str]


# ---------------------------------------------------------------------------
# Structured outputs
# ---------------------------------------------------------------------------

class PolicyCheckOutput(BaseModel):
    is_violation: bool = Field(description="Whether the request violates outreach policies")
    reason: str = Field(description="Explanation of why the request was flagged or approved")


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Detailed feedback on the outreach email quality")
    success_criteria_met: bool = Field(
        description="Whether the success criteria have been met"
    )
    user_input_needed: bool = Field(
        description="True if the user needs to provide more details, "
        "clarifications, or the assistant seems stuck"
    )


# ---------------------------------------------------------------------------
# OutreachSidekick
# ---------------------------------------------------------------------------

class OutreachSidekick:

    def __init__(self):
        self.worker_llm_with_tools = None
        self.policy_llm = None
        self.evaluator_llm = None
        self.tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()

    # -- lifecycle -----------------------------------------------------------

    async def setup(self):
        self.tools = get_all_tools()

        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)

        self.policy_llm = ChatOpenAI(model="gpt-4o-mini").with_structured_output(
            PolicyCheckOutput
        )
        self.evaluator_llm = ChatOpenAI(model="gpt-4o-mini").with_structured_output(
            EvaluatorOutput
        )

        await self.build_graph()

    # -- nodes ---------------------------------------------------------------

    def policy_checker(self, state: OutreachState) -> Dict[str, Any]:
        """Gate node: blocks requests that violate outreach ethics."""
        last_human_msg = None
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                last_human_msg = msg.content
                break

        if not last_human_msg:
            return {"policy_violated": False, "policy_reason": None}

        result = self.policy_llm.invoke([
            SystemMessage(content=(
                "You are an outreach policy checker. Flag requests that involve:\n"
                "1. Impersonation — pretending to be someone you're not\n"
                "2. Deceptive claims — 'guaranteed ROI', '#1 product', "
                "unverifiable superlatives\n"
                "3. PII exposure — personal emails, phone numbers, SSNs\n"
                "4. Harassment, threats, or manipulation\n"
                "5. Spam intent — mass unsolicited messaging\n\n"
                "Legitimate cold outreach with honest value propositions is fine."
            )),
            HumanMessage(
                content=f"Check this outreach request:\n\n{last_human_msg}"
            ),
        ])

        if result.is_violation:
            return {
                "policy_violated": True,
                "policy_reason": result.reason,
                "messages": [
                    AIMessage(
                        content=f"Request blocked by policy checker: {result.reason}"
                    )
                ],
            }
        return {"policy_violated": False, "policy_reason": None}

    def worker(self, state: OutreachState) -> Dict[str, Any]:
        """Main workhorse: researches prospects, drafts variants, selects the best."""
        system_prompt = (
            "You are a research-backed outreach email specialist. You create "
            "high-quality, personalized cold outreach emails grounded in real "
            "research.\n\n"
            "Your workflow:\n"
            "1. RESEARCH — Use the search tool 2-4 times to learn about the "
            "target company, person, role, industry, and recent news.\n"
            "2. SYNTHESIZE — Identify key facts, promising angles, "
            "risks/unknowns, and a strong call-to-action.\n"
            "3. DRAFT — Write THREE email variants:\n"
            "   - Professional: data-driven, credible, references specifics\n"
            "   - Creative: pattern-interrupt hook, human tone, stands out\n"
            "   - Concise: 3-4 sentences max, every word earns its place\n"
            "4. SELECT — Pick the single best variant and present it clearly.\n"
            "5. SAVE — Use save_outreach_email to save the winner as HTML.\n\n"
            f"Current date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"Success criteria:\n{state['success_criteria']}\n\n"
            "Rules:\n"
            "- ALWAYS research before drafting — never fabricate facts.\n"
            "- Ground claims in information from your searches.\n"
            "- Include a clear, specific call-to-action.\n"
            "- If you have a question, state it as 'Question: ...'\n"
            "- When finished, present all three drafts, explain your pick, "
            "then save it."
        )

        if state.get("feedback_on_work"):
            system_prompt += (
                "\n\nThe evaluator rejected your previous attempt. Feedback:\n"
                f"{state['feedback_on_work']}\n"
                "Revise accordingly — you may need additional research or a "
                "different angle."
            )

        messages = list(state["messages"])
        found_system = False
        for msg in messages:
            if isinstance(msg, SystemMessage):
                msg.content = system_prompt
                found_system = True
        if not found_system:
            messages = [SystemMessage(content=system_prompt)] + messages

        response = self.worker_llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def evaluator(self, state: OutreachState) -> Dict[str, Any]:
        """Judges the worker's output against outreach quality standards."""
        last_response = state["messages"][-1].content

        eval_result = self.evaluator_llm.invoke([
            SystemMessage(content=(
                "You evaluate cold outreach emails against quality standards.\n\n"
                "Dimensions:\n"
                "1. Research depth — grounded in specific, real facts?\n"
                "2. Personalization — feels written for THIS person/company?\n"
                "3. Value proposition — compelling reason to reply?\n"
                "4. Call-to-action — specific, low-friction next step?\n"
                "5. Tone & length — matches what was requested?\n"
                "6. Policy compliance — no deception or manipulation?\n"
                "7. Success criteria — meets the user's requirements?\n\n"
                "Be constructive but honest. Reject generic, unresearched emails."
            )),
            HumanMessage(content=(
                f"Conversation:\n{self._fmt(state['messages'])}\n\n"
                f"Success criteria: {state['success_criteria']}\n\n"
                f"Final response to evaluate:\n{last_response}\n\n"
                "If the assistant says they saved a file or did research, "
                "give benefit of the doubt. Reject if the email is generic "
                "or clearly misses criteria."
                + (
                    f"\n\nYour previous feedback: {state['feedback_on_work']}\n"
                    "If the same mistakes repeat, set user_input_needed to true."
                    if state.get("feedback_on_work") else ""
                )
            )),
        ])

        return {
            "messages": [
                AIMessage(content=f"Evaluator: {eval_result.feedback}")
            ],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }

    # -- routers -------------------------------------------------------------

    def route_after_policy(self, state: OutreachState) -> str:
        return "END" if state.get("policy_violated") else "worker"

    def worker_router(self, state: OutreachState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "evaluator"

    def route_after_evaluation(self, state: OutreachState) -> str:
        if state.get("success_criteria_met") or state.get("user_input_needed"):
            return "END"
        return "worker"

    # -- helpers -------------------------------------------------------------

    def _fmt(self, messages: List[Any]) -> str:
        parts = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                parts.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                parts.append(f"Assistant: {msg.content or '[Tool use]'}")
        return "\n\n".join(parts)

    # -- graph ---------------------------------------------------------------

    async def build_graph(self):
        gb = StateGraph(OutreachState)

        gb.add_node("policy_checker", self.policy_checker)
        gb.add_node("worker", self.worker)
        gb.add_node("tools", ToolNode(tools=self.tools))
        gb.add_node("evaluator", self.evaluator)

        gb.add_edge(START, "policy_checker")
        gb.add_conditional_edges(
            "policy_checker",
            self.route_after_policy,
            {"worker": "worker", "END": END},
        )
        gb.add_conditional_edges(
            "worker",
            self.worker_router,
            {"tools": "tools", "evaluator": "evaluator"},
        )
        gb.add_edge("tools", "worker")
        gb.add_conditional_edges(
            "evaluator",
            self.route_after_evaluation,
            {"worker": "worker", "END": END},
        )

        self.graph = gb.compile(checkpointer=self.memory)

    # -- public interface ----------------------------------------------------

    async def run_superstep(self, message, success_criteria, history):
        config = {"configurable": {"thread_id": self.sidekick_id}}

        state = {
            "messages": message,
            "success_criteria": (
                success_criteria
                or "Research-backed, personalized, under 200 words, with a clear CTA"
            ),
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "policy_violated": False,
            "policy_reason": None,
        }

        result = await self.graph.ainvoke(state, config=config)

        user_msg = {"role": "user", "content": message}

        if result.get("policy_violated"):
            block_msg = {
                "role": "assistant",
                "content": (
                    f"Policy violation: "
                    f"{result.get('policy_reason', 'Request blocked')}"
                ),
            }
            return history + [user_msg, block_msg]

        reply = {"role": "assistant", "content": result["messages"][-2].content}
        feedback = {"role": "assistant", "content": result["messages"][-1].content}
        return history + [user_msg, reply, feedback]
