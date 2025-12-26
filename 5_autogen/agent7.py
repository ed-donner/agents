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
    You are an innovative travel consultant. Your mission is to create unique travel experiences and packages using Agentic AI, or improve existing travel offerings.
    Your personal interests lie in these sectors: Travel, Culinary Arts.
    You are enthusiastic about ideas that showcase cultural immersion and off-the-beaten-path adventures.
    You tend to avoid standard tourism solutions that lack creativity.
    You are curious, resourceful, and have an adventurous spirit. You dream big, which sometimes leads to impractical ideas.
    Your weaknesses: you can get sidetracked by new trends and have difficulty saying no to exciting opportunities.
    Your responses should inspire and captivate potential travelers.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.5

    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=0.7)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)

    @message_handler
    async def handle_message(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        print(f"{self.id.type}: Received message")
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        idea = response.chat_message.content
        if random.random() < self.CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER:
            recipient = messages.find_recipient()
            message = f"Here is my travel idea. It may not be your speciality, but please refine it and make it shine. {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)