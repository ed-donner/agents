from datetime import datetime
import gradio as gr
from agents import Agent, Tool  # MCP-lite base classes
from clarifier_agent import clarifier_step  # your core clarifier function
from process_request import run_pipeline_sync  # triggers full pipeline
from config import MODEL



def start_clarification_logic(user_input: str):
    state = {
        "round": 1,
        "history": [],
        "final_query": None,
    }
    clarifier_msg, state = clarifier_step(user_message=user_input, state=state)
    return clarifier_msg, state


def continue_clarification_logic(user_answer: str, state: dict):
    state["history"].append({"user": user_answer})
    clarifier_msg, state = clarifier_step(user_message=user_answer, state=state)
    if state.get("final_query"):
        pdf_path, results = run_pipeline_sync(state["final_query"])

        summary = f"""
**Final Clarified Query:** {results['query']}
**Research:** {results['research'][:350]}...
**Risk:** {results['risk'][:350]}...
**Finance:** {results['finance'][:350]}...
**Download PDF:** [{pdf_path}]({pdf_path})
"""
        return summary, pdf_path, state, gr.update(visible=False), gr.update(visible=True)

    # Otherwise, continue clarification
    return clarifier_msg, None, state, gr.update(visible=True), gr.update(visible=False)



async def get_start_clarification_tool(mcp_servers=None) -> Tool:
    agent = Agent(
        name="StartClarification",
        instructions=f"Starts a clarification session to refine user queries. Datetime: {datetime.now()}",
        model=MODEL,
        mcp_servers=mcp_servers,
    )
    return agent.as_tool(
        tool_name="StartClarification",
        tool_description="Starts the clarification process and generates the first clarifier question.",
        func=start_clarification_logic,
    )


async def get_continue_clarification_tool(mcp_servers=None) -> Tool:
    agent = Agent(
        name="ContinueClarification",
        instructions=f"Continues an active clarification conversation with user responses. Datetime: {datetime.now()}",
        model=MODEL,
        mcp_servers=mcp_servers,
    )
    return agent.as_tool(
        tool_name="ContinueClarification",
        tool_description="Continues a clarification session and outputs the next clarifier question or final report.",
        func=continue_clarification_logic,
    )
