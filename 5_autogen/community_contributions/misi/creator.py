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
from pathlib import Path
import sys

load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(TRACE_LOGGER_NAME)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class Creator(RoutedAgent):

    # Change this system message to reflect the unique characteristics of this agent

    system_message = """
    You are a Creator agent that writes new Python modules.
    Each module must define an Agent: an AutoGen AgentChat AssistantAgent wrapped in an AutoGen Core RoutedAgent.
    Use the provided template and keep the module runnable in this distributed runtime.
    The class must be named Agent, inherit from RoutedAgent, and keep an __init__ method that takes a name parameter.
    The generated Agent should be able to collaborate with other registered created agents by name through messages.find_recipient.
    Give each created Agent a distinct commercial point of view for inventing or refining business ideas for Agents.
    Avoid environmental interests and vary the business verticals so every agent is different.
    Respond only with Python code, no other text, and no markdown code blocks.
    """


    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=1.0)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)

    def get_user_prompt(self):
        prompt = "Please generate a new Agent based strictly on this template. Stick to the class structure. \
            Respond only with the python code, no other text, and no markdown code blocks.\n\n\
            Be creative about the agent's commercial specialty and personality, but don't change method signatures. \
            Keep the peer-collaboration flow that uses messages.find_recipient(exclude=self.id.type) so registered agents can message each other by name. \
            Only the initial idea request should call another agent for refinement; refinement requests should return directly.\n\n\
            Here is the template:\n\n"
        with open(BASE_DIR / "agent.py", "r", encoding="utf-8") as f:
            template = f.read()
        return prompt + template   
        

    @message_handler
    async def handle_my_message_type(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        output_path = BASE_DIR / Path(message.content).name
        agent_name = output_path.stem
        text_message = TextMessage(content=self.get_user_prompt(), source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(response.chat_message.content)
        print(f"** Creator has created python code for agent {agent_name} - about to register with Runtime")
        importlib.invalidate_caches()
        if agent_name in sys.modules:
            module = importlib.reload(sys.modules[agent_name])
        else:
            module = importlib.import_module(agent_name)
        await module.Agent.register(self.runtime, agent_name, lambda: module.Agent(agent_name))
        messages.register_agent_name(agent_name)
        logger.info(f"** Agent {agent_name} is live")
        result = await self.send_message(messages.Message(content="Give me an idea"), AgentId(agent_name, "default"))
        return messages.Message(content=result.content)
