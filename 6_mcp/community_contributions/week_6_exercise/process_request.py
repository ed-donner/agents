import asyncio
from mcp_sim import MCPHost, MCPClient
from clarifier_agent import get_clarifier_tool
from research_agent import get_research_tool
from risk_agent import get_risk_tool
from finance_agent import get_finance_tool
from pdf_generator import get_pdf_tool, build_pdf


async def process_user_request(user_input: str, clarifier_state=None):
    print(f"[process_request] Starting new pipeline for query: {user_input}")
    host = MCPHost("PipelineHost")
    client = MCPClient("LocalClient")
    host.connect_client(client)

    clarifier_tool = await get_clarifier_tool(mcp_servers=None)
    research_tool = await get_research_tool(mcp_servers=None)
    risk_tool = await get_risk_tool(mcp_servers=None)
    finance_tool = await get_finance_tool(mcp_servers=None)
    pdf_tool = await get_pdf_tool(mcp_servers=None)
    for tool in [clarifier_tool, research_tool, risk_tool, finance_tool, pdf_tool]:
        client.register_tool(tool)
    clarifier_reply, clarifier_state = await clarifier_tool(
        user_message=user_input,
        state=clarifier_state
    )
    print(f"[process_request] Clarifier reply:\n{clarifier_reply}")
    if not clarifier_state.get("final_query"):
        return None, {
            "status": "clarifying",
            "clarifier_reply": clarifier_reply,
            "clarifier_state": clarifier_state
        }
    final_query = clarifier_state["final_query"]
    print(f"[process_request] Final clarified query: {final_query}")

    research_summary = await research_tool(final_query)
    risk_summary = await risk_tool(final_query, research_summary)
    finance_summary = await finance_tool(final_query, research_summary, risk_summary)
    pdf_text = await pdf_tool(final_query, research_summary, risk_summary, finance_summary)
    pdf_path = build_pdf(pdf_text)

    print(f"[process_request] PDF generated at {pdf_path}")

    return pdf_path, {
        "status": "done",
        "query": final_query,
        "research": research_summary,
        "risk": risk_summary,
        "finance": finance_summary,
        "pdf_text": pdf_text,
    }


def run_pipeline_sync(user_input: str, clarifier_state=None):
    return asyncio.run(process_user_request(user_input, clarifier_state))
