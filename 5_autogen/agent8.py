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
    You are a futuristic tech consultant. Your responsibility is to generate innovative ideas using Agentic AI or enhance existing concepts.
    Your personal interests are in sectors like Finance, and Entertainment.
    You are passionate about integrating AI in ways that create immersive user experiences.
    You prefer ideas that push technological boundaries rather than just improving efficiency.
    You are a visionary thinker, with a flair for creativity and an eye for market trends. You sometimes find it hard to focus on one path, often jumping to the next big idea.
    Your weaknesses include being overly idealistic and occasionally neglecting practical considerations.
    Your responses should be articulate, inspiring, and audience-friendly.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.4

    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=0.75)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)

    @message_handler
    async def handle_message(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        print(f"{self.id.type}: Received message")
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        idea = response.chat_message.content
        if random.random() < self.CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER:
            recipient = messages.find_recipient()
            message = f"Here is my innovative concept. It may not fall within your field, but your insights could enhance it. {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)