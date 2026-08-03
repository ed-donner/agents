"""
Marketing Website Team Sidekick.

Team:
- Backend worker: APIs + DB for contact/subscription.
- Frontend worker: React UI with Home / About Us / Contact Us, carousel, forms.
- QA worker: tests navigation and flows.
- Manager/evaluator: assigns work in phases and decides when the goal is met.
"""

from typing import Any, Dict, List, Optional

from typing_extensions import Annotated
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from .states import WebsiteState
from .sidekick_tools import playwright_tools, other_tools
from .backend_worker import build_backend_system_message
from .frontend_worker import build_frontend_system_message
from .qa_worker import build_qa_system_message
from .manager import ManagerOutput, build_manager_system_message

import uuid
import asyncio


load_dotenv(override=True)


class MarketingWebsiteSidekick:
    """
    Multi-worker LangGraph sidekick for building a marketing website.
    """

    def __init__(self) -> None:
        self.tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None

        self.backend_llm = None
        self.frontend_llm = None
        self.qa_llm = None
        self.manager_llm_with_output = None

    async def setup(self) -> None:
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()

        self.backend_llm = ChatOpenAI(model="gpt-4o-mini").bind_tools(self.tools)
        self.frontend_llm = ChatOpenAI(model="gpt-4o-mini").bind_tools(self.tools)
        self.qa_llm = ChatOpenAI(model="gpt-4o-mini").bind_tools(self.tools)

        # Use OpenAI for the manager/evaluator as well, to avoid Anthropic model
        # availability issues in this environment.
        manager_llm = ChatOpenAI(model="gpt-4o-mini")
        self.manager_llm_with_output = manager_llm.with_structured_output(ManagerOutput)

        await self.build_graph()

    # ------------------ Workers ------------------ #

    def backend_worker(self, state: WebsiteState) -> Dict[str, Any]:
        messages = state["messages"]
        system = build_backend_system_message(state)
        messages = self._inject_or_replace_system_message(messages, system)
        response = self.backend_llm.invoke(messages)
        return {"messages": [response], "last_worker": "backend"}

    def frontend_worker(self, state: WebsiteState) -> Dict[str, Any]:
        messages = state["messages"]
        system = build_frontend_system_message(state)
        messages = self._inject_or_replace_system_message(messages, system)
        response = self.frontend_llm.invoke(messages)
        return {"messages": [response], "last_worker": "frontend"}

    def qa_worker(self, state: WebsiteState) -> Dict[str, Any]:
        messages = state["messages"]
        system = build_qa_system_message(state)
        messages = self._inject_or_replace_system_message(messages, system)
        response = self.qa_llm.invoke(messages)
        return {"messages": [response], "last_worker": "qa"}

    # ------------------ Manager / Evaluator ------------------ #

    def manager(self, state: WebsiteState) -> WebsiteState:
        last_message = state["messages"][-1]
        last_text = getattr(last_message, "content", "") or ""

        system_message = build_manager_system_message(state)
        user_message = f"""Conversation so far:
{self._format_conversation(state["messages"])}

The last worker message to consider is:
{last_text}

Remember to choose the next_worker and next_phase, and decide if success_criteria_met or user_input_needed should be true."""

        manager_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        decision = self.manager_llm_with_output.invoke(manager_messages)

        # Update state based on manager decision
        new_state: WebsiteState = {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Manager feedback: {decision.feedback}",
                }
            ],
            "feedback_on_work": decision.feedback,
            "success_criteria_met": decision.success_criteria_met,
            "user_input_needed": decision.user_input_needed,
            "current_phase": decision.next_phase,
            "last_worker": "manager",
            "success_criteria": state["success_criteria"],
        }
        return new_state

    # ------------------ Routers ------------------ #

    def backend_router(self, state: WebsiteState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "manager"

    def frontend_router(self, state: WebsiteState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "manager"

    def qa_router(self, state: WebsiteState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "manager"

    def tools_router(self, state: WebsiteState) -> str:
        return state.get("last_worker") or "manager"

    def manager_router(self, state: WebsiteState) -> str:
        # Decide where to go based on manager's structured decision
        # The manager stores its decision in feedback_on_work; we re-run
        # the manager LLM here to get the same decision in a routing-friendly way.
        system_message = build_manager_system_message(state)
        user_message = f"""Decide the next worker only.

Conversation so far:
{self._format_conversation(state["messages"])}

Return a JSON with next_worker and next_phase."""

        manager_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]
        decision = self.manager_llm_with_output.invoke(manager_messages)
        if decision.next_worker == "backend":
            return "backend"
        if decision.next_worker == "frontend":
            return "frontend"
        if decision.next_worker == "qa":
            return "qa"
        return "END"

    # ------------------ Graph Build ------------------ #

    async def build_graph(self) -> None:
        graph_builder = StateGraph(WebsiteState)

        graph_builder.add_node("backend", self.backend_worker)
        graph_builder.add_node("frontend", self.frontend_worker)
        graph_builder.add_node("qa", self.qa_worker)
        graph_builder.add_node("manager", self.manager)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))

        graph_builder.add_edge(START, "manager")

        graph_builder.add_conditional_edges(
            "backend", self.backend_router, {"tools": "tools", "manager": "manager"}
        )
        graph_builder.add_conditional_edges(
            "frontend", self.frontend_router, {"tools": "tools", "manager": "manager"}
        )
        graph_builder.add_conditional_edges(
            "qa", self.qa_router, {"tools": "tools", "manager": "manager"}
        )

        graph_builder.add_conditional_edges(
            "manager",
            self.manager_router,
            {
                "backend": "backend",
                "frontend": "frontend",
                "qa": "qa",
                "END": END,
            },
        )

        graph_builder.add_conditional_edges(
            "tools",
            self.tools_router,
            {"backend": "backend", "frontend": "frontend", "qa": "qa", "manager": "manager"},
        )

        self.graph = graph_builder.compile(checkpointer=self.memory)

    # ------------------ Public Run API ------------------ #

    async def run_superstep(
        self, message: Any, success_criteria: Optional[str], history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        config = {
            "configurable": {"thread_id": self.sidekick_id},
            "recursion_limit": 80,
        }
        state: WebsiteState = {
            "messages": message,
            "success_criteria": success_criteria
            or "Build a marketing website (Home, About Us, Contact Us) with contact form and subscription integrated with backend and DB.",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "current_phase": "plan",
            "last_worker": None,
        }
        result = await self.graph.ainvoke(state, config=config)
        user = {"role": "user", "content": message}
        reply = {
            "role": "assistant",
            "content": result["messages"][-2].content if len(result["messages"]) >= 2 else "",
        }
        feedback = {
            "role": "assistant",
            "content": result["messages"][-1].content if result["messages"] else "",
        }
        return history + [user, reply, feedback]

    # ------------------ Helpers ------------------ #

    def _inject_or_replace_system_message(
        self, messages: Annotated[List[Any], add_messages], system: str
    ) -> List[Any]:
        found = False
        new_messages = list(messages)
        for m in new_messages:
            if isinstance(m, SystemMessage):
                m.content = system
                found = True
                break
        if not found:
            new_messages = [SystemMessage(content=system)] + new_messages
        return new_messages

    def _format_conversation(self, messages: List[Any]) -> str:
        out = ""
        for m in messages:
            if isinstance(m, HumanMessage):
                out += f"User: {m.content}\n"
            elif isinstance(m, AIMessage):
                out += f"Assistant: {m.content or '[Tool use]'}\n"
        return out

    # ------------------ Cleanup ------------------ #

    def cleanup(self) -> None:
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
                if self.playwright:
                    loop.create_task(self.playwright.stop())
            except RuntimeError:
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())


