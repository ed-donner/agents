from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv
from typing import List, Any, Optional, Dict, Literal
from pydantic import BaseModel, Field
from sidekick_tools import playwright_tools, all_tools
import uuid
import asyncio

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


load_dotenv(override=True)


# Outputs
class EvaluatorOutput(BaseModel):
    feedback: str = Field(description='Feedback on assistants reponse')
    success_criteria_met: bool = Field(description='Whether the criteria have been met.')
    user_input_needed: bool = Field(
        description='True if more input is needed from the user, or clarification, or assistant is stuck, or user input is incomplete'
        )

class EventOutput(BaseModel):
    country: str
    city: str
    date: str = Field(..., description='Date must be given, e.g. 2026-10-13')
    vibe: str
    why_recommended: str = Field(description="Short reason why this event is recommended")
    approx_cost: str = Field(description='Calculated costs')


# Inputs
class EventPlannerInput(BaseModel):
    country: str
    city: str
    date: str = Field(..., description='Date must be given, e.g. 2026-10-13')
    vibe: str = Field(description='User defines what kind of vibe he/she looking for, e.g. House, Techno ...')
    budget: Optional[int] = Field(description='Max budget')


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    event_input: Optional[EventPlannerInput]



# Sidekick 
class Sidekick:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools = None
        self.worker_llm_with_tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None
        self.intake_llm_with_input = None

    async def setup(self):
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await all_tools()
        
        intake_llm = ChatOpenAI(model='gpt-4o-mini')
        self.intake_llm_with_input = intake_llm.with_structured_output(EventPlannerInput)
        
        worker_llm = ChatOpenAI(model='gpt-4o-mini')
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        
        evaluator_llm = ChatOpenAI(model='gpt-4o-mini')
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        
        await self.build_graph()

    def get_last_user_text(self, state: State) -> str:
        """Helper to get the user's last message text."""
        last_text = state["messages"][-1]

        if isinstance(last_text, HumanMessage):
            return last_text.content

        if isinstance(last_text, dict) and "content" in last_text:
            return str(last_text["content"])


        return str(last_text)

    
    def intake(self, state: State) -> Dict[str, Any]:
        """
        Extract required input fields from the user's message using structured output.
        If anything essential is missing, ask a targeted question and stop.
        Otherwise store parsed input in state['event_input'] and proceed.
        """ 

        user_text = self.get_last_user_text(state)

        extracted: EventPlannerInput = self.intake_llm_with_input.invoke(
            [
                SystemMessage(
                    content=(
                        "Extract the event planning inputs from the user's message. "
                        "Do not invent missing information. If a required field is missing, ask the user for it"
                    )
                ),
                HumanMessage(content=user_text),
            ]
        )

        missing = []
        
        if not getattr(extracted, "country", None):
            missing.append("country")
        if not getattr(extracted, "city", None):
            missing.append("city")
        if not getattr(extracted, "date", None):
            missing.append("date (YYYY-MM-DD)")
        if not getattr(extracted, "vibe", None):
            missing.append("vibe (e.g. techno/house/hiphop/...)")

        if missing:
            question = (
                "Question: I’m missing the following required info to start: "
                + ", ".join(missing)
                + ". Please provide it."
            )
            return {
                "user_input_needed": True,
                "messages": [AIMessage(content=question)],
                "event_input": None,
            }

        return {
            "user_input_needed": False,
            "event_input": extracted,
        }

    def intake_router(self, state: State) -> str:
        """Route after intake: either stop (need user input) or continue to worker.""" 
        return "END" if state.get("user_input_needed") else "worker"

        

    def worker(self, state: State) -> Dict[str, Any]:
        system_message = f""" Your are a helpful event planner assistant that can use tools to complete tasks.
        You keep working on a task until either you have a question or need clarification from the user, 
        or the user input is incomplete. You have tools to browse the internet for the events, navigating and 
        retrieving web pages.
        

        This is the success criteria:
        {state["success_criteria"]}
        
        You should use the structured event input in {state['event_input']}.
        You should reply either with a question for the user about this assignement, or with the final response.
        If you have any question or you miss some user input, you need to reply by clearly stating your question. 
        An example might be:
        
        Question: Please provide the missing city.

        If you've finished, reply with the final answer, don't ask a question; simply reply with the answer.
        """

        if state.get('feedback_on_work'):
            system_message += f"""
            Previously you thought you completed the task, but your reply was rejected beacause the success criteria was not met.
            Here is the feedback on why this was rejected:
            {state['feedback_on_work']}
            With this feedback, please continue the assignment, ensuring that you meet success criteria or have a specific question for the user.#
            """

        found_system_message = False
        messages = state['messages']
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.worker_llm_with_tools.invoke(messages)

        return {
            'messages': [response],
        }

    def worker_router(self, state: State) -> str:
        last_message = state['messages'][-1]

        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return 'tools'

        else:
            return 'evaluator'

    def format_conversation(self, messages: List[Any]) -> str:
        conversation = 'Conversation history: \n\n'
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f'User: {message.content}\n'
            elif isinstance(message, AIMessage):
                text = message.content or '[Tool use]'
                conversation += f'Assistant: {text}\n'

        return conversation

    def evaluator(self, state: State) -> State:
        last_response = state['messages'][-1].content

        system_message = """ You are an evaluator that determines if a a task has been completed sucessfully.
        Assess the Assistant's last responce based on the given criteria- Respond with your feedback, and with your decision on whether the success criteria has been met,
    and whether more input is needed from the user.
    """

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


    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        else:
            return "worker"


    async def build_graph(self):
        graph_builder = StateGraph(State)

        graph_builder.add_node('intake', self.intake)
        graph_builder.add_node('worker', self.worker)
        graph_builder.add_node('tools', ToolNode(tools=self.tools))
        graph_builder.add_node('evaluator', self.evaluator)

        graph_builder.add_conditional_edges(
            'worker', self.worker_router, {'tools': 'tools', 'evaluator': 'evaluator'}
        )
        graph_builder.add_edge("tools", "worker")
        #graph_builder.add_edge('intake', 'worker')
        
        graph_builder.add_conditional_edges(
            'evaluator', self.route_based_on_evaluation, {'worker': 'worker', 'END': END}
            )
        graph_builder.add_edge(START, 'intake')
        graph_builder.add_conditional_edges(
            "intake", self.intake_router, {"worker": "worker", "END": END},
        )

        self.graph = graph_builder.compile(checkpointer=self.memory)


    async def run_superstep(self, message, success_criteria, history):
        config = {'configurable': {'thread_id': self.sidekick_id}}

        state = {
            'messages': message,
            'success_criteria': success_criteria,
            'feedback_on_work': None,
            'success_criteria_met': False,
            'user_input_needed': False,
            "event_input": None,
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
                # If no loop is running, do a direct run
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())