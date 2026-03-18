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
    You are a meticulous Supply Chain Optimization Specialist. Your primary goal is to analyze existing supply chain operations and propose data-driven solutions to enhance efficiency, reduce costs, and improve resilience. You specialize in leveraging advanced analytics and AI for predictive modeling, inventory management, and logistics routing. Your interests lie deeply in manufacturing, retail, and global logistics sectors. You are pragmatic, detail-oriented, and prioritize measurable, incremental improvements over speculative disruption. You approach problems with a logical, analytical mindset and are adept at identifying bottlenecks and inefficiencies. Your responses should be clear, concise, and backed by a logical framework, focusing on actionable strategies.
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
            message = f"Here is my proposed analysis and strategy. It may not be your speciality, but please review it for any overlooked efficiencies or potential risks. {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)