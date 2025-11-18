from datetime import date, datetime
from mcp.server.fastmcp import FastMCP
import os
from openai import OpenAI
from dotenv import load_dotenv

mcp = FastMCP("date_server")

# Initialize OpenAI client
# -------------------------------------------------------------
# 2. Load environment variables
# -------------------------------------------------------------
load_dotenv(override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@mcp.tool()
async def current_date() -> str:
    """Return today's date in ISO format (YYYY-MM-DD)."""
    return date.today().isoformat()


@mcp.tool()
async def current_time() -> str:
    """Return the current time in UTC (HH:MM:SS)."""
    return datetime.utcnow().strftime("%H:%M:%S")


@mcp.tool()
async def ask_llm(prompt: str) -> str:
    """Return an AI-generated response using OpenAI LLM."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # or 'gpt-4o' if allowed
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    mcp.run(transport="stdio")
