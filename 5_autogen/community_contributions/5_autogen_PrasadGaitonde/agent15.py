from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import messages
import random
from dotenv import load_dotenv

load_dotenv(override=True)

class Agent(RoutedAgent):

    DEFAULT_SYSTEM_MESSAGE = """
    You are a consulting entrepreneur who believes in first principles thinking. Your strengths are creative problem-solving and technical depth. You avoid feature creep.
    Your task is to come up with a new business idea using Agentic AI, or refine an existing idea.
    Respond with your business ideas in an engaging and clear way that reflects your persona.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.5

    def __init__(self, name, persona=None, seed=None) -> None:
        super().__init__(name)
        self.persona = persona or self.DEFAULT_SYSTEM_MESSAGE
        self.seed = seed
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=0.7)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.persona)
        self.idea_lineage = []

    @message_handler
    async def handle_message(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        print(f"{self.id.type}: Received message")
        
        content = message.content
        text_message = TextMessage(content=str(content), source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        idea = response.chat_message.content
        
        # Track lineage
        self.idea_lineage = [self.id.type]
        
        if random.random() < self.CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER:
            recipient = messages.find_recipient()
            message_text = f"Here is my business idea. It may not be your speciality, but please refine it and make it better. {idea}"
            response = await self.send_message(messages.Message(content=message_text), recipient)
            idea = response.content
        
        return messages.Message(content=idea)