"""ARES CLI — run research from the terminal."""

import argparse
import asyncio
import sys

from dotenv import load_dotenv
from agents import Runner, InputGuardrailTripwireTriggered

from ares_agents import architect_agent, notification_agent

load_dotenv()

DEFAULT_EMAIL = "gasmyrmougang@gmail.com"


async def run_research(query: str, email: str | None = None) -> None:
    """Run the full ARES pipeline with live console output."""
    print(f"\n{'='*60}")
    print("ARES: Autonomous Research & Extraction System")
    print(f"{'='*60}\n")

    stream = Runner.run_streamed(architect_agent, input=query)

    async for event in stream.stream_events():
        if event.type == "agent_updated_stream_event":
            print(f"  >> Agent: {event.new_agent.name}")
        elif event.type == "run_item_stream_event":
            if event.name == "tool_called":
                print(f"     Tool: {event.item.raw_item.name}")
            elif event.name == "tool_output":
                print("     Done.")

    print(f"\n{'='*60}")
    print("RESEARCH REPORT")
    print(f"{'='*60}\n")
    print(stream.final_output)

    # HITL: ask user before sending email
    if email:
        send = (await asyncio.to_thread(input, f"\nSend report to {email}? [Y/n]: ")).strip().lower()
        if send in ("", "y", "yes"):
            print(f"\nSending to {email}...")
            notification_input = (
                f"Send the following report to {email}:\n\n{stream.final_output}"
            )
            await Runner.run(notification_agent, input=notification_input)
            print(f"Report sent to {email}")
        else:
            print("Email skipped.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ARES: Autonomous Research & Extraction System",
    )
    parser.add_argument(
        "--query", "-q",
        required=True,
        help="The research query to investigate.",
    )
    parser.add_argument(
        "--email", "-e",
        default=DEFAULT_EMAIL,
        help=f"Email to send the report to (default: {DEFAULT_EMAIL}). Use --no-email to skip.",
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Skip email delivery.",
    )
    args = parser.parse_args()

    email = None if args.no_email else args.email

    try:
        asyncio.run(run_research(args.query, email))
    except InputGuardrailTripwireTriggered:
        print("\nQuery blocked by safety guardrail. Please rephrase.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(0)


if __name__ == "__main__":
    main()
