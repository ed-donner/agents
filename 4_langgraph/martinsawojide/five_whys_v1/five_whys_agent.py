"""
five_whys_agent.py
------------------
Core agent class for the 5 Whys iterative interrogative investigation system.

Graph topology
--------------
START
  → intake            (pure Python: validates and formats initial state)
  → why_generator     (LLM + tools: proposes hypotheses for the current phenomenon)
  → gemba_dispatcher  (pure Python: pops the next hypothesis from the queue)
  → gemba_check       (interrupt: halts and waits for human OK/NOK + notes)
  → gemba_router      (pure Python: routes on gemba_result)
      OK  → branch_closer      → check_complete
      NOK → root_cause_validator → validate_router
                          is_root_cause=True          → countermeasure_generator → check_complete
                          not root + depth < max       → why_generator  (loop deeper)
                          not root + depth >= max      → countermeasure_generator → check_complete
  → check_complete    (pure Python: more pending? → gemba_dispatcher, else → report_generator)
  → report_generator  (LLM + FileManagementToolkit: builds and saves the investigation report)
  → END
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt

from eight_d_report import generate_pdf, populate_8d_content
from five_whys_tools import investigation_tools
from models import (
    CountermeasureOutput,
    InputState,
    OverallState,
    RootCauseDecision,
    WhyHypothesisOutput,
    WhyNode,
    make_why_node,
)

load_dotenv(override=True)


class FiveWhysAgent:
    """
    Encapsulates the entire 5 Whys investigation graph.

    Usage
    -----
    agent = FiveWhysAgent()
    await agent.setup(domain="manufacturing", equipment_context="Hydraulic press line 3")

    # First call — starts the investigation and runs until the first gemba_check interrupt
    result = await agent.start_investigation(
        phenomenon="Glue overflowed from tank",
        investigation_id="inv-001",
    )

    # Subsequent calls — resume after each human Gemba Check
    result = await agent.submit_gemba_result(
        investigation_id="inv-001",
        result="NOK",
        notes="Level gauge switch was physically stuck in OFF position",
    )
    """

    def __init__(self) -> None:
        self.tools: list = []
        self.why_llm = None         # LLM with tools bound — for why_generator
        self.tools_node = None      # ToolNode for why_generator's tool loop
        self.validator_llm = None   # Structured-output LLM — for root_cause_validator
        self.countermeasure_llm = None  # Structured-output LLM — for countermeasure_generator
        self.report_llm = None      # Plain LLM — for report_generator
        self.graph = None
        self.memory: Optional[SqliteSaver] = None
        self._domain: str = "manufacturing"
        self._equipment_context: str = ""

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def setup(
        self,
        domain: str = "manufacturing",
        equipment_context: str = "",
    ) -> None:
        """Initialise tools, LLMs, and compile the graph."""
        self._domain = domain
        self._equipment_context = equipment_context

        self.tools = await investigation_tools()
        self.tools_node = ToolNode(self.tools)

        base_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.why_llm = base_llm.bind_tools(self.tools)

        self.validator_llm = ChatOpenAI(
            model="gpt-4o-mini", temperature=0
        ).with_structured_output(RootCauseDecision)

        self.countermeasure_llm = ChatOpenAI(
            model="gpt-4o-mini", temperature=0
        ).with_structured_output(CountermeasureOutput)

        self.report_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

        os.makedirs("investigations", exist_ok=True)
        self.memory = SqliteSaver.from_conn_string("investigations/memory.db")

        await self.build_graph()

    async def build_graph(self) -> None:
        """Wire all nodes and edges into the compiled StateGraph."""
        builder = StateGraph(OverallState, input=InputState)

        # Nodes
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

        # Edges
        builder.add_edge(START, "intake")
        builder.add_edge("intake", "why_generator")

        # why_generator tool loop
        builder.add_conditional_edges(
            "why_generator",
            self.why_router,
            {"tools": "why_tools", "dispatch": "gemba_dispatcher"},
        )

        builder.add_edge("why_tools", "why_generator")

        builder.add_edge("gemba_dispatcher", "gemba_check")

        builder.add_conditional_edges(
            "gemba_check",
            self.gemba_router,
            {"OK": "branch_closer", "NOK": "root_cause_validator"},
        )

        builder.add_edge("branch_closer", "check_complete")

        builder.add_conditional_edges(
            "root_cause_validator",
            self.validate_router,
            {
                "countermeasure": "countermeasure_generator",
                "deeper": "why_generator",
            },
        )

        builder.add_edge("countermeasure_generator", "check_complete")

        builder.add_conditional_edges(
            "check_complete",
            self.check_complete_router,
            {"dispatch": "gemba_dispatcher", "report": "report_generator"},
        )
        
        builder.add_edge("report_generator", END)

        self.graph = builder.compile(
            checkpointer=self.memory,
            interrupt_before=["gemba_check"],
        )

    async def cleanup(self) -> None:
        """Close the SQLite checkpointer connection."""
        if self.memory is not None:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(asyncio.to_thread(self.memory.conn.close))
            except RuntimeError:
                asyncio.run(asyncio.to_thread(self.memory.conn.close))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def start_investigation(
        self,
        phenomenon: str,
        investigation_id: str,
        domain: Optional[str] = None,
        max_depth: int = 5,
    ) -> dict:
        """
        Begin a new investigation.  Runs until the first gemba_check interrupt.
        Returns a dict with keys: 'status', 'active_hypothesis', 'gemba_instructions',
        'why_nodes', 'report_path'.
        """
        if domain:
            self._domain = domain

        config = {"configurable": {"thread_id": investigation_id}}
        initial: InputState = {
            "phenomenon": phenomenon,
            "domain_context": f"Domain: {self._domain}. {self._equipment_context}".strip(),
            "max_depth": max_depth,
            "investigation_id": investigation_id,
        }
        result = await self.graph.ainvoke(initial, config=config)
        return self._format_result(result)

    async def submit_gemba_result(
        self,
        investigation_id: str,
        result: str,
        notes: str,
    ) -> dict:
        """
        Resume the graph after a human Gemba Check.

        Parameters
        ----------
        investigation_id : str
        result           : "OK" or "NOK"
        notes            : Operator's physical observations
        """
        config = {"configurable": {"thread_id": investigation_id}}
        resume_value = {"result": result.upper(), "notes": notes}
        state = await self.graph.ainvoke(
            Command(resume=resume_value), config=config
        )
        return self._format_result(state)

    async def get_investigation_tree(self, investigation_id: str) -> list[WhyNode]:
        """Return the current why_nodes tree for the given investigation."""
        config = {"configurable": {"thread_id": investigation_id}}
        snapshot = self.graph.get_state(config)
        return snapshot.values.get("why_nodes", [])

    async def generate_8d_report(self, investigation_id: str) -> str:
        """
        Generate an AIAG 8D report PDF for the given investigation.

        Uses the LLM to populate fields not directly in the investigation
        State (D2 IS/IS NOT, D3 containment, D6 plan, D7 prevention) and
        maps the why_nodes tree into D4 root causes and D5 corrective actions.

        Returns the path to the saved PDF file.
        """
        config = {"configurable": {"thread_id": investigation_id}}
        snapshot = self.graph.get_state(config)
        values = snapshot.values

        phenomenon = values.get("phenomenon", "Unknown phenomenon")
        domain_context = values.get("domain_context", "")
        why_nodes = values.get("why_nodes", [])

        os.makedirs("investigations", exist_ok=True)

        content = await populate_8d_content(
            investigation_id=investigation_id,
            phenomenon=phenomenon,
            domain_context=domain_context,
            why_nodes=why_nodes,
            domain=self._domain,
        )

        pdf_path = f"investigations/{investigation_id}_8D.pdf"
        generate_pdf(content, pdf_path)
        return pdf_path

    # ------------------------------------------------------------------
    # Node implementations
    # ------------------------------------------------------------------

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
        """
        LLM + tools node: researches and proposes hypotheses for the current
        phenomenon / branch.  Uses structured output after the tool loop settles.
        """
        depth = state.get("current_depth", 1)
        branch_path = state.get("current_branch_path", "1")
        phenomenon = state["phenomenon"]
        domain_context = state.get("domain_context", "")

        # Build the phenomenon description for this depth level
        if depth == 1:
            current_problem = phenomenon
        else:
            # Find the parent WhyNode whose branch_path is the prefix of this one
            parent_path = ".".join(branch_path.split(".")[:-1])
            parent_nodes = [
                n for n in state.get("why_nodes", [])
                if n["branch_path"] == parent_path and n["gemba_result"] == "NOK"
            ]
            current_problem = (
                parent_nodes[-1]["hypothesis"] if parent_nodes else phenomenon
            )

        # Build full investigation history so the LLM is aware of what has
        # already been confirmed (NOK) and ruled out (OK) at all prior levels.
        tree_nodes = state.get("why_nodes", [])
        if tree_nodes:
            tree_summary_lines = []
            for n in tree_nodes:
                status = "OK (ruled out)" if n["gemba_result"] == "OK" else "NOK (confirmed)"
                line = f"  [{n['branch_path']}] depth={n['depth']} | {status} | {n['hypothesis']}"
                if n.get("gemba_notes"):
                    line += f"\n    Operator notes: {n['gemba_notes']}"
                if n.get("countermeasure"):
                    line += f"\n    Countermeasure: {n['countermeasure']}"
                tree_summary_lines.append(line)
            tree_summary = "\n".join(tree_summary_lines)
        else:
            tree_summary = "(none yet — this is the first level)"

        system_prompt = (
            f"You are an expert root cause analyst specialising in {self._domain}.\n"
            f"Today is {datetime.now().strftime('%Y-%m-%d %H:%M')}.\n"
            f"Equipment / process context: {self._equipment_context or 'not specified'}.\n\n"
            "Your task: use search and Wikipedia tools to research known failure modes, "
            "then propose 1–4 specific, testable hypotheses for WHY the given problem occurs.\n"
            "Be concrete — each hypothesis must describe a physical or process mechanism "
            "that an operator can verify with a Gemba Check.\n"
            "IMPORTANT: Do NOT re-propose any cause that already appears in the investigation "
            "history below, regardless of whether it was ruled out or confirmed.\n"
            "After your research, respond with the structured output schema."
        )
        user_prompt = (
            f"Original phenomenon: '{phenomenon}'\n\n"
            f"Investigation history so far:\n{tree_summary}\n\n"
            f"Problem to drill into now (depth {depth}, branch {branch_path}):\n"
            f"'{current_problem}'\n\n"
            f"Domain context: {domain_context}\n\n"
            "Using the history above as context, propose new hypotheses that have NOT yet "
            "been investigated. Use search_failure_modes and wikipedia tools as needed, "
            "then provide your structured hypothesis output."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        # Allow the LLM to call tools (may loop via why_tools node)
        response = await self.why_llm.ainvoke(messages)

        # If the LLM is calling tools, return immediately — the tool loop will
        # cycle back here.  Otherwise, parse structured output.
        if response.tool_calls:
            return {"messages": [response]} if hasattr(state, "messages") else {}

        # Parse the free-text response into structured form using a second call
        structured_llm = ChatOpenAI(
            model="gpt-4o-mini", temperature=0
        ).with_structured_output(WhyHypothesisOutput)
        parsed: WhyHypothesisOutput = await structured_llm.ainvoke(
            [
                SystemMessage(content="Extract the hypotheses and gemba instructions from the following analysis."),
                HumanMessage(content=response.content),
            ]
        )

        # Build pending_hypotheses queue
        pending = []
        for idx, cause in enumerate(parsed.causes, start=1):
            child_path = f"{branch_path}.{idx}" if depth > 1 else str(idx)
            pending.append({
                "hypothesis": cause,
                "branch_path": child_path,
                "depth": depth,
                "gemba_instructions": parsed.gemba_instructions,
                "domain_context": parsed.domain_context,
            })

        return {
            "pending_hypotheses": pending,
            "current_depth": depth,
            "current_branch_path": branch_path,
        }

    def why_router(self, state: OverallState) -> str:
        """Route: if why_generator returned tool_calls, go to tools; else dispatch."""
        # Check last message if it exists (tool-loop path)
        messages = state.get("messages", [])
        if messages and hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
            return "tools"
        return "dispatch"

    def gemba_dispatcher(self, state: OverallState) -> dict:
        """
        Pure Python: pop the next hypothesis from pending_hypotheses and set it
        as active_hypothesis.
        """
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
        """
        Human-in-the-loop node: interrupt() pauses the graph and surfaces the
        hypothesis + instructions to the operator.  Resumes when submit_gemba_result
        calls Command(resume={"result": "OK"/"NOK", "notes": "..."}).
        """
        active = state.get("active_hypothesis", {})
        hypothesis = active.get("hypothesis", "No hypothesis set")
        instructions = active.get("gemba_instructions", "Check the equipment directly.")

        # interrupt() halts the graph and returns control to the caller
        response = interrupt({
            "hypothesis": hypothesis,
            "gemba_instructions": instructions,
            "branch_path": active.get("branch_path", ""),
            "depth": active.get("depth", 1),
        })

        # response is the dict passed to Command(resume=...) by submit_gemba_result
        result = response.get("result", "NOK").upper()
        notes = response.get("notes", "")

        # Record the WhyNode with the gemba result
        active_hypothesis = state.get("active_hypothesis", {})
        node = make_why_node(
            branch_path=active_hypothesis.get("branch_path", "1"),
            depth=active_hypothesis.get("depth", 1),
            hypothesis=active_hypothesis.get("hypothesis", ""),
        )
        node["gemba_result"] = result
        node["gemba_notes"] = notes

        return {
            "why_nodes": [node],
            "active_hypothesis": {**active_hypothesis, "gemba_result": result, "gemba_notes": notes},
        }

    def gemba_router(self, state: OverallState) -> str:
        """Route based on the gemba result in the active_hypothesis."""
        active = state.get("active_hypothesis", {})
        return "OK" if active.get("gemba_result", "NOK") == "OK" else "NOK"

    def branch_closer(self, state: OverallState) -> dict:
        """Pure Python: mark the current branch as closed (gemba OK — not a cause)."""
        return {}

    def root_cause_validator(self, state: OverallState) -> dict:
        """
        Evaluator LLM: assesses whether the confirmed NOK cause is a genuine
        root cause or an intermediate symptom requiring deeper investigation.
        """
        active = state.get("active_hypothesis", {})
        phenomenon = state["phenomenon"]
        depth = active.get("depth", 1)
        max_depth = state.get("max_depth", 5)

        # Build investigation history for context
        tree_summary = "\n".join(
            f"  [{n['branch_path']}] depth={n['depth']} | {n['gemba_result']} | {n['hypothesis']}"
            for n in state.get("why_nodes", [])
        )

        system_prompt = (
            f"You are a senior root cause analyst for {self._domain}.\n"
            "Evaluate whether the confirmed cause is a TRUE ROOT CAUSE or an intermediate symptom.\n"
            "A root cause is one where fixing it would prevent the original phenomenon from recurring.\n"
            "An intermediate symptom is one that itself has a deeper mechanical / process cause.\n\n"
            "CRITICAL RULE: Human error, operator mistake, or any cause that blames a person's "
            "behaviour is NEVER a root cause. Human behaviour is always a symptom of a deeper "
            "systemic, process, or design failure (e.g. missing procedure, inadequate training, "
            "poor equipment design, absent error-proofing). If the confirmed cause describes "
            "human action or inaction, set is_root_cause=False and direct the probe toward the "
            "underlying system or process that enabled or failed to prevent that behaviour.\n"
        )
        user_prompt = (
            f"Original phenomenon: '{phenomenon}'\n\n"
            f"Current depth: {depth} of {max_depth}\n\n"
            f"Confirmed cause (Gemba NOK):\n  '{active.get('hypothesis', '')}'\n"
            f"Operator notes: '{active.get('gemba_notes', '')}'\n\n"
            f"Investigation tree so far:\n{tree_summary or '  (none yet)'}\n\n"
            "Is this a root cause or an intermediate symptom? Provide your structured decision."
        )

        decision: RootCauseDecision = self.validator_llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )

        # Update the most recent WhyNode with the validator's decision
        nodes = list(state.get("why_nodes", []))
        branch_path = active.get("branch_path", "")
        for i in range(len(nodes) - 1, -1, -1):
            if nodes[i]["branch_path"] == branch_path:
                nodes[i] = {**nodes[i], "is_root_cause": decision.is_root_cause}
                break

        updated_active = {
            **active,
            "is_root_cause": decision.is_root_cause,
            "validator_reasoning": decision.reasoning,
            "probe_direction": decision.probe_direction,
            "validator_confidence": decision.confidence,
        }

        return {
            "active_hypothesis": updated_active,
        }

    def validate_router(self, state: OverallState) -> str:
        """Route based on validator decision and remaining depth."""
        active = state.get("active_hypothesis", {})
        depth = active.get("depth", 1)
        max_depth = state.get("max_depth", 5)
        remaining = state.get("remaining_steps", 999)

        is_root = active.get("is_root_cause", False)

        if is_root or depth >= max_depth or remaining <= 5:
            return "countermeasure"
        return "deeper"

    def countermeasure_generator(self, state: OverallState) -> dict:
        """
        LLM with structured output: proposes a countermeasure for the confirmed
        root cause.
        """
        active = state.get("active_hypothesis", {})
        phenomenon = state["phenomenon"]

        system_prompt = (
            f"You are an operational excellence expert in {self._domain}.\n"
            "Propose a specific, actionable countermeasure to eliminate the confirmed root cause "
            "and prevent recurrence of the original phenomenon."
        )
        user_prompt = (
            f"Original phenomenon: '{phenomenon}'\n"
            f"Confirmed root cause: '{active.get('hypothesis', '')}'\n"
            f"Operator notes: '{active.get('gemba_notes', '')}'\n"
            f"Validator reasoning: '{active.get('validator_reasoning', '')}'\n\n"
            "Provide your structured countermeasure."
        )

        countermeasure: CountermeasureOutput = self.countermeasure_llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )

        # Update the matching WhyNode with the countermeasure
        branch_path = active.get("branch_path", "")
        nodes = list(state.get("why_nodes", []))
        for i in range(len(nodes) - 1, -1, -1):
            if nodes[i]["branch_path"] == branch_path:
                nodes[i] = {**nodes[i], "countermeasure": countermeasure.action}
                break

        updated_active = {
            **active,
            "countermeasure": countermeasure.action,
            "prevention_type": countermeasure.prevention_type,
            "suggested_owner": countermeasure.suggested_owner,
            "deadline_days": countermeasure.deadline_days,
        }

        return {"active_hypothesis": updated_active}

    def check_complete_node(self, state: OverallState) -> dict:
        """Pure Python: no-op node — routing is handled by check_complete_router."""
        return {}

    def check_complete_router(self, state: OverallState) -> str:
        """Route: more hypotheses pending → dispatch, else → report."""
        pending = state.get("pending_hypotheses", [])
        return "dispatch" if pending else "report"

    async def report_generator(self, state: OverallState) -> dict:
        """
        Final node: builds a structured markdown investigation report and saves
        it to investigations/<investigation_id>.md via direct file write.
        """
        investigation_id = state.get("investigation_id", "unknown")
        phenomenon = state["phenomenon"]
        domain_context = state.get("domain_context", "")
        nodes = state.get("why_nodes", [])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Build tree section
        tree_lines = []
        for node in nodes:
            indent = "  " * (node["depth"] - 1)
            status = "OK" if node["gemba_result"] == "OK" else "NOK"
            tree_lines.append(
                f"{indent}- [{node['branch_path']}] **{status}** {node['hypothesis']}"
            )
            if node["gemba_notes"]:
                tree_lines.append(f"{indent}  *Gemba notes:* {node['gemba_notes']}")
            if node["countermeasure"]:
                tree_lines.append(f"{indent}  *Countermeasure:* {node['countermeasure']}")

        # Identify root causes + countermeasures
        root_causes = [n for n in nodes if n.get("is_root_cause") or n.get("countermeasure")]

        countermeasure_lines = []
        for rc in root_causes:
            if rc.get("countermeasure"):
                countermeasure_lines.append(
                    f"- **Root cause [{rc['branch_path']}]:** {rc['hypothesis']}\n"
                    f"  **Countermeasure:** {rc['countermeasure']}"
                )

        report = (
            f"# 5 Whys Investigation Report\n\n"
            f"**Investigation ID:** {investigation_id}  \n"
            f"**Date:** {timestamp}  \n"
            f"**Domain:** {domain_context}  \n\n"
            f"---\n\n"
            f"## Phenomenon\n\n"
            f"> {phenomenon}\n\n"
            f"---\n\n"
            f"## Why Tree\n\n"
            + "\n".join(tree_lines)
            + "\n\n---\n\n"
            f"## Root Causes & Countermeasures\n\n"
            + ("\n\n".join(countermeasure_lines) if countermeasure_lines else "_No root causes confirmed._")
            + "\n\n---\n\n"
            f"*Generated by 5 Whys Agent — {timestamp}*\n"
        )

        os.makedirs("investigations", exist_ok=True)
        report_path = f"investigations/{investigation_id}.md"
        with open(report_path, "w") as f:
            f.write(report)

        return {"report_path": report_path}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _format_result(self, state: dict) -> dict:
        """
        Normalise the graph's output state into a consistent dict for the UI.
        """
        active = state.get("active_hypothesis") or {}
        nodes = state.get("why_nodes", [])

        # Detect whether the graph is interrupted at gemba_check
        snapshot = None
        try:
            config = {"configurable": {"thread_id": state.get("investigation_id", "")}}
            snapshot = self.graph.get_state(config)
        except Exception:
            pass

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
            "why_nodes": nodes,
            "report_path": state.get("report_path", ""),
            "pending_count": len(state.get("pending_hypotheses", [])),
        }
