from datetime import datetime
from agents import Agent, Tool
from config import client, MODEL, RISK_MAX_TOKENS

async def risk_step(query: str, research_summary: str = ""):
    if not query:
        return "Missing query input."

    prompt = f"""
You are the Risk Analysis Agent. Your role is to assess potential risks associated with the following research topic:
Query:{query}
Research Summary: {research_summary}

Instructions: - Identify key *strategic, financial, and operational risks* relevant to this topic.- Include risk categories and short explanations. - Suggest *1–2 realistic mitigation strategies* per major risk. - Suggest *1–2 realistic mitigation strategies* per major risk. - Avoid repetition or generic statements.- Keep output under 250 words.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a concise and analytical risk advisor."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=RISK_MAX_TOKENS,
            temperature=0.2,
        )
        text = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[risk_agent] API error: {e}")
        text = (
            "Unable to generate risk analysis due to an API error. "
            "Please check configuration or retry later."
        )

    return text


async def get_risk_tool(mcp_servers) -> Tool:
    agent = Agent(
        name="RiskAgent",
        instructions=f"Assesses financial and operational risks. Datetime: {datetime.now()}",
        model=MODEL,
        mcp_servers=mcp_servers,
    )
    return agent.as_tool(
        tool_name="RiskAgent",
        tool_description="Identifies and evaluates potential risks related to the topic.",
        func=risk_step,
    )
