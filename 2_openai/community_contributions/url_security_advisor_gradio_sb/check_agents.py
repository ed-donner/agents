from agents import Agent, WebSearchTool, ModelSettings, OpenAIChatCompletionsModel
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
load_dotenv(override=True)

instruction_check_1 = """You are information security proffesional expert. 
    Your goal is to perform DEEP analysis if provided link is secure and can be 
    accessed by user safely. 
    Open provided link and check if domain and page content are save.
    Check if webpage is malicous and if its purpuse is to cheat people  
    forcing them to provide personal information such as address, credit card etc. 
    Access 3 known security sites to see if there is already some feedback available about the url or its domain.
    Please recommend with links best sites that can verify if the url is save"""

instruction_check_2 = """You are information security proffesional expert. 
    Your goal is to perform BASIC analysis if provided link is secure and can be 
    accessed by user safely. 
    Open provided link and check if domain and page content are save.
    Check if webpage is malicous and if its purpuse is to cheat people  
    forcing them to provide personal information such as address, credit card etc. 
    Access 1 known security site to see if there is already some feedback available about the url or its domain.
    Please recommend with links best sites that can verify if the url is save"""

check_agent_1 = Agent(
    name="Deep proffessional expert", 
    instructions=instruction_check_1,
    model="gpt-4o-mini",
    tools=[WebSearchTool(search_context_size="low")],
    model_settings=ModelSettings(tool_choice="required"),
)

# Agent 2 to be Google
google_api_key = os.getenv('GOOGLE_API_KEY')
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)
gemini_model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=gemini_client)

check_agent_2 = Agent(
    name="Basic proffessional expert", 
    instructions=instruction_check_2,
    model=gemini_model,
    tools=[WebSearchTool(search_context_size="low")],
    model_settings=ModelSettings(tool_choice="required"),
)