from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import List, Any, Optional, Dict
from pydantic import BaseModel, Field
import uuid
import asyncio
from langchain_core.messages import ToolMessage
from pharmacy_tools import check_drug_allergy, check_drug_interaction,  calculate_daily_dose,check_duplicate_therapy,check_geriatric_considerations,check_pediatric_dosing,check_renal_dosing,check_pregnancy_safety,check_drug_recall,check_multi_drug_interactions,check_therapeutic_duplication,get_controlled_substance_info
load_dotenv(override=True)


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    iteration_count: int


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the pharmacist, or clarifications, or the assistant is stuck"
    )



DEFAULT_SUCCESS_CRITERIA = """
1. All relevant clinical checks completed (allergies, interactions, dosing)
2. Clear decision provided: "Dispense" or "Do Not Dispense"
3. Clinical reasoning documented
4. Specific recommendations given to pharmacist
"""

def final_clinical_assessment(decision: str, reasoning: str, recommendations: List[str], user_input_needed: bool = False) -> str:
    """
    Submit the final clinical assessment.
    
    Args:
        decision: "Dispense" or "Do Not Dispense"
        reasoning: Clinical reasoning for the decision
        recommendations: Recommendations for the pharmacist
        user_input_needed: True if more input is needed (default: False)
    """
    return f"Assessment Recorded:\nDecision: {decision}\nReasoning: {reasoning}\nRecommendations: {', '.join(recommendations)}\nUser Input Needed: {user_input_needed}"


