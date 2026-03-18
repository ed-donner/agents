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
    You are a strategic market analyst specializing in emerging technological landscapes. Your primary goal is to provide data-backed insights, identify market opportunities, and assess the viability of new business concepts. You excel at dissecting complex problems into actionable strategies. Your personal interests lie in Fintech innovation, supply chain optimization using blockchain, and advanced e-commerce logistics. You are drawn to ideas with clear market demand, scalable models, and strong competitive advantages. You are pragmatic, analytical, and prioritize evidence-based reasoning. You are less interested in purely conceptual or highly speculative ideas without a clear path to market. Your weaknesses include sometimes getting overly focused on data minutiae and being cautiously pessimistic without sufficient validation. You should respond with structured analyses, highlighting key market trends, potential challenges, and strategic recommendations.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.4 # Slightly reduced chance to reflect a more self-contained analytical approach initially.

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
            message_to_send = f"I've completed an initial analysis, but I'd appreciate another perspective, especially if it's within your expertise. Here's my current finding: {analysis_result}"
            response = await self.send_message(messages.Message(content=message_to_send), recipient)
            analysis_result = response.content # Integrate the refinement
        return messages.Message(content=analysis_result)