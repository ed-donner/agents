"""
Template for Creator: a Core RoutedAgent whose brain is an AgentChat AssistantAgent.
The Creator LLM rewrites this file (especially system_message) per module basename.
"""

from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import messages
import random
from dotenv import load_dotenv

load_dotenv(override=True)


class Agent(RoutedAgent):
    system_message = """
    You are part of a team inventing a commercial business idea aimed at the AI agents industry
    (products or services for teams that build, deploy, or operate autonomous agents).
    Be concrete: name a customer, a wedge, and how you monetize. Keep replies concise.
    """

    CHANCES_PEER_ROUND = 0.65

    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=0.75)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)

    @message_handler
    async def handle_message(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        print(f"{self.id.type}: received: {message.content[:100]!r}...")
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        idea = response.chat_message.content
        if random.random() < self.CHANCES_PEER_ROUND:
            peer = messages.random_peer_excluding(self.id.type)
            print(f"{self.id.type}: messaging peer by name -> {peer.type}")
            forward = (
                f"Your teammate ({self.id.type}) asks you to refine or challenge this, still targeting "
                f"a commercial opportunity in the AI agents space: {idea}"
            )
            peer_reply = await self.send_message(messages.Message(content=forward), peer)
            idea = f"{idea}\n\n— Refinement from {peer.type} —\n{peer_reply.content}"
        return messages.Message(content=idea)
