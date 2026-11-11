"""
Week 4 Day 4 - lab 4 exercise, as a standalone script.

1. A deep research agent with a second tool (the Playwright MCP browser tools).
2. Read every file the agent wrote to the sandbox.
3. Stretch: a skill of my own (midnight blue house style) for a slide-maker sub-agent.

Needs Node (npx), Chrome, OPENAI_API_KEY and SERPER_API_KEY in .env, plus
midnight_slide_kit.py and sandbox/skills_midnight/ next to this file.
Run with:  python lab4_exercise.py
"""

# --- Step 1: imports and environment ---------------------------------------
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

from midnight_slide_kit import build_midnight_slide

load_dotenv(override=True)

# --- Step 2: shared setup: sandbox folder, model, search tool --------------
# The agent sees this folder as its filesystem root "/"
SANDBOX = str(Path(__file__).parent / "sandbox")
os.makedirs(SANDBOX, exist_ok=True)

model = ChatOpenAI(model="gpt-5.4-mini")
search = GoogleSerperRun(api_wrapper=GoogleSerperAPIWrapper())


def backend():
    return FilesystemBackend(root_dir=SANDBOX, virtual_mode=True)


def tools_called(result):
    """Names of every tool the agent called, in order."""
    return [tc["name"] for m in result["messages"] for tc in (getattr(m, "tool_calls", []) or [])]


# --- Step 3: the midnight slide tool and sub-agent -------------------------
@tool
def create_midnight_slide(title: str, key_points: list[str], recommendation: str) -> str:
    """Create a one-slide PowerPoint in the midnight blue style, saved as midnight_fleet.pptx."""
    build_midnight_slide(title, key_points, recommendation, os.path.join(SANDBOX, "midnight_fleet.pptx"))
    return "Saved the slide to /midnight_fleet.pptx"


midnight_slide_maker = {
    "name": "midnight-slide-maker",
    "description": "Turns a finished recommendation into a one-slide PowerPoint deck in the midnight blue style.",
    "system_prompt": "You turn research recommendations into slides, following your midnight-slide skill.",
    "tools": [create_midnight_slide],
    # Only my own skill folder, so Voltway's skill is not loaded
    "skills": ["/skills_midnight/"],
}


def print_sandbox_files():
    """Print every text file in the sandbox; only list the binary ones."""
    text_suffixes = {".md", ".txt", ".json", ".py"}
    for path in sorted(Path(SANDBOX).rglob("*")):
        if not path.is_file():
            continue
        print("=" * 70)
        print(f"{path.relative_to(SANDBOX)}  ({path.stat().st_size} bytes)")
        print("=" * 70)
        print(path.read_text() if path.suffix in text_suffixes else "[binary file, not printed]")
        print()


async def main():
    # --- Step 4: load the Playwright MCP browser tools (async) -------------
    client = MultiServerMCPClient({
        "playwright": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest", "--isolated"],
        }
    })
    browser_tools = await client.get_tools()
    print(f"Loaded {len(browser_tools)} browser tools")

    # --- Step 5: research agent with search plus browser tools -------------
    researcher_browser = create_deep_agent(
        model=model,
        tools=[search, *browser_tools],
        system_prompt=(
            "You are a research analyst. Plan your work with your todo tool. "
            "Use the search tool to find sources, then use the browser tools to open the most relevant page "
            "and read the real figures from it. Write your findings as a tidy markdown briefing to a file."
        ),
        backend=backend(),
    )

    print("\n--- Step 6: run the researcher (ainvoke, because the browser tools are async) ---")
    brief = """
    Our company is planning to move its sales fleet to electric vehicles.
    Find out roughly how many public EV charging ports there are in the US.
    Search for a reliable source, then open that page in the browser and quote the figure from it.
    Write a short markdown briefing with a heading, the figure, and the source URL to the file charging_browser.md.
    """
    result = await researcher_browser.ainvoke({"messages": [{"role": "user", "content": brief}]})
    print(result["messages"][-1].content)
    print("Tools the agent called, in order:", tools_called(result))

    print("\n--- Step 7: read every file the agent wrote to the sandbox ---")
    print_sandbox_files()

    # --- Step 8: presenter that delegates to the slide-maker sub-agent -----
    midnight_presenter = create_deep_agent(
        model=model,
        subagents=[midnight_slide_maker],
        system_prompt="You prepare research for presentation by delegating to your midnight-slide-maker sub-agent.",
        backend=backend(),
    )

    print("\n--- Step 9: make a one-slide deck in my own house style ---")
    result = await midnight_presenter.ainvoke({"messages": [{"role": "user", "content":
        "Read fleet.md and have a one-slide deck made of its recommendation."}]})
    print(result["messages"][-1].content)
    print("Open sandbox/midnight_fleet.pptx and compare it with sandbox/fleet.pptx")


if __name__ == "__main__":
    asyncio.run(main())
