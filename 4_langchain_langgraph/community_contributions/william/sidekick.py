from typing import Annotated, List, Any, Optional, Dict
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from sidekick_tools import playwright_tools, other_tools
import uuid
import asyncio
from datetime import datetime

load_dotenv(override=True)


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )


class Sidekick:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None

    async def setup(self):
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()
        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        evaluator_llm = ChatOpenAI(model="gpt-4o-mini")
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        await self.build_graph()

    def worker(self, state: State) -> Dict[str, Any]:
        system_message = f"""You are an expert travel planner sidekick. You help users plan detailed, personalized travel itineraries.

You have access to tools to search the web, browse websites, look up Wikipedia, run Python code, and write files to a sandbox directory.

When planning a trip, you should:
- Research the destination thoroughly (weather, local customs, visa requirements, currency)
- Find top-rated attractions, restaurants, and experiences matching the user's interests and budget
- Build a structured day-by-day itinerary with time slots, locations, estimated costs, and travel tips
- Include practical details: transportation between spots, opening hours, booking links when available
- Suggest budget breakdowns (accommodation, food, activities, transport)
- Note any safety tips, local etiquette, or seasonal considerations
- Save the final itinerary as a markdown file in the sandbox using the file write tool

The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

This is the success criteria:
{state["success_criteria"]}

You should reply either with a question for the user about this trip, or with your final itinerary.
If you have a question, clearly state it. Example:

Question: How many days are you planning to stay, and what's your approximate daily budget?

If you've finished, reply with the complete itinerary and don't ask further questions."""

        if state.get("feedback_on_work"):
            system_message += f"""
Previously you thought you completed the itinerary, but it was rejected because the success criteria was not met.
Here is the feedback:
{state["feedback_on_work"]}
With this feedback, please revise and improve the itinerary, ensuring you meet the success criteria or have a question for the user."""

        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.worker_llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def worker_router(self, state: State) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "evaluator"

    def format_conversation(self, messages: List[Any]) -> str:
        conversation = "Conversation history:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Tools use]"
                conversation += f"Assistant: {text}\n"
        return conversation

    def evaluator(self, state: State) -> State:
        last_response = state["messages"][-1].content

        system_message = """You are an evaluator for a travel planning assistant.
Assess whether the assistant has produced a complete, practical, and well-researched travel itinerary.
A good itinerary should include: day-by-day breakdown, specific place names, estimated costs, transportation tips, and practical travel advice.
Respond with feedback and your decision on whether the criteria are met."""

        user_message = f"""You are evaluating a travel itinerary conversation between User and Assistant.

The entire conversation is:
{self.format_conversation(state["messages"])}

The success criteria for this itinerary is:
{state["success_criteria"]}

The final response from the Assistant:
{last_response}

Decide if the success criteria is met. A quality travel itinerary should have:
- Day-by-day schedule with specific times and places
- Estimated costs or budget guidance
- Practical logistics (transport, booking tips)
- Tailored to the user's stated preferences

Also decide if more user input is required (the assistant has a question, needs clarification, or seems stuck).
The Assistant can write files to a sandbox. If they say they saved a file, trust that."""

        if state["feedback_on_work"]:
            user_message += f"\nPrevious feedback you gave: {state['feedback_on_work']}\n"
            user_message += "If the Assistant is repeating the same mistakes, respond that user input is required."

        evaluator_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]
        eval_result = self.evaluator_llm_with_output.invoke(evaluator_messages)
        return {
            "messages": [
                {"role": "assistant", "content": f"Evaluator Feedback: {eval_result.feedback}"}
            ],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }

    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        return "worker"

    async def build_graph(self):
        graph_builder = StateGraph(State)

        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
        )
        graph_builder.add_edge(START, "worker")

        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message, success_criteria, history):
        config = {"configurable": {"thread_id": self.sidekick_id}}

        state = {
            "messages": message,
            "success_criteria": success_criteria or "Produce a detailed, day-by-day travel itinerary with specific places, estimated costs, and practical travel tips",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
        }
        result = await self.graph.ainvoke(state, config=config)
        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-2].content}
        feedback = {"role": "assistant", "content": result["messages"][-1].content}
        return history + [user, reply, feedback]

    def cleanup(self):
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
                if self.playwright:
                    loop.create_task(self.playwright.stop())
            except RuntimeError:
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())
