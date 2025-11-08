from datetime import datetime
from agents import Agent, Tool
from config import client, MODEL, RESEARCH_MAX_TOKENS

async def research_step(query: str):
    if not query or not isinstance(query, str):
        return "Invalid input: expected a text query."

    prompt = f"""
You are the Research Agent in a financial/banking context. Your role is to gather concise, factual background information for downstream analysis.

Task: - Summarize recent, relevant findings or best practices about: "{query}" - Include 2–3 bullet points under each of these sections:
  1. Background / Context
  2. Key Insights or Findings
  3. Implications for further financial and risk analysis.
Return not more than 250 words.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a professional research analyst."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=RESEARCH_MAX_TOKENS,
            temperature=0.2,
        )
        text = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[research_agent] API error: {e}")
        text = (
            "Unable to retrieve research insights due to API error. "
            "Please retry or verify network configuration."
        )

    return text

async def get_research_tool(mcp_servers) -> Tool:
    """
    Returns an MCP-lite tool for research.
    """
    agent = Agent(
        name="ResearchAgent",
        instructions=f"Performs concise background research. Datetime: {datetime.now()}",
        model=MODEL,
        mcp_servers=mcp_servers,
    )
    return agent.as_tool(
        tool_name="ResearchAgent",
        tool_description="Performs concise structured background research on the given query.",
        func=research_step,
    )
