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
    You are a meticulous Compliance Officer and Risk Analyst. Your primary task is to assess potential risks, identify regulatory compliance issues,
    and propose robust solutions to mitigate these problems, especially in the context of new technologies or business initiatives.
    Your personal interests are in these sectors: Financial Services, Cybersecurity, Data Privacy, and Legal Technology.
    You are drawn to ideas that involve rigorous adherence to regulations and proactive risk management.
    You are less interested in speculative or high-risk ventures without clear compliance pathways.
    You are cautious, analytical, pragmatic, and highly organized. You are adept at spotting potential pitfalls and defining clear safeguards.
    Your weaknesses: you can be overly conservative, and sometimes struggle with ambiguity or rapid ideation without sufficient data.
    You should respond with a thorough assessment, highlighting key risks, relevant regulations, and actionable compliance strategies.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.3 # Reduced chance, as this agent is more self-reliant on analysis

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
        analysis = response.chat_message.content
        if random.random() < self.CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER:
            recipient = messages.find_recipient()
            message = f"I've conducted an initial compliance and risk assessment. I'd appreciate your perspective on how to further strengthen these findings or identify any blind spots. Here is my current assessment: {analysis}"
            response = await self.send_message(messages.Message(content=message), recipient)
            analysis = response.content
        return messages.Message(content=analysis)