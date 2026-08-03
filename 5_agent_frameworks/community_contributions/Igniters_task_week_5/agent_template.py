from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage

import messages
from model_client import build_openrouter_client


SYSTEM_MESSAGE = """{{SYSTEM_MESSAGE}}"""


class _GeneratedAgent(RoutedAgent):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._delegate = AssistantAgent(
            name=name,
            model_client=build_openrouter_client(temperature=0.4),
            system_message=SYSTEM_MESSAGE,
        )

    @message_handler
    async def handle_message(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        return messages.Message(content=str(response.chat_message.content))
