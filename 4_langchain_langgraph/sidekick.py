"""The Sidekick: a create_agent worker wrapped in a homemade evaluator loop.

The worker is a single create_agent (Layer 3). Around it we run our own loop that checks
the worker's answer against the user's success criteria, and either accepts it, sends it
back for another attempt, or returns to the user with a question.
"""

import os
import uuid

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from sidekick_tools import get_all_tools

load_dotenv(override=True)

HERE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(HERE, "sandbox")
PLAYWRIGHT_CONFIG = os.path.join(HERE, "playwright-config.json")
MAX_ATTEMPTS = 3


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if the assistant has a question, needs clarification, or is stuck and needs the user"
    )


WORKER_PROMPT = """You are Sidekick, a capable personal assistant who completes tasks for the user.
You have a real web browser, a sandbox filesystem, web search, Wikipedia, and the ability to send push notifications.
When you use the browser, navigate to a page and read it with a snapshot rather than clicking around unnecessarily.
Keep working on the task until the success criteria is met, or until you genuinely need to ask the user a question.
If you have a question, ask it plainly. When you are finished, give your final answer clearly."""


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
    def __init__(self):
        self.sidekick_id = str(uuid.uuid4())
        self.memory = InMemorySaver()
        self.tools = None
        self.client = None
        self.worker = None
        self.evaluator = None

    async def setup(self):
        os.makedirs(SANDBOX, exist_ok=True)
        self.tools, self.client = await get_all_tools(SANDBOX, PLAYWRIGHT_CONFIG)
        self.worker = create_agent(
            model=ChatOpenAI(model="gpt-5.4-mini"),
            tools=self.tools,
            system_prompt=WORKER_PROMPT,
            middleware=[TolerateToolErrors()],
            checkpointer=self.memory,
        )
        self.evaluator = ChatOpenAI(model="gpt-5.4-mini").with_structured_output(EvaluatorOutput)

    async def evaluate(self, message: str, success_criteria: str, last_reply: str) -> EvaluatorOutput:
        prompt = f"""You decide whether an assistant has met the success criteria for a task.

The user's request was:
{message}

The success criteria is:
{success_criteria}

The assistant's most recent reply was:
{last_reply}

Decide whether the success criteria is met. Also decide whether the assistant needs more input from the user,
either because it asked a question, needs clarification, or seems stuck. Give brief, concrete feedback."""
        return await self.evaluator.ainvoke(prompt)

    async def run_superstep(self, message: str, success_criteria: str, history: list) -> list:
        config = {"configurable": {"thread_id": self.sidekick_id}}
        success_criteria = success_criteria or "The answer should be clear, correct and complete"
        task = f"{message}\n\nThe success criteria for this task is: {success_criteria}"

        reply, verdict = "", None
        for _ in range(MAX_ATTEMPTS):
            result = await self.worker.ainvoke({"messages": [{"role": "user", "content": task}]}, config=config)
            reply = result["messages"][-1].content
            verdict = await self.evaluate(message, success_criteria, reply)
            if verdict.success_criteria_met or verdict.user_input_needed:
                break
            task = (
                f"Your last response did not meet the success criteria. Here is the feedback: {verdict.feedback}. "
                "Please keep working and address it."
            )

        return history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": reply},
            {"role": "assistant", "content": f"Evaluator feedback: {verdict.feedback}"},
        ]

    def cleanup(self):
        # Release the MCP client so its browser and filesystem servers can shut down.
        self.client = None
