# evaluates financial impacts, cost implications, and opportunities
from datetime import datetime
from agents import Agent, Tool
from config import client, MODEL, FINANCE_MAX_TOKENS

async def finance_step(query: str, research_summary: str = "", risk_summary: str = ""):
    if not query:
        return "Missing query input."

    prompt = f"""
You are the Financial Analysis Agent. Analyze the following information to generate a concise, structured financial insight report.
Query: {query}
Research Summary:{research_summary}
Risk Summary: {risk_summary}

Instructions: - Provide 2–3 key *financial implications* or *cost considerations*, - Identify any *potential financial opportunities*, - Mention relevant *industry or market trends* if applicable,
- Keep language neutral, concise, and evidence-based, - Limit output to ~250 words.
Output format:1. Overview2. Financial Implications3. Opportunities or Trends"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an expert in finance and cost analysis."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=FINANCE_MAX_TOKENS,
            temperature=0.25,
        )
        text = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[finance_agent] API error: {e}")
        text = (
            "API erroe. "
        )

    return text


async def get_finance_tool(mcp_servers) -> Tool:
    agent = Agent(
        name="FinanceAgent",
        instructions=f"Performs financial analysis for the given topic. Datetime: {datetime.now()}",
        model=MODEL,
        mcp_servers=mcp_servers,
    )
    return agent.as_tool(
        tool_name="FinanceAgent",
        tool_description="Evaluates financial impacts, costs, and opportunities for the topic.",
        func=finance_step,
    )
