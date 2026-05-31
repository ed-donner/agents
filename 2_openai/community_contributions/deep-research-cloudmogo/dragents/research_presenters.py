from agents.stream_events import AgentUpdatedStreamEvent, RunItemStreamEvent

from models.models import Clarification, ResearchState, SearchEvidence, WebSearchPlan


def format_clarification(clarification: Clarification) -> str:
    """Format question and answer pairs for downstream agents and UI."""
    lines = []

    for question, answer in zip(
        clarification.clarification_questions,
        clarification.clarification_answers,
    ):
        lines.append(f"Question: {question}")
        lines.append(f"Answer: {answer or '[No answer provided]'}")

    return "\n".join(lines)


def format_state_update(state: ResearchState) -> str:
    """Render the supervisor state as a user-facing progress update."""
    lines = ["Supervisor update:"]
    lines.append(f"Next action: {state.next_action or 'unknown'}")
    lines.append(f"Needs clarification: {state.needs_clarification}")
    lines.append(f"Ready to email: {state.ready_to_email}")

    if state.planned_searches:
        lines.append("Current planned searches:")
        for item in state.planned_searches:
            lines.append(f"- {item.query}")

    if state.delivery_status:
        lines.append(f"Delivery status: {state.delivery_status}")

    return "\n".join(lines)


def format_stream_event(event: object) -> str | None:
    """Convert useful supervisor streaming events into UI-friendly progress updates."""
    if isinstance(event, AgentUpdatedStreamEvent):
        return f"Active agent: {event.new_agent.name}"

    if isinstance(event, RunItemStreamEvent):
        if event.name == "tool_called":
            tool_name = getattr(getattr(event.item, "raw_item", None), "name", None)
            return f"Running tool: {tool_name or 'unknown tool'}"

        if event.name == "tool_output":
            return "Tool finished."

        if event.name == "handoff_requested":
            return "Supervisor requested a specialist handoff."

        if event.name == "handoff_occured":
            source = getattr(event.item, "source_agent", None)
            target = getattr(event.item, "target_agent", None)
            source_name = getattr(source, "name", "unknown")
            target_name = getattr(target, "name", "unknown")
            return f"Handoff: {source_name} -> {target_name}"

    return None


def format_search_plan(search_plan: WebSearchPlan) -> str:
    """Render a planned search list for the UI."""
    return "\n".join(
        f"- {item.query} ({item.reason})" for item in search_plan.searches
    )


def format_evidence(evidence: list[SearchEvidence]) -> str:
    """Render accumulated evidence for streaming UI updates."""
    lines = []

    for item in evidence:
        lines.append(f"Query: {item.query}")
        lines.append(f"Reason: {item.reason}")
        lines.append(f"Summary: {item.summary}")
        lines.append("")

    return "\n".join(lines).strip()


def render_research_state_messages(
    query: str,
    clarification: Clarification,
    state: ResearchState,
) -> list[str]:
    """Render the supervisor's final state into ordered UI messages."""
    messages = [format_state_update(state)]

    if state.next_action == "clarify" or state.needs_clarification:
        messages.append("Supervisor requested more clarification before continuing.")
        return messages

    if state.planned_searches:
        messages.append(
            f"Researching '{query}' with clarification:\n\n"
            f"{format_clarification(clarification)}\n\n"
            f"Planned searches:\n{format_search_plan(WebSearchPlan(searches=state.planned_searches))}\n"
        )

    if state.evidence:
        messages.append(f"Search results:\n{format_evidence(state.evidence)}\n")

    if state.report is not None:
        messages.append(f"Report:\n{state.report.markdown_report}\n")

    if state.delivery_status:
        messages.append(state.delivery_status)

    if state.next_action == "done" or state.delivery_status:
        messages.append("Research complete.")

    return messages


def merge_supervisor_state(
    previous: ResearchState,
    current: ResearchState,
) -> ResearchState:
    """Preserve important accumulated state fields across supervisor updates."""
    current.original_query = previous.original_query
    current.clarification = previous.clarification

    if not current.planned_searches:
        current.planned_searches = previous.planned_searches
    if not current.evidence:
        current.evidence = previous.evidence
    if current.report is None:
        current.report = previous.report
    if current.delivery_status is None:
        current.delivery_status = previous.delivery_status

    return current
