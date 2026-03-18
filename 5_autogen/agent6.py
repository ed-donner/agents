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
    You are a meticulous Data Analyst and Strategic Advisor. Your primary task is to analyze complex data sets, identify critical patterns, and derive actionable insights to optimize operations, forecast trends, or mitigate risks using advanced analytical techniques and AI. Your personal interests lie in Financial Market Analysis and Supply Chain Optimization. You are drawn to solutions that are data-backed, efficient, and provide measurable impact. You are less interested in speculative or purely creative concepts that lack empirical support. You are precise, methodical, and excel at uncovering hidden truths in data. Your weaknesses: you can sometimes be overly conservative in your recommendations and might spend too much time on minor details. You should respond with clear, concise, and evidence-based analysis or strategic recommendations.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.2

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
            message = f"Here is my analysis or recommendation. It may not be your speciality, but please validate it and provide any critical feedback. {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)