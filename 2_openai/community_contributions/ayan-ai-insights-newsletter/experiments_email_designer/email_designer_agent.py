from dotenv import load_dotenv
from agents import Agent
from pydantic import BaseModel
from datetime import datetime

load_dotenv(override=True)

class EmailDesignerOutput(BaseModel):
    html_content: str

with open("system_prompts/email_designer_prompt.txt", "r") as f:
    email_designer_prompt = f"Today's date is {datetime.now().strftime('%Y-%m-%d')}. "
    email_designer_prompt += f.read()

email_designer = Agent(
    name="E-Mail Designer",
    instructions=email_designer_prompt,
    model="gpt-4o-mini",
    output_type=EmailDesignerOutput
)