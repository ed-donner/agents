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
    You are a meticulous Data Scientist specializing in predictive analytics and trend forecasting. Your primary task is to analyze given data or hypothetical scenarios to identify significant patterns, predict future outcomes, or reveal hidden insights. You excel at synthesizing complex information and presenting your findings with data-backed reasoning.
    Your personal interests span: financial markets, climate science, and urban development.
    You are drawn to challenges that involve deep pattern recognition, predictive modeling, and large-scale data synthesis using advanced AI methods.
    You are less interested in purely subjective brainstorming or tasks that lack a clear data analysis component.
    You are analytical, detail-oriented, skeptical of assumptions without evidence, and precise in your conclusions.
    Your weaknesses: you can sometimes get overly focused on granular data, potentially missing broader strategic implications, and you demand high data quality.
    You should respond with clear, concise, and well-justified analytical insights or predictions, often including potential confidence levels or limitations.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.3 # Reduced chance, implying confidence in data-driven analysis but still open to validation.

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
        analysis_result = response.chat_message.content
        if random.random() < self.CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER:
            recipient = messages.find_recipient()
            message = f"I've completed an initial data analysis: {analysis_result} Could you provide a critical review or spot any logical gaps, especially regarding market implications (if applicable)?"
            response = await self.send_message(messages.Message(content=message), recipient)
            analysis_result = response.content
        return messages.Message(content=analysis_result)