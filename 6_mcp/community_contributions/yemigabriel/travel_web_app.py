from __future__ import annotations

from contextlib import AsyncExitStack
from datetime import datetime
import os
import shutil

import gradio as gr
from dotenv import load_dotenv

from agents import Agent, Runner, Tool, trace
from agents.mcp import MCPServerStdio

load_dotenv(override=True)

MAX_TURNS = 30


def build_env() -> dict[str, str]:
    env = os.environ.copy()
    node_path = shutil.which("node") or "/usr/local/bin/node"
    node_dir = os.path.dirname(node_path)
    env["PATH"] = f"{node_dir}:{env.get('PATH', '')}"
    brave_api_key = os.getenv("BRAVE_API_KEY")
    if brave_api_key:
        env["BRAVE_API_KEY"] = brave_api_key
    return env


def default_state() -> dict[str, str | bool]:
    return {"awaiting_confirmation": False, "request": "", "proposal": ""}


class TravelWorkflow:
    def __init__(self):
        env = build_env()
        npx_command = shutil.which("npx") or "/usr/local/bin/npx"

        self.researcher_params = [
            {
                "command": npx_command,
                "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                "env": env,
            },
            {
                "command": npx_command,
                "args": [
                    "-y",
                    "@playwright/mcp@latest",
                    "--browser",
                    "chromium",
                    "--headless",
                    "--isolated",
                ],
                "env": env,
            },
        ]
        self.browser_params = [
            {
                "command": npx_command,
                "args": [
                    "-y",
                    "@playwright/mcp@latest",
                    "--browser",
                    "chromium",
                    "--headless",
                    "--isolated",
                ],
                "env": env,
            }
        ]

    async def get_travel_researcher(self, mcp_servers) -> Agent:
        instructions = f"""You are a travel researcher.
You can use Brave Search and Playwright browser tools to investigate live travel options on the web.
Look for practical hotel, neighborhood, transport, food, and activity options that match the user's request.
When you cite options, include useful details such as approximate pricing, location, and why each option fits.
Be concise and organized. The current datetime is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}."""
        return Agent(
            name="TravelResearcher",
            instructions=instructions,
            model="gpt-4.1-mini",
            mcp_servers=mcp_servers,
        )

    async def get_travel_researcher_tool(self, mcp_servers) -> Tool:
        researcher = await self.get_travel_researcher(mcp_servers)
        return researcher.as_tool(
            tool_name="TravelResearcher",
            tool_description="Research live travel options on the web using Brave Search and Playwright.",
        )

    async def propose_trip(self, request: str) -> str:
        async with AsyncExitStack() as stack:
            researcher_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params=params, client_session_timeout_seconds=90)
                )
                for params in self.researcher_params
            ]
            researcher_tool = await self.get_travel_researcher_tool(researcher_servers)
            planner = Agent(
                name="TravelPlanner",
                instructions="""You are a travel planner.
Use the TravelResearcher tool to gather live options and create a practical shortlist.
Do not browse or book directly in this phase.
Respond with:
1. A short trip summary.
2. A shortlist of the best hotel and activity options.
3. A recommended plan.
4. A final line starting with READY_FOR_CONFIRMATION:""",
                model="gpt-4o-mini",
                tools=[researcher_tool],
            )
            with trace("travel-planner-proposal"):
                result = await Runner.run(planner, request, max_turns=MAX_TURNS)
        return result.final_output

    async def execute_booking(self, request: str, proposal: str) -> str:
        async with AsyncExitStack() as stack:
            researcher_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params=params, client_session_timeout_seconds=120)
                )
                for params in self.researcher_params
            ]
            browser_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params=params, client_session_timeout_seconds=120)
                )
                for params in self.browser_params
            ]
            researcher_tool = await self.get_travel_researcher_tool(researcher_servers)
            booking_agent = Agent(
                name="TravelBooker",
                instructions="""You are a browser-assisted travel booking agent.
Use the TravelResearcher tool if you need to refresh or verify live options.
Use Playwright browser tools to search travel sites, click through hotel or activity pages, and reach booking or checkout flows.
You may navigate, click, fill search fields, change dates, and compare offers.
Never enter payment details.
Never click a final button that would create a real reservation, charge a card, or submit an irreversible booking.
Stop at the final review or checkout step and summarize exactly what you reached, what site you used, and what remains for the human to finish.""",
                model="gpt-4o-mini",
                tools=[researcher_tool],
                mcp_servers=browser_servers,
            )
            prompt = f"""Original request:
{request}

Approved proposal:
{proposal}

Proceed with browser-assisted booking work now.
Search for the recommended options, click through booking flows, and get as far as you safely can.
Stop before any irreversible confirmation or payment step.
Then return a concise operational summary with the site visited, the option selected, and the final page reached."""
            with trace("travel-booking-browser"):
                result = await Runner.run(booking_agent, prompt, max_turns=MAX_TURNS)
        return result.final_output


