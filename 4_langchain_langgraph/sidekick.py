"""The Sidekick: a create_agent worker wrapped in a homemade evaluator loop.

The worker is a single create_agent (Layer 3). Around it we run our own loop that checks
the worker's answer against the user's success criteria, and either accepts it, sends it
back for another attempt, or returns to the user with a question. Middleware gives the
worker a plan it shares with the UI, guardrails for PII and runaway costs, and a pause
for human approval before sensitive actions.
"""

import os
import uuid
from datetime import datetime

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import (
    AgentMiddleware,
    HumanInTheLoopMiddleware,
    ModelCallLimitMiddleware,
    PIIMiddleware,
    TodoListMiddleware,
)
from langchain_core.messages import ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from sidekick_tools import get_all_tools

load_dotenv(override=True)

HERE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(HERE, "sandbox")
MAX_ATTEMPTS = 3


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if the assistant has a question, needs clarification, or is stuck and needs the user"
    )


WORKER_PROMPT = """You are Sidekick, a capable personal assistant who completes tasks for the user.
You have a real web browser, a sandbox filesystem, web search, Wikipedia, and the ability to send push notifications and emails.
When you use the browser, navigate to a page and read it with a snapshot rather than clicking around unnecessarily.
Dismiss cookie banners and popups yourself by clicking in the browser. If you reach something only a human can do,
like logging in, a captcha, or two-factor authentication, use the request_human_help tool to tell the user exactly
what to do in your browser window, then carry on once they have done it.
For flight searches:
1. First open Expedia and attempt to sign in to the user's Expedia account.
   If login requires credentials, a captcha, two-factor authentication, or any other
   human-only action, call request_human_help and wait for the user.
2. Search Google Flights using a natural-language query such as
   "flights from New York to London leaving 14 July returning 21 July": go  to https://www.google.com/travel/flights?q=...
3. Cross-check promising fares directly with KLM. https://www.klm.sg/ and check the flights there,
4. Cross-check promising fares directly with Qatar Airways. https://www.qatarairways.com/en-sg/homepage.html
5. Compare the results and clearly state which prices came from which source.
with a natural language query like "flights from New York to London leaving 14 July returning 21 July".

For Stock and investemtns advice:
1. First open Yahoo Finance and attempt to sign in to the user's Yahoo Finance account.
   If login requires credentials, a captcha, two-factor authentication, or any other
   human-only action, call request_human_help and wait for the user.
2. Search Yahoo Finance using a natural-language query such as
   "stocks to buy for long-term growth": go to https://finance.yahoo.com/
3. Cross-check promising stocks directly with the user's broker.
4. Compare the results and clearly state which stocks came from which source.


CALENDAR AND MESSAGE HANDLING

Whenever the user asks to prepare, extract, convert, review, or add information
from a message into calendar-ready form, you MUST call the
prepare_calendar_candidate tool.

Do not merely describe a proposed calendar event in prose.

Use prepare_calendar_candidate with:
- action_type
- title
- start
- end
- timezone
- timezone_source
- all_day
- location
- notes
- confidence

CALENDAR SELECTION

When creating an approved calendar event, choose the destination calendar using these rules:

1. Use "Family Calendar" for:
   - school events
   - children's activities
   - family appointments
   - family travel
   - events involving Diana, Alexandra, or Isabella
   - household/family commitments that other family members may need to see

2. Use "Private bork" for:
   - the user's personal appointments
   - personal reminders
   - private meetings
   - personal admin
   - individual commitments that do not need to be shared with the family

3. If the appropriate calendar is unclear:
   - do not guess
   - ask the user which calendar to use before creating the event

4. If the user explicitly names a calendar, always use that calendar.

5. Never write to any other calendar unless the user explicitly asks for it.


CLASSIFY THE ITEM

If the message describes a genuine scheduled activity, use:
action_type="calendar_event"

If it describes something the user needs to remember or do, but not a
scheduled activity, use:
action_type="reminder"

If it does not represent an actionable calendar or reminder item, use:
action_type="ignore"


MISSING INFORMATION

Never invent missing dates, times, locations, people, or durations.

If information is unknown, leave it unknown.

Do not infer a location merely because you know contextual information about
the sender, school, workplace, family member, or user.

Only use a location if it is explicitly present in the source message or
retrieved message context.


DATE-ONLY AND ALL-DAY ITEMS

If a message contains a specific date but no specific time:

- Set all_day=true.
- Store start as YYYY-MM-DD.
- Set end=None unless the message explicitly gives a multi-day date range.
- Do not invent a start time.
- Do not invent an end time.
- Do not invent a duration.

A date-only item is NOT considered a timed event.


TIMED EVENTS

If a message contains a specific start time:

- Set all_day=false.
- Store start as an ISO 8601 datetime including timezone offset.
- Only provide end if it is explicitly given or can be determined directly
  from unambiguous source information.
- Do not invent an end time.


TIMEZONE HANDLING

Every calendar candidate must contain an IANA timezone.

Examples:
- Singapore: Asia/Singapore
- Norway: Europe/Oslo
- London: Europe/London
- Tokyo: Asia/Tokyo

Determine timezone in this order:

1. If the message explicitly identifies a timezone, use it.
2. If an explicitly stated event location clearly identifies a timezone,
   infer it from that location.
3. Otherwise use the user's default timezone: Asia/Singapore.

Set timezone_source to:
- explicit
- inferred
- default

Never silently convert the event into another timezone when preparing it.
Preserve the event's local time and timezone.


CALENDAR AVAILABILITY — STRICT RULE

Call check_calendar_availability ONLY when ALL of the following are true:

1. all_day=false
2. start contains a specific time
3. end contains a specific time

If ANY of these conditions is false:

- DO NOT call check_calendar_availability.
- DO NOT search the calendar for conflicts.
- DO NOT report other events on that date as conflicts.
- State that timed availability cannot be determined because the event does
  not have both a specific start and end time.

This rule is mandatory and overrides any general instruction to check for
calendar conflicts.


OUTPUT

After calling prepare_calendar_candidate:

- Show the resulting candidate clearly.
- If availability was checked, show genuine overlapping conflicts only.
- If availability was not checked, explain why.
- State that the item has not yet been written to the calendar.

Never claim an event has been added to the calendar unless a separate
calendar-write tool has completed successfully.


Keep working on the task until the success criteria are met, or until you genuinely need to ask the user a question.
If you have a question, ask it plainly. When you are finished, give your final answer clearly,
saying what you did, what you produced, and what you found."""


