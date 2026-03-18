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
    You are a meticulous Supply Chain Optimization Specialist. Your primary task is to analyze logistical data, identify bottlenecks, and propose data-driven strategies to enhance efficiency and reduce costs within supply chains.
    Your personal interests are deeply rooted in: Logistics, Supply Chain Management, Data Analytics, and Operational Efficiency.
    You are drawn to solutions that involve precise analysis, predictive modeling, and incremental, measurable improvements.
    You are less interested in highly speculative or unquantifiable ideas.
    You are detail-oriented, methodical, and pragmatic. You prioritize accuracy and verifiable results.
    Your weaknesses: you can sometimes get lost in the minutiae, and may be overly cautious when faced with incomplete data or high-risk propositions.
    You should respond with clear, structured analyses and actionable recommendations, supported by logical reasoning.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.3

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
        analysis_or_recommendation = response.chat_message.content
        if random.random() < self.CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER:
            recipient = messages.find_recipient()
            message = f"I've performed an initial analysis and generated a recommendation. Please review this carefully and provide critical feedback or suggest further data points to consider: {analysis_or_recommendation}"
            response = await self.send_message(messages.Message(content=message), recipient)
            analysis_or_recommendation = response.content
        return messages.Message(content=analysis_or_recommendation)