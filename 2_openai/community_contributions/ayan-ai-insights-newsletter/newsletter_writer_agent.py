from dotenv import load_dotenv
from agents import Agent
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

load_dotenv(override=True)

class NewsletterSection(BaseModel):
    headline: str = Field(description="The headline of the newsletter item.")
    body: str = Field(description="The content body of the newsletter item. This should NOT contain any links.")
    source_link: str = Field(description="The link related to the item.")

class NewsletterWriterOutput(BaseModel):
    sections: List[NewsletterSection] = Field(description="List of NewsletterSection items.")

with open('system_prompts/newsletter_writer_prompt.txt') as f:
    newsletter_writer_agent_prompt = f"Today's date is {datetime.now().strftime('%Y-%m-%d')}. "
    newsletter_writer_agent_prompt += f.read()

newsletter_writer_agent = Agent(
    name="Newsletter Writer Agent",
    instructions=newsletter_writer_agent_prompt,
    model="gpt-4o-mini",
    output_type=NewsletterWriterOutput
)