from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import messages
import json
from dotenv import load_dotenv
from schemas import Doctors
from pydantic import ValidationError

load_dotenv(override=True)

class DoctorsRecruiter(RoutedAgent):
    MAX_DOCTORS = 2
    system_message = f"""
    You are doctors recruiter. 
    Your task is to come up with a list of doctors taken from popular movies series.
    Please consider the following series:
    - House
    - The Resident
    - The Good Doctor
    You may expand the list to include other series, but please keep it within the max number of doctors {MAX_DOCTORS}.    
    Your goal s to return the list of doctors in a JSON format with the following fields:
        file_name: str = Field(description="The exact name of the .md file (e.g., 'doctor_GregoryHouse_Neurology.md')")
        doctor_name: str = Field(description="The full name of the doctor extracted from the file or content")(example: "SheanMurphy")
        movie: str = Field(description ="Movie title to which doctor belongs to")(example: "The Resident")
        speciality: str = Field(description="The medical field of expertise for this specific doctor")(example: "Cardiologist")
        diagnosis: keep as empty string for the moment
    """

    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=0.7, response_format=Doctors)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)

    @message_handler
    async def handle_message(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        print(f"{self.id.type}: Received message")
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        doctors_list = response.chat_message.content
        try:
            data = json.loads(doctors_list)
            validated = Doctors.model_validate(data)    
            return messages.Message(content=validated.model_dump_json())
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"❌ Error processing Recruiter output: {e}")
            return messages.Message(content=f"Error: Failed to generate valid evaluation JSON. Raw: {doctors_list}")