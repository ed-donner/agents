from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import List, Any, Optional, Dict
from pydantic import BaseModel, Field
from sidekick_tools import playwright_tools, other_tools
from sqlite_memory import SQLiteMemory
import os
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
	clarifying_questions: Optional[List[str]]
	clarifying_answers: Optional[List[str]]
	clarifying_step: int

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
        self.planner_llm = None
        self.tools = None
        self.llm_with_tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = SQLiteMemory()
        self.browser = None
        self.playwright = None
        
    def serialize_message(self, message):
        
        if hasattr(message, 'to_dict'):
            return message.to_dict()
        if isinstance(message, dict):
            return message
        
        return {
            'type': type(message).__name__,
            'content': getattr(message, 'content', str(message)),
        }

    def serialize_state(self, state):
        
        state_copy = dict(state)
        if 'messages' in state_copy and isinstance(state_copy['messages'], list):
            state_copy['messages'] = [self.serialize_message(m) for m in state_copy['messages']]
        return state_copy


    async def setup(self):
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()
        worker_llm = ChatOpenAI(model="gpt-4o-mini",
                                base_url="https://openrouter.ai/api/v1",
                                api_key=os.getenv("OPENROUTER_API_KEY"))
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        evaluator_llm = ChatOpenAI(model="gpt-4o-mini",
                                    base_url="https://openrouter.ai/api/v1",
                                    api_key=os.getenv("OPENROUTER_API_KEY"))
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        self.planner_llm = ChatOpenAI(model="gpt-4o-mini",
                                    base_url="https://openrouter.ai/api/v1",
                                    api_key=os.getenv("OPENROUTER_API_KEY"))
        await self.build_graph()

    def planner(self, state: State) -> State:
        
        if "messages" not in state or not isinstance(state["messages"], list):
            state["messages"] = []
        # If clarifying questions are not yet generated, generate them
        if not state.get("clarifying_questions"):
            prompt = f"""You are a planner agent. Your job is to ask up to three clarifying questions to better understand the user's request before any work is done. \nUser's request: {state['messages'][0].content if state['messages'] else ''}\nPlease return a list of three concise, relevant clarifying questions. If fewer than three are needed, return as many as make sense."""
            questions = self.planner_llm.invoke([HumanMessage(content=prompt)])
            if isinstance(questions, list):
                qlist = [q.content for q in questions]
            else:
                qlist = [q.strip() for q in questions.content.split("\n") if q.strip()]
            result = {
                **state,
                "clarifying_questions": qlist[:3],
                "clarifying_answers": [],
                "clarifying_step": 0,
            }
            return result
        if len(state.get("clarifying_answers", [])) < len(state.get("clarifying_questions", [])):
            return state  
        # All clarifications collected, move to worker
        result = {
            **state,
            "clarifying_step": len(state["clarifying_questions"]),
        }
        return result

    def worker(self, state: State) -> Dict[str, Any]:
        
        if "messages" not in state or not isinstance(state["messages"], list):
            state["messages"] = []
        
        if "success_criteria" not in state:
            state["success_criteria"] = "The answer should be clear and accurate"
        system_message = f"""You are a helpful assistant that can use tools to complete tasks.\nYou keep working on a task until either you have a question or clarification for the user, or the success criteria is met.\nYou have many tools to help you, including tools to browse the internet, navigating and retrieving web pages.\nYou have a tool to run python code, but note that you would need to include a print() statement if you wanted to receive output.\nThe current date and time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nThis is the success criteria:\n{state['success_criteria']}\nYou should reply either with a question for the user about this assignment, or with your final response.\nIf you have a question for the user, you need to reply by clearly stating your question. An example might be:\n\nQuestion: please clarify whether you want a summary or a detailed answer\n\nIf you've finished, reply with the final answer, and don't ask a question; simply reply with the answer.\n"""
        if state.get("feedback_on_work"):
            system_message += f"\nPreviously you thought you completed the assignment, but your reply was rejected because the success criteria was not met.\nHere is the feedback on why this was rejected:\n{state['feedback_on_work']}\nWith this feedback, please continue the assignment, ensuring that you meet the success criteria or have a question for the user."
        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True
        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages
        response = self.worker_llm_with_tools.invoke(messages)
        return {
            "messages": [response],
        }

    def worker_router(self, state: State) -> str:
        if "messages" not in state or not state["messages"]:
            return "evaluator"
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
        
        if "messages" not in state or not state["messages"]:
            return {
                **state,
                "feedback_on_work": "No messages to evaluate.",
                "success_criteria_met": False,
                "user_input_needed": True,
            }
        last_response = state["messages"][-1].content if hasattr(state["messages"][-1], "content") else str(state["messages"][-1])
        system_message = """You are an evaluator that determines if a task has been completed successfully by an Assistant.\nAssess the Assistant's last response based on the given criteria. Respond with your feedback, and with your decision on whether the success criteria have been met,\nand whether more input is needed from the user."""
        user_message = f"""You are evaluating a conversation between the User and Assistant. You decide what action to take based on the last response from the Assistant.\n\nThe entire conversation with the assistant, with the user's original request and all replies, is:\n{self.format_conversation(state['messages'])}\n\nThe success criteria for this assignment is:\n{state['success_criteria']}\n\nAnd the final response from the Assistant that you are evaluating is:\n{last_response}\n\nRespond with your feedback, and decide if the success criteria is met by this response.\nAlso, decide if more user input is required, either because the assistant has a question, needs clarification, or seems to be stuck and unable to answer without help.\n\nThe Assistant has access to a tool to write files. If the Assistant says they have written a file, then you can assume they have done so.\nOverall you should give the Assistant the benefit of the doubt if they say they've done something. But you should reject if you feel that more work should go into this.\n\n"""
        if state.get("feedback_on_work"):
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

    def route_based_on_evaluation(self, state: State) -> str:
        if state.get("success_criteria_met") or state.get("user_input_needed"):
            return "END"
        else:
            return "worker"

    async def build_graph(self):
        graph_builder = StateGraph(State)
        graph_builder.add_node("planner", self.planner)
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)
        graph_builder.add_edge("planner", "worker")
        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
        )
        graph_builder.add_edge(START, "planner")
        self.graph = graph_builder.compile(checkpointer=None)

    async def run_superstep(self, message, success_criteria, history, clarifying_answers=None):
        config = {"configurable": {"thread_id": self.sidekick_id}}
        state = {
            "messages": message,
            "success_criteria": success_criteria or "The answer should be clear and accurate",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "clarifying_questions": None,
            "clarifying_answers": clarifying_answers or [],
            "clarifying_step": 0,
        }
        
        self.memory.save(self.sidekick_id, "state", self.serialize_state(state))
        result = await self.graph.ainvoke(state, config=config)
        self.memory.save(self.sidekick_id, "state", self.serialize_state(result))
        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-2].content if len(result["messages"]) > 1 and hasattr(result["messages"][-2], 'content') else ""}
        feedback = {"role": "assistant", "content": result["messages"][-1].content if result["messages"] and hasattr(result["messages"][-1], 'content') else ""}
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