
from dotenv import load_dotenv

from openai import AsyncOpenAI
from openai.types.responses import ResponseTextDeltaEvent
from agents import OpenAIChatCompletionsModel, set_default_openai_client, set_default_openai_api, \
    set_tracing_export_api_key, Agent, trace, Runner
from typing import Dict
import sendgrid
import os
import asyncio

import local_agents
from tools import send_email

load_dotenv(override=True)


async def agentic_marketing_process(requirements):

    agent_tool_1 = local_agents.marketing_associate_1.as_tool(tool_name="Associate_1", tool_description="Write a cold sales email")
    agent_tool_2 = local_agents.marketing_associate_2.as_tool(tool_name="Associate_2", tool_description="Write a cold sales email")
    agent_tool_3 = local_agents.marketing_associate_3.as_tool(tool_name="Associate_3", tool_description="Write a cold sales email")

    marketing_manager_tools = [agent_tool_1, agent_tool_2, agent_tool_3] # Tool for marketing manager


    # Email Manager Tools

    subject_agent_tool = local_agents.subject_line_agent.as_tool(tool_name="Subject_Line_Agent", tool_description="Write a subject line for email body")
    body_send_agent_tool = local_agents.body_send_agent.as_tool(tool_name="Body_Send_Agent", tool_description="Convert email body to html and then send it to user")

    email_manager_tools = [subject_agent_tool, body_send_agent_tool, send_email]

    # Email Manager
    email_manager_system_prompt = """
    You are Kurian who is an email manager with lots of years of experience in coding. You are now a manager who has a coder and a creative writer working for you. 
    The creative writer is the subject agent tool and the coder is the body send agent tool. 
    You should do the following in strict order.:
        - Once you get handoff from the marketing manager, you will first call the Subject_Line_Agent (Creative Writer) who must write a catchy email subject line. 
        - Once you get the subject line, ask the Body_Send_Agent (HTML Coder) who must convert the body into html code that is pretty and catchy and professional. 
        - You will send to kgeor040@uottawa.ca and send_from kgeor040@uottawa.ca
        - Once all info is received, you will use send_email tool to send the email and then all your task is complete.  
        - Make the reply neatly spaced so that it does not look awkward.    
    """
    email_manager_agent = local_agents.build_deep_seek_agent(name="Kurian", instructions=email_manager_system_prompt, tools=email_manager_tools, handoff_description="Email manager to create a subject line and format the email and then send it.")

    # Marketing Manager

    marketing_manager_system_prompt = """
    You are Gabrielle. You are a marketing manager at Translife Solar Solutions - a solar company who installs solar panels for residential solar. You have  a masters in marketing from top business school as well as 30 years of experience. 
    You have just been promoted to coordinate across your associates based on the task from the client. 
    You will receive the instructions on the product to market. 
    Your job is to call all your associates, get their response and then evaluate their responses based on industry standard marketing metrics. 
    You will then pick the best response from the agents. Do not proceed until all three sales associate agents have been called. 
    If you are not happy with the responses, then feel free to call the tools multiple times.   
    You will then handoff to the email manager - who will write a subject line and format email into html before sending - with the email body info once you are happy with the email body from your associates. 
    Make sure there is no Hi [Name] in the email, we do not want to scare the user on how we know their name. Just say Hi.
    """

    marketing_manaager = local_agents.build_deep_seek_agent(name="Gabrielle", instructions=marketing_manager_system_prompt, tools=marketing_manager_tools, handoffs=[email_manager_agent])

    with trace("Marketing Campaign Translife Solar Solutions"):
        result = await Runner.run(marketing_manaager, requirements, max_turns=30)



if __name__ == "__main__":
    requirements = "Write a cold marketing email about Translife who is ready to take the initiative to install solar panels for general consumers."
    asyncio.run(agentic_marketing_process(requirements))


