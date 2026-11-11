"""
Week 4 Day 5 - lab 5 exercise, as a standalone script.

1. The Expedia errand: the Sidekick pauses so I can log in myself, then searches flights.
2. A harmless write task, to see the approval gate on the filesystem write tools.
3. My own tools (days_until and split_cost), first called directly, then through the Sidekick.
4. A real task: a LinkedIn content calendar, written to sandbox/linkedin_calendar.md.

Needs Node (npx), Chrome, OPENAI_API_KEY and SERPER_API_KEY in .env (plus the Pushover
keys for the push notification), and sidekick.py and sidekick_tools.py next to this file.
Run with:  python lab5_exercise.py
"""

# --- Step 1: imports and environment ---------------------------------------
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from sidekick import Sidekick
from sidekick_tools import days_until, split_cost

load_dotenv(override=True)

# The Sidekick reads and writes files in "sandbox/", relative to the working directory,
# so run from this file's folder wherever the script is launched from
os.chdir(Path(__file__).parent)


# --- Step 2: shared helpers ------------------------------------------------
def show_last(history, count=2):
    """Print the last few messages of the conversation."""
    for entry in history[-count:]:
        print(f"[{entry['role']}] {entry['content']}\n")


async def approve_each_pause(sidekick, history):
    """Approve each pause one at a time, reading what the Sidekick wants to do first.
    Anything other than 'y' stops here and leaves the Sidekick paused."""
    while sidekick.paused:
        print(history[-1]["content"])
        if input("Approve? (y/n) ").strip().lower() != "y":
            break
        history = await sidekick.resume(history)
    return history


async def fresh_sidekick(previous=None):
    """Close the previous Sidekick (and its browser), then build a new one with its own plan and session."""
    if previous is not None:
        previous.cleanup()
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick


async def main():
    # --- Part 1: the Expedia errand ----------------------------------------
    print("\n=== Part 1: the Expedia errand ===")
    sidekick = await fresh_sidekick()

    # The login is deliberately left to me: the task tells the agent to ask for help rather than type credentials
    expedia_task = """Go to expedia.com and sign in to my account. When you reach the login page, use request_human_help
so I can log in myself in your browser window. Once I have, find the best round-trip flight from Lima to London,
leaving about a month from now and returning a week later. I care about price first, then total journey time,
and I would rather avoid itineraries with two or more stops. Write the top three options to expedia_flights.md."""

    # The criteria demand evidence from Expedia itself, so a Google Flights fallback cannot satisfy the evaluator
    expedia_criteria = "expedia_flights.md is written with three specific options from Expedia including airline, times and price, plus a clear recommendation."

    history = await sidekick.run_turn(expedia_task, expedia_criteria, history=[])
    print(history[-1]["content"])

    # The run is now paused on request_human_help: log in in the Sidekick's browser window.
    # Approving means "I have logged in, carry on"
    if sidekick.paused:
        input("Log in to Expedia in the Sidekick's browser window, then press Enter to resume...")
        history = await sidekick.resume(history)
    show_last(history)

    # --- Part 2: the approval gate on the filesystem write tools -----------
    print("\n=== Part 2: gating the filesystem write tools ===")
    sidekick = await fresh_sidekick(sidekick)

    # A harmless write task: it should pause BEFORE the file is created
    history = await sidekick.run_turn(
        message="Write a file called approval_test.md containing one sentence about why human approval matters for AI agents.",
        success_criteria="approval_test.md exists in the sandbox and contains one sentence.",
        history=[],
    )
    print(history[-1]["content"])
    print("Paused:", sidekick.paused)

    # The pause message shows the exact write_file call: check the file is not there yet, then approve
    print("Exists before approval:", os.path.exists("sandbox/approval_test.md"))
    if sidekick.paused:
        history = await sidekick.resume(history)
    print("Exists after approval:", os.path.exists("sandbox/approval_test.md"))
    show_last(history)

    # --- Part 3: tools of my own -------------------------------------------
    print("\n=== Part 3: days_until and split_cost ===")
    # First call them directly, with no model involved, to prove they work.
    # @tool objects are called with .invoke and a dict of arguments
    print(days_until.invoke({"date": "2026-12-25"}))
    print(split_cost.invoke({"total": 183.40, "people": 4, "tip_percent": 15}))

    # Then let the Sidekick decide when to use them
    sidekick = await fresh_sidekick(sidekick)
    print([tool.name for tool in sidekick.tools if tool.name in ("days_until", "split_cost")])

    history = await sidekick.run_turn(
        message="How many days until Christmas Day 2026, and if a dinner costs 183.40 split between 4 people with a 15% tip, what does each person pay?",
        success_criteria="The reply gives the number of days and the per-person amount, and the days_until and split_cost tools were both called.",
        history=[],
    )
    show_last(history)

    # --- Part 4: a real task, a LinkedIn content calendar ------------------
    print("\n=== Part 4: the LinkedIn content calendar ===")
    sidekick = await fresh_sidekick(sidekick)

    # Each topic comes with the real thing I did, so the model does not invent experiences
    linkedin_task = """Create a LinkedIn content calendar for the next 5 weekdays, starting tomorrow, about what I learned this week
in an AI engineering course on building agents. One topic per day, in this order, each with the real thing I did that I want
the post to mention (do not invent other experiences):
1. The building blocks of an agent: LLM, tools, memory. I started with a simple agent with search, Wikipedia and a push notification tool.
2. LangGraph: orchestration with state, nodes and edges. I drew the graph of my agent as a diagram and read its nodes and edges.
3. create_agent and middleware: planning, guardrails, human approval. I made my agent pause for my approval before it could write a file.
4. MCP servers: a real browser and a filesystem. I asked my agent to search flights on Expedia; it paused so I could log in myself,
   and I noticed it searched from Lima instead of New York because the site prefilled the origin.
5. The Sidekick: a worker with an evaluator loop. I used it to plan this very calendar, and my first run reused sources and sounded generic.
For each day, search the web for one article, announcement or tutorial published in 2025 or 2026 (not a documentation home page)
that matches the topic. Every source URL must be different. Open each URL in the browser to confirm it loads before you use it.
Use days_until to get the exact date of each post.
Write the calendar to linkedin_calendar.md. Each entry needs the date and weekday, the topic, a hook line, a full draft post of
at most 1,000 characters in the first person that mentions the thing I did and ends with a practical takeaway, three hashtags,
and the source link. Finish by sending me a push notification saying the calendar is ready."""

    # Concrete criteria, so the evaluator can check them against the tool calls
    linkedin_criteria = """linkedin_calendar.md is written with exactly 5 entries on consecutive weekdays starting tomorrow,
each with a date and weekday, a topic from the list, a hook, a draft of at most 1,000 characters that mentions the specific thing
the user did for that day, three hashtags and a source URL. All 5 source URLs are different and each was opened with browser_navigate.
The days_until tool was called, and a push notification was sent."""

    history = await sidekick.run_turn(linkedin_task, linkedin_criteria, history=[])
    print(history[-1]["content"])

    # The Sidekick pauses at every gated action (the write_file, then the push notification)
    history = await approve_each_pause(sidekick, history)
    show_last(history)

    # --- Final step: the deliverable, and the plan the Sidekick followed ---
    print("\n=== The deliverable ===")
    print(Path("sandbox/linkedin_calendar.md").read_text())
    print()
    for todo in sidekick.todos:
        print(f"[{todo['status']}] {todo['content']}")

    sidekick.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