def create_travel_ui():
    workflow = TravelWorkflow()
    example_requests = [
        [
            "Plan a 3-day Lagos birthday staycation with a quiet hotel, art spots, good food, and a moderate budget."
        ],
        [
            "Plan a 4-day Paris trip for two with boutique hotels, museums, river views, and one special anniversary dinner."
        ],
    ]

    async def submit_message(message, history, state):
        message = (message or "").strip()
        history = history or []
        state = state or default_state()
        if not message:
            return history, state, ""

        history = history + [{"role": "user", "content": message}]
        if state["awaiting_confirmation"] and message.lower() == "confirm":
            booking_summary = await workflow.execute_booking(
                str(state["request"]), str(state["proposal"])
            )
            history.append({"role": "assistant", "content": booking_summary})
            return history, default_state(), ""

        proposal = await workflow.propose_trip(message)
        confirmation_note = (
            "\n\nClick `Confirm Browsing` or reply with `CONFIRM` to let me continue "
            "with Playwright-driven browsing up to the final review or checkout step."
        )
        history.append({"role": "assistant", "content": proposal + confirmation_note})
        next_state = {
            "awaiting_confirmation": True,
            "request": message,
            "proposal": proposal,
        }
        return history, next_state, ""

    async def confirm_booking(history, state):
        history = history or []
        state = state or default_state()
        if not state["awaiting_confirmation"]:
            history.append(
                {
                    "role": "assistant",
                    "content": "Send a trip request first, then I can prepare a plan for confirmation.",
                }
            )
            return history, state
        booking_summary = await workflow.execute_booking(
            str(state["request"]), str(state["proposal"])
        )
        history.append({"role": "assistant", "content": booking_summary})
        return history, default_state()

    def cancel_booking(history, state):
        history = history or []
        history.append(
            {
                "role": "assistant",
                "content": "Booking was cancelled. Send a new travel request whenever you're ready.",
            }
        )
        return history, default_state()

    with gr.Blocks(title="Travel Planner", theme=gr.themes.Default(primary_hue="sky")) as ui:
        gr.Markdown(
            """### Travel Planner

Plan a trip from a chat prompt, then explicitly confirm before browser automation continues.
The browser workflow stops before any irreversible booking or payment step."""
        )
        chatbot = gr.Chatbot(type="messages", height=500)
        state = gr.State(default_state())
        with gr.Row():
            textbox = gr.Textbox(
                label="Trip request",
                placeholder="Plan a 3-day Lagos birthday staycation with a quiet hotel, art spots, and a memorable dinner.",
                scale=5,
            )
        gr.Examples(
            examples=example_requests,
            inputs=[textbox],
            label="Example Requests",
        )
        with gr.Row():
            confirm_btn = gr.Button("Confirm Browsing", variant="primary")
            cancel_btn = gr.Button("Cancel Pending Request")

        textbox.submit(submit_message, [textbox, chatbot, state], [chatbot, state, textbox])
        confirm_btn.click(confirm_booking, [chatbot, state], [chatbot, state])
        cancel_btn.click(cancel_booking, [chatbot, state], [chatbot, state])

    return ui
