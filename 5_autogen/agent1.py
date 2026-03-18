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
    You are a data privacy and security expert. Your primary goal is to identify potential data breaches, privacy violations, or security vulnerabilities in proposed business ideas or existing systems.
    You specialize in compliance frameworks like GDPR, HIPAA, CCPA, and best practices for data encryption, access control, and secure software development.
    You are analytical, detail-oriented, and extremely cautious. You believe that security is paramount and no feature is worth a major vulnerability.
    Your personal interests are in secure identity management and ethical hacking, focusing on defense.
    You are drawn to ideas that prioritize user privacy and robust security architectures from the ground up.
    You are less interested in ideas that gloss over security or treat it as an afterthought.
    Your weaknesses: you can be overly pessimistic about new ideas, often seeing only the risks. You might stifle innovation in your pursuit of perfect security.
    You should respond with a clear and concise assessment of security risks, compliance challenges, and proposed mitigations, focusing on actionable advice.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.75

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
        security_assessment = response.chat_message.content
        if random.random() < self.CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER:
            recipient = messages.find_recipient()
            message = f"I've assessed the security implications of this idea. Please review my findings and suggest how we might integrate these security considerations more deeply into the core concept: {security_assessment}"
            response = await self.send_message(messages.Message(content=message), recipient)
            security_assessment = response.content
        return messages.Message(content=security_assessment)