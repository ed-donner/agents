"""
Week 4 Day 3 - lab 3 exercise, as a standalone script.

1. A browser agent with memory (checkpointer + thread_id).
2. Middleware that blocks navigation to sites on a block list.

Needs Node (npx), Chrome and OPENAI_API_KEY in .env.
Run with:  python lab3_exercise.py
"""

# --- Step 1: imports and environment ---------------------------------------
import asyncio
from urllib.parse import urlparse

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain_core.messages import ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import MemorySaver

load_dotenv(override=True)

MODEL = "openai:gpt-5.4-mini"
SYSTEM_PROMPT = "You are a web research assistant. Use the browser tools to complete the task, then report clearly."

# --- Step 2: block list configuration --------------------------------------
BLOCKED_SITES = ["reddit.com"]


def is_blocked(url: str) -> bool:
    """True if the URL's host is a blocked domain or one of its subdomains."""
    host = (urlparse(url).hostname or "").lower()
    return any(host == site or host.endswith("." + site) for site in BLOCKED_SITES)


# --- Step 3: the block list middleware -------------------------------------
# Wraps every tool call. It is async because the browser tools only speak async.
@wrap_tool_call
async def block_sites(request, handler):
    call = request.tool_call
    # Only browser_navigate takes a URL we need to check
    if call["name"] == "browser_navigate" and is_blocked(call["args"].get("url", "")):
        print(f"  [middleware] BLOCKED navigation to {call['args']['url']}")
        # Skip handler(request): the real tool never runs. Reply with a ToolMessage
        # so the agent sees the refusal and can explain it to the user.
        return ToolMessage(
            content=f"Navigation refused: {call['args']['url']} is on the block list. Do not try to reach it another way.",
            tool_call_id=call["id"],
        )
    # Anything else proceeds as normal
    return await handler(request)


async def ask(agent, text, config=None):
    """Send one user message and print the agent's final answer."""
    result = await agent.ainvoke({"messages": [{"role": "user", "content": text}]}, config=config)
    print(result["messages"][-1].content)


async def main():
    # --- Step 4: load the Playwright MCP browser tools ---------------------
    client = MultiServerMCPClient({
        "playwright": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest", "--isolated"],
        }
    })
    browser_tools = await client.get_tools()
    print(f"Loaded {len(browser_tools)} browser tools")

    # --- Step 5: browser agent with memory ---------------------------------
    # The checkpointer stores the conversation; thread_id says which one.
    memory_agent = create_agent(
        model=MODEL,
        tools=browser_tools,
        checkpointer=MemorySaver(),
        system_prompt=SYSTEM_PROMPT,
    )
    mem_config = {"configurable": {"thread_id": "browsing"}}

    print("\n--- Step 6: first question (open a site) ---")
    await ask(memory_agent, "Go to https://news.ycombinator.com and tell me the titles of the top three stories.", mem_config)

    print("\n--- Step 7: follow-up that relies on memory, no browsing ---")
    await ask(memory_agent, "What was the title of the second story you just told me about? Answer from memory, don't browse again.", mem_config)

    # --- Step 8: browser agent guarded by the block list middleware --------
    guarded_agent = create_agent(
        model=MODEL,
        tools=browser_tools,
        middleware=[block_sites],
        system_prompt=SYSTEM_PROMPT,
    )

    print("\n--- Step 9: blocked site (expect a refusal) ---")
    await ask(guarded_agent, "Go to https://www.reddit.com and tell me the top post.")

    print("\n--- Step 10: allowed site (expect it to work) ---")
    await ask(guarded_agent, "Go to https://news.ycombinator.com and tell me the title of the top story.")


if __name__ == "__main__":
    asyncio.run(main())