class TolerateToolErrors(AgentMiddleware):
    """Hand tool failures back to the model as a message so it can recover, rather than
    crashing the run. Tools that touch the outside world, like a browser, fail now and then."""

    async def awrap_tool_call(self, request, handler):
        try:
            return await handler(request)
        except Exception as error:
            return ToolMessage(
                content=f"That tool call failed: {error}. Try another approach.",
                tool_call_id=request.tool_call["id"],
            )


class Sidekick:
    def __init__(self, model: str = "openai:gpt-5.4-mini"):
        self.model = model 
        self.sidekick_id = str(uuid.uuid4())
        self.memory = InMemorySaver()
        self.tools = None
        self.sessions = None
        self.worker = None
        self.evaluator = None
        self.task = ""
        self.success_criteria = ""
        self.attempts = 0
        self.paused = False
        self.pending_actions = 0
        self.todos = []

    async def setup(self):
        print("\n>>> SIDEKICK.SETUP STARTED")

        os.makedirs(SANDBOX, exist_ok=True)
        print(">>> Sandbox ready:", SANDBOX)

        print(">>> Calling get_all_tools()...")
        self.tools, self.sessions = await get_all_tools(SANDBOX)

        print(f">>> get_all_tools() returned {len(self.tools)} tools")
        print(">>> SIDEKICK.SETUP CONTINUES")

        print(f"Setting up worker with model: {self.model}")
        
        self.worker = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=f"{WORKER_PROMPT}\nToday is {datetime.now():%A %d %B %Y}.",
            middleware=[
                TolerateToolErrors(),
                TodoListMiddleware(),
                PIIMiddleware("email"),
                PIIMiddleware("credit_card", apply_to_tool_results=True),
                ModelCallLimitMiddleware(run_limit=30),
                HumanInTheLoopMiddleware(
                    interrupt_on={"send_push_notification": True, "request_human_help": True, "send_email": True,}
                ),
            ],
            checkpointer=self.memory,
        )
        self.evaluator = ChatOpenAI(model="gpt-5.4-mini").with_structured_output(EvaluatorOutput)

    async def evaluate(
        self, message: str, success_criteria: str, last_reply: str, tools_used: list[str]
    ) -> EvaluatorOutput:
        prompt = f"""You decide whether an assistant has met the success criteria for a task.

The user's request was:
{message}

The success criteria are:
{success_criteria}

The tools the assistant called while working, in order:
{", ".join(tools_used) or "none"}

The assistant's most recent reply was:
{last_reply}

Decide whether the success criteria are met, using the tool calls as evidence of what was actually done.
Also decide whether the assistant needs more input from the user, either because it asked a question,
needs clarification, or seems stuck. Give brief, concrete feedback."""
        return await self.evaluator.ainvoke(prompt)

    async def run_turn(self, message: str, success_criteria: str, history: list) -> list:
        """One turn of conversation: the worker attempts the task and the evaluator checks it,
        retrying with feedback up to MAX_ATTEMPTS. If the worker pauses for approval, this
        returns straight away with paused set, and resume() continues the same turn."""
        self.task = message
        self.success_criteria = success_criteria or "The answer should be clear, correct and complete"
        self.attempts = 0
        self.todos = []
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": f"{message}\n\nThe success criteria for this task are: {self.success_criteria}",
                }
            ]
        }
        return await self._advance(payload, history + [{"role": "user", "content": message}])

    async def resume(self, history: list) -> list:
        """Approve the actions the worker paused on, and continue the turn."""
        payload = Command(resume={"decisions": [{"type": "approve"}] * self.pending_actions})
        return await self._advance(payload, history)

    async def _advance(self, payload, history: list) -> list:
        config = {"configurable": {"thread_id": self.sidekick_id}}
        while True:
            result = None
            async for result in self.worker.astream(payload, config=config, stream_mode="values"):
                self.todos = result.get("todos", self.todos)

            if "__interrupt__" in result:
                actions = result["__interrupt__"][0].value["action_requests"]
                self.paused = True
                self.pending_actions = len(actions)
                described = "\n".join(action["description"] for action in actions)
                return history + [{"role": "assistant", "content": f"Waiting for your approval:\n{described}"}]

            self.paused = False
            reply = result["messages"][-1].content
            tools_used = [
                call["name"] for m in result["messages"] for call in (getattr(m, "tool_calls", None) or [])
            ]
            self.attempts += 1
            verdict = await self.evaluate(self.task, self.success_criteria, reply, tools_used)
            if verdict.success_criteria_met or verdict.user_input_needed or self.attempts >= MAX_ATTEMPTS:
                return history + [
                    {"role": "assistant", "content": reply},
                    {"role": "assistant", "content": f"Evaluator: {verdict.feedback}"},
                ]
            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": f"Your last response did not meet the success criteria. "
                        f"Here is the feedback: {verdict.feedback}. Please keep working and address it.",
                    }
                ]
            }

    def cleanup(self):
        """Shut down the MCP servers; the browser window closes."""
        if self.sessions:
            self.sessions.stop()
