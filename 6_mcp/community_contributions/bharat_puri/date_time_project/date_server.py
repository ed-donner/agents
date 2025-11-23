from datetime import date, datetime
from mcp.server.fastmcp import FastMCP
import os
import asyncio
from openai import OpenAI
from dotenv import load_dotenv

mcp = FastMCP("date_server")

# Load environment variables (allows using a .env file)
load_dotenv(override=True)

# Create OpenAI client only if API key is present. This avoids hard failures
# when running the server in environments without LLM configured.
_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
_DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI(api_key=_OPENAI_API_KEY) if _OPENAI_API_KEY else None


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
    """Return an AI-generated response using an OpenAI LLM.

    Behavior:
    - If no API key is configured, returns a friendly message.
    - Calls the OpenAI client in a thread to avoid blocking the event loop
      if the client is synchronous.
    - Catches exceptions and returns a readable error message.
    """
    if not client:
        return "LLM not configured. Please set OPENAI_API_KEY in the environment."

    model = os.getenv("OPENAI_MODEL", _DEFAULT_MODEL)

    try:
        def _call():
            # Use the standard chat/completions create call on the OpenAI client.
            return client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )

        response = await asyncio.to_thread(_call)

        # Extract content robustly depending on response shape
        content = None
        if hasattr(response, "choices") and response.choices:
            choice = response.choices[0]
            # Try common shapes: choice.message.content or dicts
            message = getattr(choice, "message", None)
            if message is None and isinstance(choice, dict):
                message = choice.get("message")
            if message is not None:
                # message may be an object or a dict
                if hasattr(message, "content"):
                    content = message.content
                elif isinstance(message, dict):
                    content = message.get("content")

        return content or str(response)

    except Exception as exc:  # pragma: no cover - runtime error path
        # Return an informative string; MCP clients can surface this to users.
        return f"LLM error: {exc}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
