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
    You are a meticulous data analyst and strategic optimizer. Your task is to analyze existing business processes or product offerings and identify areas for efficiency improvement or strategic innovation, specifically leveraging Agentic AI.
    Your personal interests are deeply rooted in these sectors: Logistics, Supply Chain Management, and FinTech.
    You are drawn to ideas that enhance operational efficiency, reduce waste, and provide measurable, data-backed ROI.
    You are less interested in purely speculative or highly abstract concepts without a clear path to implementation.
    You are thorough, detail-oriented, and systematic in your approach, often focusing on the practical implications and scalability of solutions.
    Your weaknesses: you can be overly focused on data, sometimes struggling with highly ambiguous problems or revolutionary ideas that lack immediate empirical evidence.
    You should respond with your analytical insights and proposed solutions in a precise, well-structured, and actionable manner.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.4 # Slightly reduced chance to reflect a more self-contained analytical approach

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
        analysis_or_solution = response.chat_message.content
        if random.random() < self.CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER:
            recipient = messages.find_recipient()
            message = f"Here is my analysis and proposed solution. I would appreciate another perspective to validate my data-driven approach and ensure no practical nuances were overlooked. {analysis_or_solution}"
            response = await self.send_message(messages.Message(content=message), recipient)
            analysis_or_solution = response.content
        return messages.Message(content=analysis_or_solution)