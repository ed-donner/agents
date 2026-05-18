from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage

import messages
from model_client import build_openrouter_client


SYSTEM_MESSAGE = """Analyze the target market to identify customer pain points, timing dynamics, current alternatives, and whitespace opportunities. Transform ambiguous problems into clear, actionable market insights that can inform strategic decisions. Prioritize data-driven conclusions and ensure recommendations are specific, relevant, and geared towards maximizing market potential."""


class ResearcherAgent(RoutedAgent):
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
