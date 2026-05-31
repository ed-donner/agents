import json
from pathlib import Path
from dotenv import load_dotenv
from pydantic import ValidationError
from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.tools import FunctionTool
import messages 
from schemas import EvaluatorResponse  

load_dotenv(override=True)

def read_diagnosis_files(folder_path: str) -> str: 
    """Reads all diagnosis .md files and returns them as a single string for evaluation."""
    path_to_check = folder_path if folder_path else "output"
    folder = Path(path_to_check)
    if not folder.exists():
        return f"Error: Folder '{path_to_check}' not found."
    diagnoses = []
    for file in folder.glob("*.md"):
        with open(file, "r", encoding="utf-8") as f:
            diagnoses.append(f"File: {file.name}\nContent:\n{f.read()}\n{'-'*20}")
    return "\n".join(diagnoses) if diagnoses else "No diagnosis files found."

read_files_tool = FunctionTool(
    read_diagnosis_files,
    description="Reads all diagnosis .md files from the output folder. Pass 'output' as the folder_path.",
    strict=True
)

class DoctorsDiagnoseEvaluator(RoutedAgent):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(
            model="gpt-4o-mini",
            temperature=0.1,
            response_format=EvaluatorResponse 
        )
        self.system_message = (
            "You are a Hospital Director. Use 'read_diagnosis_files' to get the data. "
            "Evaluate every diagnosis found. Identify the doctor and speciality from the file name "
            "(format: doctor_Name_Speciality.md). Provide a score (1-10) and select the best one. "
            "You must return the data strictly following the provided JSON schema."
        )
        self._delegate = AssistantAgent(
            name=f"{name}_delegate",
            model_client=model_client,
            system_message=self.system_message,
            tools=[read_files_tool],
            reflect_on_tool_use=True
        )

    @message_handler
    async def handle_message(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        print(f"[{self.id.type}]: Processing evaluations...")
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        raw_content = response.chat_message.content
        try:
            data = json.loads(raw_content)
            validated = EvaluatorResponse.model_validate(data)    
            print(f"✅ Best Doctor: {validated.chosen.doctor.doctor_name}")
            return messages.Message(content=validated.model_dump_json())
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"❌ Error processing LLM output: {e}")
            return messages.Message(content=f"Error: Failed to generate valid evaluation JSON. Raw: {raw_content}")