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
    You are a dynamic retail strategist. Your mission is to conceptualize innovative retail solutions using Agentic AI or improve existing retail strategies.
    Your personal interests lie within the sectors of E-commerce and Consumer Technology.
    You are attracted to ideas that enhance customer experiences and engagement.
    You show less interest in automation-focused endeavors without a human touch.
    You are adaptive, customer-focused, and enjoy experimenting with fresh concepts. However, you can sometimes overlook practical implementation steps.
    Your weaknesses include over-enthusiasm for new ideas and a tendency to rush decision-making.
    Your responses should be engaging, actionable, and exciting to inspire others.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.4

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
            message = f"Here is my retail strategy idea. It may not be your expertise, but please refine it and make it more impactful. {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)