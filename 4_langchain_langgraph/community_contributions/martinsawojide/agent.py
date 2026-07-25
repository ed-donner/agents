from __future__ import annotations

import asyncio
import os
from datetime import datetime
from typing import Optional

import logging

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, RemoveMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt

from prompts import countermeasure_prompts, validator_prompts, why_prompts
from report import build_report
from schemas import (
    CountermeasureOutput,
    HypothesisCause,
    InputState,
    OverallState,
    RootCauseDecision,
    WhyHypothesisOutput,
    WhyNode,
    make_why_node,
)
from tools import investigation_tools

load_dotenv(override=True)

_log = logging.getLogger(__name__)


def _write_report(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


class FiveWhysAgent:
    """
    Encapsulates the 5 Whys investigation graph
    """

    def __init__(self) -> None:
        self.tools: list = []
        self.why_llm = None
        self.hypothesis_llm = None
        self.tools_node = None
        self.validator_llm = None
        self.countermeasure_llm = None
        self.graph = None
        self.memory: Optional[AsyncSqliteSaver] = None
        self._memory_ctx = None
        self._domain: str = "manufacturing"
        self._equipment_context: str = ""

    def _require_setup(self) -> None:
        if self.graph is None:
            raise RuntimeError("Call await agent.setup() before using this agent.")

    async def setup(self, domain: str = "manufacturing", equipment_context: str = "") -> None:
        """Initialise tools, LLMs, and compile the graph."""
        self._domain = domain
        self._equipment_context = equipment_context

        self.tools = await investigation_tools()
        self.tools_node = ToolNode(self.tools)

        _openrouter = dict(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        base_llm = ChatOpenAI(model="openai/gpt-4o-mini", temperature=0, **_openrouter)
        why_base_llm = ChatOpenAI(model="anthropic/claude-3.5-haiku", temperature=0, **_openrouter)
        self.why_llm = why_base_llm.bind_tools(self.tools)
        self.hypothesis_llm = base_llm.with_structured_output(WhyHypothesisOutput)
        self.validator_llm = base_llm.with_structured_output(RootCauseDecision)
        self.countermeasure_llm = base_llm.with_structured_output(CountermeasureOutput)

        os.makedirs("investigations", exist_ok=True)
        self._memory_ctx = AsyncSqliteSaver.from_conn_string("investigations/memory.db")
        self.memory = await self._memory_ctx.__aenter__()
        await self._build_graph()

    async def cleanup(self) -> None:
        """Close the SQLite checkpointer connection."""
        if self._memory_ctx is not None:
            await self._memory_ctx.__aexit__(None, None, None)
            self._memory_ctx = None
            self.memory = None

    async def start_investigation(
        self,
        phenomenon: str,
        investigation_id: str,
        domain: Optional[str] = None,
        equipment_context: Optional[str] = None,
        max_depth: int = 5,
    ) -> dict:
        """Begin a new investigation; runs until the first gemba_check interrupt."""
        self._require_setup()
        if domain is not None:
            self._domain = domain
        if equipment_context is not None:
            self._equipment_context = equipment_context
        config = {"configurable": {"thread_id": investigation_id}}
        initial: InputState = {
            "phenomenon": phenomenon,
            "domain": self._domain,
            "equipment_context": self._equipment_context,
            "domain_context": f"Domain: {self._domain}. {self._equipment_context}".strip(),
            "max_depth": max_depth,
            "investigation_id": investigation_id,
        }
        result = await self.graph.ainvoke(initial, config=config)
        return await self._format_result(result, investigation_id)

    async def submit_gemba_result(
        self, investigation_id: str, result: str, notes: str
    ) -> dict:
        """Resume the graph after a human Gemba Check.

        result : "OK" or "NOK"
        notes  : operator's physical observations
        """
        self._require_setup()
        config = {"configurable": {"thread_id": investigation_id}}
        state = await self.graph.ainvoke(
            Command(resume={"result": result.upper(), "notes": notes}),
            config=config,
        )
        return await self._format_result(state, investigation_id)

    async def get_investigation_tree(self, investigation_id: str) -> list[WhyNode]:
        """Return the current why_nodes tree for the given investigation."""
        self._require_setup()
        config = {"configurable": {"thread_id": investigation_id}}
        snapshot = await self.graph.aget_state(config)
        return snapshot.values.get("why_nodes", [])

    async def _build_graph(self) -> None:
        builder = StateGraph(OverallState, input=InputState)

        builder.add_node("intake", self.intake)
        builder.add_node("why_generator", self.why_generator)
        builder.add_node("why_tools", self.tools_node)
        builder.add_node("gemba_dispatcher", self.gemba_dispatcher)
        builder.add_node("gemba_check", self.gemba_check)
        builder.add_node("branch_closer", self.branch_closer)
        builder.add_node("root_cause_validator", self.root_cause_validator)
        builder.add_node("countermeasure_generator", self.countermeasure_generator)
        builder.add_node("check_complete", self.check_complete_node)
        builder.add_node("report_generator", self.report_generator)

        builder.add_edge(START, "intake")
        builder.add_edge("intake", "why_generator")
        builder.add_conditional_edges(
            "why_generator",
            self._why_router,
            {"tools": "why_tools", "dispatch": "gemba_dispatcher"},
        )
        builder.add_edge("why_tools", "why_generator")
        builder.add_edge("gemba_dispatcher", "gemba_check")
        builder.add_conditional_edges(
            "gemba_check",
            self._gemba_router,
            {"OK": "branch_closer", "NOK": "root_cause_validator"},
        )
        builder.add_edge("branch_closer", "check_complete")
        builder.add_conditional_edges(
            "root_cause_validator",
            self._validate_router,
            {"countermeasure": "countermeasure_generator", "deeper": "why_generator"},
        )
        builder.add_edge("countermeasure_generator", "check_complete")
        builder.add_conditional_edges(
            "check_complete",
            self._check_complete_router,
            {"dispatch": "gemba_dispatcher", "report": "report_generator"},
        )
        builder.add_edge("report_generator", END)

        self.graph = builder.compile(
            checkpointer=self.memory,
            interrupt_before=["gemba_check"],
        )

    def intake(self, state: OverallState) -> dict:
        """Validate and initialise tracking fields."""
        return {
            "why_nodes": [],
            "pending_hypotheses": [],
            "active_hypothesis": None,
            "current_depth": 1,
            "current_branch_path": "1",
            "report_path": "",
        }

    async def why_generator(self, state: OverallState) -> dict:
        """Research and propose hypotheses for the current phenomenon or branch."""
        depth = state.get("current_depth", 1)
        branch_path = state.get("current_branch_path", "1")
        phenomenon = state["phenomenon"]
        nodes = state.get("why_nodes", [])

        if depth == 1:
            current_problem = phenomenon
        else:
            parent_nodes = [
                n for n in nodes
                if n["branch_path"] == branch_path and n["gemba_result"] == "NOK"
            ]
            if parent_nodes:
                parent = parent_nodes[-1]
                current_problem = parent["hypothesis"]
                notes = parent.get("gemba_notes", "").strip()
                if notes:
                    current_problem = f"{current_problem} (operator observed: {notes})"
            else:
                current_problem = phenomenon

        domain = state.get("domain") or self._domain
        equipment_context = state.get("equipment_context") or self._equipment_context
        sys_msg, usr_msg = why_prompts(
            domain=domain,
            equipment_context=equipment_context,
            phenomenon=phenomenon,
            depth=depth,
            branch_path=branch_path,
            nodes=nodes,
            domain_context=state.get("domain_context", ""),
            current_problem=current_problem,
        )

        history = list(state.get("messages", []))
        re_entering_after_tools = bool(history) and isinstance(history[-1], ToolMessage)

        if re_entering_after_tools:
            llm_input = [SystemMessage(content=sys_msg)] + history
        else:
            llm_input = [SystemMessage(content=sys_msg), HumanMessage(content=usr_msg)]

        response = await self.why_llm.ainvoke(llm_input)

        if response.tool_calls:
            return {"messages": [response]}

        if not response.content:
            raise ValueError(
                f"why_llm returned no content and no tool calls "
                f"(branch_path={branch_path}, depth={depth}); cannot extract hypotheses."
            )

        parsed: WhyHypothesisOutput = await self.hypothesis_llm.ainvoke(
            [
                SystemMessage(content="Extract the hypotheses and gemba instructions from the following analysis."),
                HumanMessage(content=response.content),
            ]
        )

        pending = [
            {
                "hypothesis": h.cause,
                "branch_path": f"{branch_path}.{idx}" if depth > 1 else str(idx),
                "depth": depth,
                "gemba_instructions": h.gemba_instructions,
                "domain_context": parsed.domain_context,
            }
            for idx, h in enumerate(parsed.hypotheses, start=1)
        ]

        clear_messages = [RemoveMessage(id=m.id) for m in state.get("messages", [])]
        existing_pending = list(state.get("pending_hypotheses", []))

        return {
            "pending_hypotheses": pending + existing_pending,
            "current_depth": depth,
            "current_branch_path": branch_path,
            "messages": clear_messages,
        }

    def gemba_dispatcher(self, state: OverallState) -> dict:
        """Pop the next hypothesis from the queue and set it as active."""
        pending = list(state.get("pending_hypotheses", []))
        if not pending:
            return {"active_hypothesis": None}
        active = pending.pop(0)
        return {
            "pending_hypotheses": pending,
            "active_hypothesis": active,
            "current_depth": active["depth"],
            "current_branch_path": active["branch_path"],
        }

    def gemba_check(self, state: OverallState) -> dict:
        """Interrupt the graph; resume when the operator submits a Gemba result."""
        active = state.get("active_hypothesis") or {}
        response = interrupt({
            "hypothesis": active.get("hypothesis", "No hypothesis set"),
            "gemba_instructions": active.get("gemba_instructions", "Check the equipment directly."),
            "branch_path": active.get("branch_path", ""),
            "depth": active.get("depth", 1),
        })

        raw_result = response.get("result", "NOK").upper()
        operator_declared_root_cause = raw_result == "ROOT_CAUSE"
        result = "NOK" if raw_result in ("NOK", "ROOT_CAUSE") else "OK"
        notes = response.get("notes", "")

        node = make_why_node(
            branch_path=active.get("branch_path", "1"),
            depth=active.get("depth", 1),
            hypothesis=active.get("hypothesis", ""),
        )
        node["gemba_result"] = result
        node["gemba_notes"] = notes

        active_update: dict = {**active, "gemba_result": result, "gemba_notes": notes}
        if operator_declared_root_cause:
            active_update["is_root_cause"] = True

        return {
            "why_nodes": [node],
            "active_hypothesis": active_update,
        }

    def branch_closer(self, state: OverallState) -> dict:
        return {}

    async def root_cause_validator(self, state: OverallState) -> dict:
        """Assess whether the confirmed NOK cause is a root cause or intermediate symptom."""
        active = state.get("active_hypothesis") or {}

        if active.get("is_root_cause"):
            branch_path = active.get("branch_path", "")
            nodes = list(state.get("why_nodes", []))
            for i in range(len(nodes) - 1, -1, -1):
                if nodes[i]["branch_path"] == branch_path:
                    return {"why_nodes": [{**nodes[i], "is_root_cause": True}]}
            return {}
        sys_msg, usr_msg = validator_prompts(
            domain=state.get("domain") or self._domain,
            phenomenon=state["phenomenon"],
            depth=active.get("depth", 1),
            max_depth=state.get("max_depth", 5),
            active=active,
            nodes=state.get("why_nodes", []),
        )

        decision: RootCauseDecision = await self.validator_llm.ainvoke(
            [SystemMessage(content=sys_msg), HumanMessage(content=usr_msg)]
        )

        branch_path = active.get("branch_path", "")
        nodes = list(state.get("why_nodes", []))
        updated_node = None
        for i in range(len(nodes) - 1, -1, -1):
            if nodes[i]["branch_path"] == branch_path:
                updated_node = {**nodes[i], "is_root_cause": decision.is_root_cause}
                break

        result: dict = {
            "active_hypothesis": {
                **active,
                "is_root_cause": decision.is_root_cause,
                "validator_reasoning": decision.reasoning,
                "probe_direction": decision.probe_direction,
                "validator_confidence": decision.confidence,
            }
        }
        if updated_node is not None:
            result["why_nodes"] = [updated_node]
        if not decision.is_root_cause:
            result["current_depth"] = active.get("depth", 1) + 1
        return result

    async def countermeasure_generator(self, state: OverallState) -> dict:
        """Propose a countermeasure for the confirmed root cause."""
        active = state.get("active_hypothesis") or {}
        sys_msg, usr_msg = countermeasure_prompts(
            domain=state.get("domain") or self._domain,
            phenomenon=state["phenomenon"],
            active=active,
        )

        countermeasure: CountermeasureOutput = await self.countermeasure_llm.ainvoke(
            [SystemMessage(content=sys_msg), HumanMessage(content=usr_msg)]
        )

        branch_path = active.get("branch_path", "")
        nodes = list(state.get("why_nodes", []))
        updated_node = None
        for i in range(len(nodes) - 1, -1, -1):
            if nodes[i]["branch_path"] == branch_path:
                updated_node = {**nodes[i], "countermeasure": countermeasure.action}
                break

        result: dict = {
            "active_hypothesis": {
                **active,
                "countermeasure": countermeasure.action,
                "prevention_type": countermeasure.prevention_type,
                "suggested_owner": countermeasure.suggested_owner,
                "deadline_days": countermeasure.deadline_days,
            }
        }
        if updated_node is not None:
            result["why_nodes"] = [updated_node]
        return result

    def check_complete_node(self, state: OverallState) -> dict:
        return {}

    async def report_generator(self, state: OverallState) -> dict:
        """Build and save the markdown investigation report."""
        investigation_id = state.get("investigation_id", "unknown")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        report = build_report(
            investigation_id=investigation_id,
            phenomenon=state["phenomenon"],
            domain_context=state.get("domain_context", ""),
            nodes=state.get("why_nodes", []),
            timestamp=timestamp,
        )
        os.makedirs("investigations", exist_ok=True)
        report_path = f"investigations/{investigation_id}.md"
        await asyncio.to_thread(_write_report, report_path, report)
        return {"report_path": report_path}

    def _why_router(self, state: OverallState) -> str:
        messages = state.get("messages", [])
        if messages and hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
            return "tools"
        return "dispatch"

    def _gemba_router(self, state: OverallState) -> str:
        active = state.get("active_hypothesis") or {}
        return "OK" if active.get("gemba_result", "NOK") == "OK" else "NOK"

    def _validate_router(self, state: OverallState) -> str:
        active = state.get("active_hypothesis") or {}
        depth = active.get("depth", 1)
        max_depth = state.get("max_depth", 5)
        remaining = state.get("remaining_steps", 999)
        if active.get("is_root_cause", False) or depth > max_depth or remaining <= 5:
            return "countermeasure"
        return "deeper"

    def _check_complete_router(self, state: OverallState) -> str:
        return "dispatch" if state.get("pending_hypotheses") else "report"

    async def _format_result(self, state: dict, investigation_id: str) -> dict:
        """Normalise graph output state into a consistent dict for the UI."""
        active = state.get("active_hypothesis") or {}
        snapshot = None
        try:
            config = {"configurable": {"thread_id": investigation_id}}
            snapshot = await self.graph.aget_state(config)
        except Exception as exc:
            _log.warning("aget_state failed for investigation %s: %s", investigation_id, exc)

        interrupted = (
            snapshot is not None
            and snapshot.next
            and "gemba_check" in snapshot.next
        )

        return {
            "status": "awaiting_gemba" if interrupted else "complete",
            "active_hypothesis": active.get("hypothesis", ""),
            "gemba_instructions": active.get("gemba_instructions", ""),
            "branch_path": active.get("branch_path", ""),
            "depth": active.get("depth", 0),
            "why_nodes": state.get("why_nodes", []),
            "report_path": state.get("report_path", ""),
            "pending_count": len(state.get("pending_hypotheses", [])),
        }
