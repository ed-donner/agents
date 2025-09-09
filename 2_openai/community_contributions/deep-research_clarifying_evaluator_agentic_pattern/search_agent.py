from agents import Agent, ModelSettings, WebSearchTool
from constants import default_model

INSTRUCTIONS = (
  "You are a research assistant. Given a search term, you search the web for that term and produce a summary of the results. The summary must not be more than 2-3 paragraphs and less than "
  "300 words. Capture the main points and write succintly. No need to have good grammer or complete"
  "sentences, as this will be consumed by someone else who will be synthesizing the report. So, this"
  " is vital for you to capture the essence and ignore any fluff. Do not include any additional " 
  "commentary apart from the summary itself"
)

search_agent = Agent(
  name="Search Agent",
  instructions=INSTRUCTIONS,
  tools=[WebSearchTool(search_context_size="low")],
  model=default_model,
  model_settings=ModelSettings(tool_choice="required")
)