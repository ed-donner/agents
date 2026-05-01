from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import List, Any, Optional, Dict
from pydantic import BaseModel, Field
from sidekick_tools import playwright_tools, other_tools
import uuid
import asyncio
from datetime import datetime

load_dotenv(override=True)


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(
        description="Whether the success criteria have been met"
    )
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )


class PlanOutput(BaseModel):
    list_of_steps: List[str] = Field(
        description="A list of steps to accomplish the user's request"
    )
    estimated_complexity: str = Field(
        description="The estimated complexity of the steps"
    )


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    planning_complete: bool
    plan: Optional[PlanOutput] = None
    final_worker_response: Optional[str]
    engagement_questions: Optional[str]


class Sidekick:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.engagement_llm = None
        self.tools = None
        self.llm_with_tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory_ctx = None
        self.memory = None
        self.browser = None
        self.playwright = None

    async def setup(self):
        if self.memory is None:
            self.memory_ctx = AsyncSqliteSaver.from_conn_string("sidekick_memory.db")
            self.memory = await self.memory_ctx.__aenter__()

        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()
        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        planner_llm = ChatOpenAI(model="gpt-4o-mini")
        self.planner_llm = planner_llm.with_structured_output(PlanOutput)
        evaluator_llm = ChatOpenAI(model="gpt-4o-mini")
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(
            EvaluatorOutput
        )
        self.engagement_llm = ChatOpenAI(model="gpt-4o-mini")
        self.planner_llm_evaluator = planner_llm.with_structured_output(EvaluatorOutput)
        await self.build_graph()

    def worker(self, state: State) -> Dict[str, Any]:
        system_message = f"""You are a helpful assistant that can use tools to complete tasks.
    You keep working on a task until either you have a question or clarification for the user, or the success criteria is met.
    You have many tools to help you, including tools to browse the internet, navigating and retrieving web pages.
    You have a tool to run python code, but note that you would need to include a print() statement if you wanted to receive output.
    The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    You received a list of steps to accomplish the user's request:
    {state["plan"].list_of_steps}
    The estimated complexity of the steps is:
    {state["plan"].estimated_complexity}

    You should follow the steps in the order they are listed.
    This is the success criteria:
    {state["success_criteria"]}
    You should reply either with a question for the user about this assignment, or with your final response.
    If you have a question for the user, you need to reply by clearly stating your question. An example might be:

    Question: please clarify whether you want a summary or a detailed answer

    If you've finished, reply with the final answer, and don't ask a question; simply reply with the answer.
    """

        if state.get("feedback_on_work"):
            system_message += f"""
    Previously you thought you completed the assignment, but your reply was rejected because the success criteria was not met.
    Here is the feedback on why this was rejected:
    {state["feedback_on_work"]}
    With this feedback, please continue the assignment, ensuring that you meet the success criteria or have a question for the user."""

        # Add in the system message

        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        # Invoke the LLM with tools
        response = self.worker_llm_with_tools.invoke(messages)

        # Return updated state
        current_response = (
            response.content
            if isinstance(response, AIMessage) and response.content
            else state.get("final_worker_response")
        )
        return {
            "messages": [response],
            "final_worker_response": current_response,
        }

    def planner(self, state: State) -> State:
        system_message = f"""You are a planner that determines the next action to take based on the user's request.
        You have a list of tools to help you, including tools to browse the internet, navigating and retrieving web pages.
        You have a tool to run python code, but note that you would need to include a print() statement if you wanted to receive output.
        The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        Use the full conversation context to keep continuity and avoid repeating already completed work.
        """

        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.planner_llm.invoke(messages)
        plan = PlanOutput(
            list_of_steps=response.list_of_steps,
            estimated_complexity=response.estimated_complexity,
        )

        return {
            "messages": [
                AIMessage(
                    content=(
                        "Plan generated.\n"
                        f"Steps: {plan.list_of_steps}\n"
                        f"Estimated complexity: {plan.estimated_complexity}"
                    )
                )
            ],
            "plan": plan,
        }

    def planner_router(self, state: State) -> str:
        return "planner_evaluator"

    def worker_router(self, state: State) -> str:
        last_message = state["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        else:
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

        system_message = """You are an evaluator that determines if a task has been completed successfully by an Assistant.
    Assess the Assistant's last response based on the given criteria. Respond with your feedback, and with your decision on whether the success criteria has been met,
    and whether more input is needed from the user."""

        user_message = f"""You are evaluating a conversation between the User and Assistant. You decide what action to take based on the last response from the Assistant.

    The entire conversation with the assistant, with the user's original request and all replies, is:
    {self.format_conversation(state["messages"])}

    The success criteria for this assignment is:
    {state["success_criteria"]}

    And the final response from the Assistant that you are evaluating is:
    {last_response}

    Respond with your feedback, and decide if the success criteria is met by this response.
    Also, decide if more user input is required, either because the assistant has a question, needs clarification, or seems to be stuck and unable to answer without help.

    The Assistant has access to a tool to write files. If the Assistant says they have written a file, then you can assume they have done so.
    Overall you should give the Assistant the benefit of the doubt if they say they've done something. But you should reject if you feel that more work should go into this.

    """
        if state["feedback_on_work"]:
            user_message += f"Also, note that in a prior attempt from the Assistant, you provided this feedback: {state['feedback_on_work']}\n"
            user_message += "If you're seeing the Assistant repeating the same mistakes, then consider responding that user input is required."

        evaluator_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        eval_result = self.evaluator_llm_with_output.invoke(evaluator_messages)
        new_state = {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Evaluator Feedback on this answer: {eval_result.feedback}",
                }
            ],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }
        return new_state

    def planner_evaluator(self, state: State) -> State:
        user_request = next(
            (
                msg.content
                for msg in reversed(state["messages"])
                if isinstance(msg, HumanMessage)
            ),
            "",
        )
        system_message = """You are an evaluator that determines if a planner has emmited a good plan to accomplish the user's request. You fact check the plan combined
        with the user's request to ensure that the plan is feasible and realistic.
        You ensure that the user did not enter trash or ilegible words or requests.
        """

        user_message = f"""You are evaluating a plan to address the user's request. The Planner has emmited a plan to accomplish the user's request.
        You need to assess the plan and determine if it is a good plan.
        The user's request is:
        {user_request}
        The plan is:
        {state["plan"].list_of_steps}
        The estimated complexity of the steps is:
        {state["plan"].estimated_complexity}
        """

        planner_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        planner_result = self.planner_llm_evaluator.invoke(planner_messages)
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Planner Feedback on this plan: {planner_result.feedback}",
                }
            ],
            "feedback_on_work": planner_result.feedback,
            "success_criteria_met": planner_result.success_criteria_met,
            "user_input_needed": planner_result.user_input_needed,
            "planning_complete": planner_result.success_criteria_met,
        }

    def route_based_on_evaluation(self, state: State) -> str:
        if state["user_input_needed"]:
            return "END"
        elif state["success_criteria_met"]:
            return "engagement"
        else:
            return "worker"

    def planner_evaluator_router(self, state: State) -> str:
        if state["user_input_needed"]:
            return "END"
        elif state["planning_complete"]:
            return "worker"
        else:
            return "planner"

    def engagement_agent(self, state: State) -> Dict[str, Any]:
        system_message = """You are an engagement assistant.

                            Your task:
                            - Review the user's request, the generated plan, and the evaluator feedback.
                            - Ask concise follow-up questions that improve progress on the task.

                            Rules:
                            - Ask 0 to 3 questions maximum.
                            - Ask questions only if they add decision-critical information (scope, preferences, constraints, missing data, priorities).
                            - Do not ask questions that are already answered in the conversation.
                            - Do not ask generic engagement questions.
                            - Keep each question specific, actionable, and under 20 words.
                            - If no clarification is needed, return exactly: NO_QUESTIONS

                            Output format:
                            - If asking questions, output one per line as:
                            Q1: ...
                            Q2: ...
                            Q3: ...
        """
        latest_user_message = next(
            (
                msg.content
                for msg in reversed(state["messages"])
                if isinstance(msg, HumanMessage)
            ),
            "",
        )
        latest_worker_response = state.get("final_worker_response") or next(
            (
                msg.content
                for msg in reversed(state["messages"])
                if isinstance(msg, AIMessage)
                and msg.content
                and "Plan generated." not in str(msg.content)
                and "Evaluator Feedback on this answer:" not in str(msg.content)
                and "Planner Feedback on this plan:" not in str(msg.content)
            ),
            "",
        )
        plan_steps = state["plan"].list_of_steps if state.get("plan") else []
        plan_complexity = (
            state["plan"].estimated_complexity if state.get("plan") else "unknown"
        )

        user_message = f"""The evaluator feedback was:
            {state.get("feedback_on_work") or "No evaluator feedback provided yet."}

            The plan was:
            Steps: {plan_steps}
            Estimated complexity: {plan_complexity}

            The latest user message was:
            {latest_user_message}

            The latest worker response was:
            {latest_worker_response or "No worker response available yet."}

            Based on this context, provide your engagement follow-up questions.
        """
        response = self.engagement_llm.invoke(
            [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message),
            ]
        )

        engagement_text = (response.content or "").strip()
        normalized_engagement = (
            engagement_text.upper().replace(" ", "_").rstrip(".!?")
            if engagement_text
            else ""
        )
        if not engagement_text or normalized_engagement == "NO_QUESTIONS":
            engagement_text = "NO_QUESTIONS"

        if engagement_text != "NO_QUESTIONS":
            lines = [
                line.strip() for line in engagement_text.splitlines() if line.strip()
            ]
            question_lines = [
                line for line in lines if line.startswith(("Q1:", "Q2:", "Q3:"))
            ]
            if question_lines:
                engagement_text = "\n".join(question_lines[:3])
            else:
                engagement_text = "NO_QUESTIONS"

        return {
            "messages": [AIMessage(content=engagement_text)],
            "engagement_questions": engagement_text,
        }

    async def build_graph(self):
        # Set up Graph Builder with State
        graph_builder = StateGraph(State)

        # Add nodes
        graph_builder.add_node("planner", self.planner)
        graph_builder.add_node("planner_evaluator", self.planner_evaluator)
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)
        graph_builder.add_node("engagement", self.engagement_agent)

        # Add edges
        graph_builder.add_edge(START, "planner")
        graph_builder.add_conditional_edges(
            "planner",
            self.planner_router,
            {"planner_evaluator": "planner_evaluator"},
        )
        graph_builder.add_conditional_edges(
            "planner_evaluator",
            self.planner_evaluator_router,
            {"planner": "planner", "worker": "worker", "END": END},
        )
        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator",
            self.route_based_on_evaluation,
            {"worker": "worker", "engagement": "engagement", "END": END},
        )
        graph_builder.add_edge("engagement", END)

        # Compile the graph
        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message, success_criteria, history):
        config = {"configurable": {"thread_id": self.sidekick_id}}

        state = {
            "messages": [HumanMessage(content=message)],
            "success_criteria": success_criteria
            or "The answer should be clear and accurate",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "planning_complete": False,
            "final_worker_response": None,
            "engagement_questions": None,
        }
        result = await self.graph.ainvoke(state, config=config)

        worker_response = result.get("final_worker_response") or ""
        engagement_response = result.get("engagement_questions") or ""
        combined_response = worker_response
        if engagement_response and str(engagement_response).strip() != "NO_QUESTIONS":
            combined_response = (
                f"{worker_response}\n\nFollow-up questions:\n{engagement_response}"
            )

        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": combined_response}
        feedback = {
            "role": "assistant",
            "content": f"Evaluator Feedback on this answer: {result.get('feedback_on_work') or ''}",
        }
        return history + [user, reply, feedback]

    def cleanup(self):
        async def _cleanup_async():
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            if self.memory_ctx:
                await self.memory_ctx.__aexit__(None, None, None)
                self.memory_ctx = None
                self.memory = None

        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_cleanup_async())
            except RuntimeError:
                asyncio.run(_cleanup_async())
        elif self.memory_ctx:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_cleanup_async())
            except RuntimeError:
                asyncio.run(_cleanup_async())
