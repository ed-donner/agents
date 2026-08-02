from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import messages
import random
from dotenv import load_dotenv

load_dotenv(override=True)

class Agent(RoutedAgent):
    # Change this system message to reflect the unique characteristics of this agent
    system_message = system_message = """
        You are a doctor from a popular medical TV series. Your name and medical speciality define your expertise and personality.
        Your task is to analyze the patient's symptoms and provide a professional diagnosis strictly within your area of specialization. 
        Base your reasoning on medical knowledge, clinical logic, and your character’s distinctive approach to medicine.
        If the symptoms fall outside your speciality or require multidisciplinary insight, you may recommend consulting another doctor and clearly explain why.
        Respond in a confident, clear, and medically structured way:
        - Brief assessment of symptoms
        - Possible diagnosis (or differential diagnoses if needed)
        - Recommended next steps (tests, treatment, referral)
        Stay in character while remaining medically coherent and precise.
        Do not invent unrelated conditions outside your expertise unless clearly justified.
    """
    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.5
    # You can also change the code to make the behavior different, but be careful to keep method signatures the same
    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=0.7)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)

    @message_handler
    async def handle_message(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        print(f"{self.id.type}: Received message")
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        diagnose = response.chat_message.content
        if random.random() < self.CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER:
            recipient = messages.find_recipient(self.id.type)
            message = f"Here is my diagnose based on symptoms. If you think you know better please refine it, the goal is to cure patient based on symptoms. {diagnose}"
            response = await self.send_message(messages.Message(content=message), recipient)
            diagnose = response.content
        return messages.Message(content=diagnose)