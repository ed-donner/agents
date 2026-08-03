"""
Agents for our AI Sidekick.
"""

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import List, Any

from .tools import Tools
from .state.state import State
from .prompts import WORKER_PROMPT, EVALUATOR_PROMPT

load_dotenv(override=True)

class Nodes:
    def __init__(self):
        self.tools_object = Tools()
        self.tools = None
        self.llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.model = "gpt-4o-mini"
        self.llm = ChatOpenAI(model=self.model)
    
    def worker_node(self, state: State):
        """
        Main worker node executing user's query.
        """
        # define system prompt + messages.
        system_prompt = WORKER_PROMPT.format(
            success_criteria=state.success_criteria,
            criteria_met=state.success_criteria_met,
            feedback=state.feedback_on_work or "",
        )
        messages = SystemMessage(system_prompt) + state.messages

        # invoke LLM.
        try:
            response = self.llm_with_tools.invoke(messages)
            return {
                "messages" : [response]
            }
        except Exception as e:
            return {
                "messages": [AIMessage(content=f"Error: {str(e)}")]
            }

    def evaluator_node(self, state: State):
        """
        Evaluator output node.
        """
        # define system prompt + messages.
        system_prompt = EVALUATOR_PROMPT.format(
            success_criteria=state.success_criteria,
            conversation_history=Nodes()._format_conversation(state.messages),
            last_response=state.messages[-1].content,
            prior_feedback_clause=state.feedback_on_work or ""
        )
        messages = SystemMessage(system_prompt) + state.messages

        # invoke LLM.
        try:
            response = self.evaluator_llm_with_output.invoke(messages)
            return {
                "messages": [
                    {
                        "role": "assistant",
                        "content": f"Evaluator Feedback on this answer: {response.feedback}",
                    }
                ],
                "feedback_on_work": response.feedback,
                "success_criteria_met": response.success_criteria_met,
                "user_input_needed": response.user_input_needed,
            }
        except Exception as e:
            return {
                "messages": [AIMessage(content=f"Evaluator error: {str(e)}")]
            }

    @staticmethod
    def _format_conversation(messages: List[Any]) -> str:
        """
        Format conversation suitable for LLM.
        """
        conversation = "Conversation history:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Tools use]"
                conversation += f"Assistant: {text}\n"
        return conversation