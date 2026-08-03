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
from monitoring_tools import get_tools
import uuid
from datetime import datetime
import json

load_dotenv(override=True)



class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    transaction: Optional[dict]
    decision: Optional[str]
    risk_score: Optional[float]


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(description="True if more input is needed from the user, or clarifications, or the assistant is stuck")


class Monitoring:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools = None
        self.graph = None
        self.monitoring_id = str(uuid.uuid4())
        self.memory = MemorySaver()

    async def setup(self):
        self.tools = get_tools()

        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)

        evaluator_llm = ChatOpenAI(model="gpt-4o-mini")
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)

        await self.build_graph()

    def worker(self, state: State) -> Dict[str, Any]:
        transaction_input = state.get("transaction_input") or state.get("transaction") or {}
        print(f"Transaction input: {transaction_input}")

        if isinstance(transaction_input, str):
            try:
                transaction_input = json.loads(transaction_input)
            except Exception:
                pass

        print(f"Transaction input (for LLM): {transaction_input}")

        system_message = f"""
        You are a compliance monitoring assistant.

        You are provided with a transaction data and you need to follow this process (you can skip steps if you don't have the data):

        - Sanctions check using tools
        - Check transaction history
        - Perform velocity check
        - Make a compliance decision (approve / flag / escalate)
        - Save the result using tools
        - Send notification

        Rules:
        - Always ask for clarification if required data is missing or input is invalid
        - Only return final decision if input is valid and all steps completed
        - Do NOT skip steps
        - Use tools when needed

        Current time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        Current transaction input (may be invalid):
        {json.dumps(transaction_input, indent=2) if isinstance(transaction_input, dict) else transaction_input}
        """

        if state.get("feedback_on_work"):
            system_message += f"""
    Previous attempt failed. Feedback:
    {state['feedback_on_work']}

    Fix the issues and try again.
    """

        messages = state["messages"]

        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=system_message)] + messages
        else:
            for m in messages:
                if isinstance(m, SystemMessage):
                    m.content = system_message

        response = self.worker_llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def worker_router(self, state: State) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "evaluator"

    def format_conversation(self, messages: List[Any]) -> str:
        conversation = ""
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                conversation += f"Assistant: {message.content or '[Tool call]'}\n"
        return conversation

    def evaluator(self, state: State) -> State:
        last_response = state["messages"][-1].content

        system_message = "You are evaluating whether a compliance monitoring task was completed correctly."

        user_message = f"""
Conversation:
{self.format_conversation(state['messages'])}

Success criteria:
{state['success_criteria']}

Last response:
{last_response}

Check:
- Was transaction analyzed?
- Were tools used (sanctions, history, velocity)?
- Was a decision made?
- Was result saved and user notified?

Return feedback + decision.
"""

        if state.get("feedback_on_work"):
            user_message += f"\nPrevious feedback: {state['feedback_on_work']}"

        eval_result = self.evaluator_llm_with_output.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ])

        return {
            "messages": [{
                "role": "assistant",
                "content": f"Evaluator Feedback: {eval_result.feedback}",
            }],
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
            "worker",
            self.worker_router,
            {"tools": "tools", "evaluator": "evaluator"},
        )

        graph_builder.add_edge("tools", "worker")

        graph_builder.add_conditional_edges(
            "evaluator",
            self.route_based_on_evaluation,
            {"worker": "worker", "END": END},
        )

        graph_builder.add_edge(START, "worker")

        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, transaction: dict, history: list):
        config = {"configurable": {"thread_id": self.monitoring_id}}

        state = {
            "messages": [],  
            "success_criteria": """
                - Analyze transaction
                - Perform sanctions check
                - Check transaction history
                - Perform velocity check
                - Make compliance decision (approve/flag/escalate)
                - Save result
                - Send notification
            """,
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,

           
            "transaction": transaction,
            "decision": None,
            "risk_score": None,
        }

        result = await self.graph.ainvoke(state, config=config)

        reply = result["messages"][-2].content
        feedback = result["messages"][-1].content

        return history + [
            {"role": "assistant", "content": reply},
            {"role": "assistant", "content": feedback},
        ]

  