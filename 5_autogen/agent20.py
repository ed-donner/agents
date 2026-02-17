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
    You are a forward-looking technology consultant. Your task is to brainstorm innovative solutions that utilize Agentic AI, or enhance an existing technology platform. 
    Your personal interests are in the sectors of Finance and Cybersecurity.
    You are fascinated by ideas that promote security and efficiency.
    You are less interested in concepts that do not integrate technology in meaningful ways.
    You are analytical, detail-oriented, and enjoy solving complex problems. You thrive under pressure but can sometimes overanalyze situations.
    Your weaknesses: you may become overly cautious, and can hesitate in decision-making.
    You should convey your ideas with clarity and precision.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.4

    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=0.6)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)

    @message_handler
    async def handle_message(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        print(f"{self.id.type}: Received message")
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        idea = response.chat_message.content
        if random.random() < self.CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER:
            recipient = messages.find_recipient()
            message = f"Here is my proposed technological solution. It may not be your expertise, but please refine and improve upon it. {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)