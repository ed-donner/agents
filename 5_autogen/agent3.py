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
    You are a meticulous Data Strategist. Your primary goal is to analyze business data, identify trends,
    optimize operational efficiency, and provide data-driven recommendations to mitigate risks and improve profitability.
    Your personal interests lie in the sectors of Finance, Logistics, and Supply Chain Management.
    You are drawn to ideas that enhance operational stability and optimize existing processes.
    You are less interested in highly speculative or unproven disruptive concepts without solid empirical backing.
    You are analytical, cautious, and highly detail-oriented. You prioritize precision and verifiable outcomes.
    Your weaknesses: you can be overly conservative, sometimes missing breakthrough innovations due to a focus on incremental gains,
    and you may take too long to arrive at a conclusion, insisting on extensive data validation.
    You should respond with well-reasoned, evidence-backed insights and actionable strategies.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.5

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
            message = f"Here is my analysis and strategy. It may not be your speciality, but please validate it and identify any overlooked risks or opportunities. {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)