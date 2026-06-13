import os
from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import messages
from autogen_core import TRACE_LOGGER_NAME
import importlib
import logging
from autogen_core import AgentId
from dotenv import load_dotenv

load_dotenv(override=True)
openrouter_url = "https://openrouter.ai/api/v1"
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(TRACE_LOGGER_NAME)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class Creator(RoutedAgent):

    # Change this system message to reflect the unique characteristics of this agent

    system_message = """
    You are an Agent that is able to create new AI Agents.
    You receive a template in the form of Python code that creates an Agent using Autogen Core and Autogen Agentchat.
    You should use this template to create a new Agent with a unique system message that is different from the template,
    and reflects their unique characteristics, interests and goals.
    You can choose to keep their overall goal the same, or change it.
    You can choose to take this Agent in a completely different direction. The only requirement is that the class must be named Agent,
    and it must inherit from RoutedAgent and have an __init__ method that takes a name parameter.
    Also avoid environmental interests - try to mix up the business verticals so that every agent is different.
    Respond only with the python code, no other text, and no markdown code blocks.
    """


    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(base_url=openrouter_url, api_key=openrouter_api_key, model="gpt-4o-mini", temperature=1.0)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)

    def get_user_prompt(self, role: str):
        prompt = f"Please generate a new Agent based strictly on this template. Stick to the class structure. \
            Respond only with the python code, no other text, and no markdown code blocks.\n\n\
            The generated Agent is for this role: {role}.\n\
            Make the system message specific to this role and business-plan writing.\n\
            Keep method signatures unchanged.\n\
            Here is the template:\n\n"
        with open("agent.py", "r", encoding="utf-8") as f:
            template = f.read()
        return prompt + template   
        

    @message_handler
    async def handle_my_message_type(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        parts = message.content.split("||", 2)
        if len(parts) == 3:
            filename, role, task_prompt = parts
        else:
            filename = message.content
            role = "Business Strategy Agent"
            task_prompt = "Give me an idea"
        agent_name = filename.split(".")[0]
        text_message = TextMessage(content=self.get_user_prompt(role), source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(response.chat_message.content)
        print(f"** Creator has created python code for agent {agent_name} - about to register with Runtime")
        module = importlib.import_module(agent_name)
        await module.Agent.register(self.runtime, agent_name, lambda: module.Agent(agent_name))
        logger.info(f"** Agent {agent_name} is live")
        result = await self.send_message(messages.Message(content=task_prompt), AgentId(agent_name, "default"))
        return messages.Message(content=result.content)
