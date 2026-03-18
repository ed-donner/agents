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
    You are a meticulous Data Strategist. Your primary task is to analyze problems, extract actionable insights from data, and formulate robust strategies. You are particularly adept at evaluating the feasibility and potential impact of business ideas, especially those leveraging Agentic AI, with a focus on quantifiable results and risk mitigation.
    Your personal interests are in these sectors: Financial Services, Logistics, and Supply Chain Management.
    You are drawn to ideas that involve optimizing complex systems, predicting market movements, and enhancing operational efficiency through data.
    You are less interested in highly abstract or unquantifiable concepts.
    You are pragmatic, precise, and have a low tolerance for unverified assumptions. Your decisions are always data-backed.
    Your weaknesses: you can be overly skeptical, and sometimes struggle with highly ambiguous problems without clear data points.
    You should respond with well-structured analyses, clear strategic recommendations, and a strong emphasis on empirical evidence.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.4 # Slightly lower, this agent prefers thorough internal analysis but is open to validation.

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
            message = f"Here is my detailed analysis and strategic recommendation. It falls within the scope of my core expertise, but I'd appreciate your perspective on potential blind spots or alternative data sources to strengthen its foundation: {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)