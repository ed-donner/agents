from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage

import messages
from model_client import build_openrouter_client


SYSTEM_MESSAGE = """Critically evaluate startup ideas by identifying execution and go-to-market risks. Challenge assumptions and surface potential pitfalls in the proposed concepts. Recommend sharper positioning strategies and suggest narrower MVPs that can mitigate risks while maximizing market fit. Focus on practical, actionable feedback that enhances the viability and competitiveness of the startup."""


class RiskCriticAgent(RoutedAgent):
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
