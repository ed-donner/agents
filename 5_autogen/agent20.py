from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import messages
import random
from dotenv import load_dotenv
import os
from autogen_core.models import ModelInfo

load_dotenv(override=True)

class Agent(RoutedAgent):

    system_message = """
    You are a meticulous Supply Chain Efficiency Expert. Your primary task is to analyze existing logistical operations,
    identify inefficiencies, and propose optimization solutions, especially those involving advanced AI and automation.
    Your personal interests are in these sectors: Logistics, Manufacturing, Retail Operations.
    You are drawn to ideas that promise tangible cost savings, improved delivery metrics, and enhanced operational resilience.
    You are less interested in speculative or unproven concepts; you prefer data-backed, practical implementations.
    You are analytical, detail-oriented, and methodical. You excel at dissecting complex systems into manageable components.
    Your weaknesses: you can sometimes get lost in minor details, potentially overlooking broader, more disruptive innovations.
    You should respond with well-structured, actionable recommendations, often supported by quantitative reasoning.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.5

    def __init__(self, name) -> None:
        super().__init__(name)
        #model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=0.7)
        model_client = OpenAIChatCompletionClient(
            model="gemini-2.5-flash",
            api_key=os.environ["GOOGLE_API_KEY"],
            base_url="https://generativelanguage.googleapis.com/v1beta/openai",
            model_info=ModelInfo(
            vision=True, 
            function_calling=True,
            json_output=True, 
            family="gemini-2.5", 
            structured_output=True
            )
        )   
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)

    @message_handler
    async def handle_message(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        print(f"{self.id.type}: Received message")
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        idea = response.chat_message.content
        if random.random() < self.CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER:
            recipient = messages.find_recipient()
            message = f"Here is my business idea. It may not be your speciality, but please refine it and make it better. {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)