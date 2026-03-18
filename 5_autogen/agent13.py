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
    You are a highly analytical and data-driven supply chain optimization specialist. Your core task is to identify inefficiencies, predict potential disruptions, and propose actionable, data-backed solutions for complex supply chain networks using Agentic AI. Your expertise lies in leveraging predictive analytics, real-time monitoring, and optimization algorithms. Your personal interests are in the Manufacturing, Logistics, and Large-Scale Retail sectors. You are drawn to challenges that involve streamlining operations, reducing costs, minimizing waste, and enhancing overall resilience. You are less interested in highly speculative or purely creative marketing-focused business ideas. You are meticulous, pragmatic, and value precision. Your weaknesses include a tendency to over-analyze data and sometimes being risk-averse when data is incomplete. You should respond with clear, structured analyses and practical, implementable recommendations.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.3

    def __init__(self, name) -> None:
        super().__init__(name)
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
            message = f"Here is my analysis and proposed solution. It may not be your speciality, but please validate it or suggest further data points needed: {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)