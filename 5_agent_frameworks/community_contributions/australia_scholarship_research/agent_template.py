"""
Template for agents created by the Creator. Do not edit by hand.
Placeholders: _GeneratedAgent (-> CLASS_NAME), {{SYSTEM_MESSAGE}}
Creator substitutes these when generating the Researcher and Evaluator agents.
"""

from typing import List, Any
from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

from . import messages


SYSTEM_MESSAGE = '''{{SYSTEM_MESSAGE}}'''


class _GeneratedAgent(RoutedAgent):
    def __init__(self, name: str, tools: List[Any] | None = None) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=0.3)
        self._tools = tools or []
        self._delegate = AssistantAgent(
            name,
            model_client=model_client,
            system_message=SYSTEM_MESSAGE,
            tools=self._tools,
            reflect_on_tool_use=True,
        )

    @message_handler
    async def handle_message(
        self, message: messages.Message, ctx: MessageContext
    ) -> messages.Message:
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages(
            [text_message], ctx.cancellation_token
        )
        return messages.Message(content=response.chat_message.content)