class Sidekick:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools = None
        self.llm_with_tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()

    async def setup(self):
        # Add output structure pydantic class as tool
        self.tools = [check_drug_allergy, check_drug_interaction,  calculate_daily_dose,check_duplicate_therapy,check_geriatric_considerations,check_pediatric_dosing,check_renal_dosing,check_pregnancy_safety,check_drug_recall, final_clinical_assessment]
        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        evaluator_llm = ChatOpenAI(model="gpt-4o-mini")
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        await self.build_graph()

    # The worker node

    def worker(self, state: State) -> Dict[str, Any]:
        system_message = f"""You are an expert Pharmacy Sidekick assistant. Your role is to validate prescriptions and ensure patient safety by rigorously checking for allergies, interactions, and dosing errors.

You have access to specialized pharmacy verification tools. You MUST use these tools to investigate the case before forming a conclusion.
If you notice absence of needed information, ask a clarifying question.
For example, if you need the patient's weight in kg for pediatric dosing, ask a question like: "Question: The patient's weight in kg is missing but required for pediatric dosing. Please provide the weight."
if you need name of medicine : "Question: The name of the medicine is missing but required for pediatric dosing. Please provide the name."
Always check patient age before calling tools like check_geriatric_considerations or check_pediatric_dosing.
Success Criteria:
{state['success_criteria']}

Tool call rules — be extremely selective — only call a tool when you are 100% certain it is necessary right now:

Tool call rules:
• ALWAYS call check_drug_allergy FIRST if allergies are provided
• ONLY call check_pediatric_dosing if age < 18 AND weight is known
• ONLY call check_geriatric_considerations if age >= 65
• ONLY call check_renal_dosing if CrCl or "renal impairment" is explicitly stated
• ONLY call check_pregnancy_safety if "pregnant" or "pregnancy" appears in patient info
• For interactions/duplicates: call check_multi_drug_interactions or check_therapeutic_duplication INSTEAD of single check_drug_interaction / check_duplicate_therapy
• NEVER call more than 3 tools in one turn unless patient has >5 drugs
• If unsure whether a tool is needed → ASK the pharmacist instead of calling it

    
WORKFLOW:
1. Use available tools to gather all necessary clinical information
2. If you need information from the pharmacist, ask a clear question starting with 'Question:'
3. When you have all information and have completed verification, you MUST call the final_clinical_assessment tool with your decision

Response Guidelines:
- For clarification questions: Start with 'Question:' followed by what you need
  Example: "Question: The patient's weight in kg is missing but required for pediatric dosing. Please provide the weight."

- For final assessment: You MUST use the final_clinical_assessment tool (not plain text) with:
  * decision: "Dispense" or "Do Not Dispense"
  * reasoning: Complete clinical reasoning
  * recommendations: List of specific recommendations
  * user_input_needed: Set to False when complete or True if more information is needed
"""
            
        # Add in the system message

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

    def worker_controller(self, state: State) -> str:
        last_message = state["messages"][-1]
    
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        else:
            return "evaluator" 

    def tools_controller(self, state: State) -> str:
        messages = state["messages"]
        last_message = messages[-1]
        
        if isinstance(last_message, ToolMessage):
             if last_message.name == "final_clinical_assessment":
                 return "evaluator"
        
        return "worker"

    def format_conversation(self, messages: List[Any]) -> str:
        conversation = []
        for i, message in enumerate(messages):
            if isinstance(message, SystemMessage):
                continue  
            elif isinstance(message, HumanMessage):
                conversation.append(f"Pharmacist: {message.content}")
            elif isinstance(message, AIMessage):
                # Show tool usage more clearly
                if hasattr(message, "tool_calls") and message.tool_calls:
                    tools_used = [tc.get("name", "unknown") for tc in message.tool_calls]
                    conversation.append(f"Assistant: [Used tools: {', '.join(tools_used)}]")
                if message.content:
                    conversation.append(f"Assistant: {message.content}")
            elif isinstance(message, ToolMessage):
                conversation.append(f"Tool Output: {message.content}")
        
        return "\n\n".join(conversation)

    def evaluator(self, state: State) -> State:
        last_response = state["messages"][-1].content

        system_message = f"""You are a Clinical Supervisor evaluating a Pharmacy Assistant agent's prescription validation work.

            Your role: Determine if the task has been completed thoroughly, safely, and with proper clinical reasoning.

            EVALUATION CRITERIA:

            1. **Completeness of Investigation**
            - Did the assistant use appropriate tools for the patient's profile?
            - For pediatric patients: check_pediatric_dosing
            - For geriatric patients (65+): check_geriatric_considerations
            - For patients with renal issues: check_renal_dosing
            - For pregnant patients: check_pregnancy_safety
            - Always check: allergies, interactions, duplicate therapy, recalls (when applicable)

            2. **Clinical Safety**
            - Were all critical checks performed based on patient demographics?
            - Don't penalize for NOT using tools that aren't relevant (e.g., geriatric checks for a 30-year-old)
            - DO penalize for missing relevant checks (e.g., not checking allergies at all)

            3. **Clear Outcome**
            - Did the assistant provide a definitive recommendation using final_clinical_assessment tool?
            - OR did they ask a legitimate clarifying question?

            4. **User Input Assessment**
            - Set user_input_needed=True if:
                * Assistant asked a valid Question: that requires pharmacist input
                * Assistant is stuck or repeating mistakes
                * Critical information is missing and assistant recognized this
            - Set user_input_needed=False if:
                * Assistant provided final assessment
                * Question is not actually necessary (info can be inferred or defaulted)

            Success Criteria: {state['success_criteria']}

            Provide constructive feedback that helps the assistant improve without being overly harsh."""

        user_message = f"""Evaluate this conversation between Pharmacist and Assistant:

            {self.format_conversation(state['messages'])}

            Success Criteria:
            {state['success_criteria']}

            Assistant's Latest Response:
            {last_response}

            {f"Previous Feedback (watch for repeated mistakes): {state['feedback_on_work']}" if state["feedback_on_work"] else ""}

            Provide:
            1. feedback: Specific, actionable feedback
            2. success_criteria_met: True only if truly complete and safe
            3. user_input_needed: True if legitimate question or stuck
            """
        if state["feedback_on_work"]:
            user_message += f"Also, note that in a prior attempt from the Assistant, you provided this feedback: {state['feedback_on_work']}\n"
            user_message += "If you're seeing the Assistant repeating the same mistakes, then consider responding that user input is required."
        
        evaluator_messages = [SystemMessage(content=system_message), HumanMessage(content=user_message)]

        eval_resp = self.evaluator_llm_with_output.invoke(evaluator_messages)

        new_state = {
            "messages": [{"role": "assistant", "content": f"Evaluator Feedback on this answer: {eval_resp.feedback}"}],
            "feedback_on_work": eval_resp.feedback,
            "success_criteria_met": eval_resp.success_criteria_met,
            "user_input_needed": eval_resp.user_input_needed,
            "iteration_count": state.get("iteration_count", 0) + 1

        }

        return new_state

    def evaluator_controller(self, state: State) -> str:
        max_iterations = 5
        if state.get("iteration_count", 0) >= max_iterations:
            return "END"
    
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        else:
            return "worker"


    async def build_graph(self):
        # Set up Graph Builder with State
        graph_builder = StateGraph(State)

        # Add nodes
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        # Add edges
        graph_builder.add_conditional_edges(
            "worker", self.worker_controller, {"tools": "tools", "evaluator": "evaluator"}
        )
        graph_builder.add_conditional_edges(
            "tools", self.tools_controller, {"evaluator": "evaluator", "worker": "worker"}
        )
        graph_builder.add_conditional_edges(
            "evaluator", self.evaluator_controller, {"worker": "worker", "END": END}
        )
        graph_builder.add_edge(START, "worker")

        # Compile the graph
        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message: str, success_criteria: str, history: list):
        if self.graph is None:
            await self.setup()

        config = {"configurable": {"thread_id": self.sidekick_id}}

        # Convert history (list of dicts) to LangChain messages
        messages = []
        for entry in history:
            if entry.get("role") == "user":
                messages.append(HumanMessage(content=entry["content"]))
            elif entry.get("role") == "assistant":
                messages.append(AIMessage(content=entry["content"]))

        # Add new user message
        if message:
            messages.append(HumanMessage(content=message))

        state = {
            "messages": messages,
            "success_criteria": success_criteria or DEFAULT_SUCCESS_CRITERIA,
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "iteration_count": 0
        }

        result = await self.graph.ainvoke(state, config=config)

        # Rebuild history
        user_entry = {"role": "user", "content": message}
        reply_entry = {"role": "assistant", "content": result["messages"][-2].content if len(result["messages"]) >= 2 else ""}
        feedback_entry = {"role": "assistant", "content": result["messages"][-1].content}

        return history + [user_entry, reply_entry, feedback_entry], self

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
