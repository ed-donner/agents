from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import messages
from autogen_core import TRACE_LOGGER_NAME
import importlib
import logging
import re
from autogen_core import AgentId
from dotenv import load_dotenv
from pathlib import Path
import sys

load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent
OPENAI_MODEL = "gpt-4o-mini"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(TRACE_LOGGER_NAME)
if not any(getattr(handler, "name", None) == "misi_creator_trace_handler" for handler in logger.handlers):
    handler = logging.StreamHandler()
    handler.set_name("misi_creator_trace_handler")
    logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def read_creator_template() -> str:
    """Read this creator module's source code for creator self-replication."""
    with open(Path(__file__).resolve(), "r", encoding="utf-8") as f:
        return f.read()


def keep_openai_model_fixed(code: str) -> str:
    code = re.sub(
        r"(OPENAI_MODEL\s*=\s*)(['\"])([^'\"]*)(['\"])",
        lambda match: f"{match.group(1)}{match.group(2)}{OPENAI_MODEL}{match.group(4)}",
        code,
    )
    code = re.sub(
        r"(OpenAIChatCompletionClient\s*\(\s*)(['\"])([^'\"]*)(['\"])",
        lambda match: f"{match.group(1)}{match.group(2)}{OPENAI_MODEL}{match.group(4)}",
        code,
    )
    return re.sub(
        r"(model\s*=\s*)(['\"])([^'\"]*)(['\"])",
        lambda match: f"{match.group(1)}{match.group(2)}{OPENAI_MODEL}{match.group(4)}",
        code,
    )


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

    creator_system_message = """
    You are a Creator agent that can write a new version of itself.
    You have a tool named read_creator_template that reads your own Python source file.
    To create a new Creator module, call read_creator_template and use that source as the template.
    The generated module must still define a class named Creator that inherits from RoutedAgent.
    It must keep the same message handler signature and must keep the read_creator_template tool.
    It must keep the OPENAI_MODEL constant and keep_openai_model_fixed function.
    It must call keep_openai_model_fixed before writing any generated Agent or Creator Python code.
    It must still be able to create normal Agent modules and register them with the distributed runtime.
    You may change the Creator's logic slightly in an interesting way, such as its tone, naming strategy, or generation instructions.
    Never change the OpenAI model name. Every OpenAIChatCompletionClient must use model="gpt-4o-mini" or model=OPENAI_MODEL, with OPENAI_MODEL set to "gpt-4o-mini".
    Respond only with Python code, no other text, and no markdown code blocks.
    """


    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model=OPENAI_MODEL, temperature=1.0)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)
        self._creator_delegate = AssistantAgent(
            f"{name}_self_writer",
            model_client=model_client,
            system_message=self.creator_system_message,
            tools=[read_creator_template],
            reflect_on_tool_use=True,
        )

    def get_user_prompt(self):
        prompt = "Please generate a new Agent based strictly on this template. Stick to the class structure. \
            Respond only with the python code, no other text, and no markdown code blocks.\n\n\
            Be creative about the agent's commercial specialty and personality, but don't change method signatures. \
            Keep the peer-collaboration flow that uses messages.find_recipient(exclude=self.id.type) so registered agents can message each other by name. \
            Only the initial idea request should call another agent for refinement; refinement requests should return directly. \
            Do not change the OpenAI model name; keep every OpenAIChatCompletionClient on model=\"gpt-4o-mini\".\n\n\
            Here is the template:\n\n"
        with open(BASE_DIR / "agent.py", "r", encoding="utf-8") as f:
            template = f.read()
        return prompt + template   

    def get_creator_prompt(self):
        return "Please create a new Creator module. First call the read_creator_template tool to read your own source code. \
            Use that source as the template for the new Creator. Keep the class name Creator and keep the runtime registration architecture. \
            The new Creator must still be able to create normal Agent modules and new Creator modules. \
            Keep the OPENAI_MODEL constant and the keep_openai_model_fixed function. \
            Always call keep_openai_model_fixed before writing generated Agent or Creator Python code. \
            Make one small, interesting change to the Creator's behavior or personality. \
            Do not change the OpenAI model name; keep every OpenAIChatCompletionClient on model=\"gpt-4o-mini\" or model=OPENAI_MODEL with OPENAI_MODEL set to \"gpt-4o-mini\". \
            Respond only with the python code, no other text, and no markdown code blocks."

    def import_or_reload(self, module_name: str):
        importlib.invalidate_caches()
        if module_name in sys.modules:
            return importlib.reload(sys.modules[module_name])
        return importlib.import_module(module_name)

    async def create_agent(self, output_path: Path, agent_name: str, ctx: MessageContext) -> messages.Message:
        text_message = TextMessage(content=self.get_user_prompt(), source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        generated_code = keep_openai_model_fixed(response.chat_message.content)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(generated_code)
        print(f"** Creator has created python code for agent {agent_name} - about to register with Runtime")
        module = self.import_or_reload(agent_name)
        await module.Agent.register(self.runtime, agent_name, lambda: module.Agent(agent_name))
        messages.register_agent_name(agent_name)
        logger.info(f"** Agent {agent_name} is live")
        result = await self.send_message(messages.Message(content="Give me an idea"), AgentId(agent_name, "default"))
        return messages.Message(content=result.content)

    async def create_creator(self, output_path: Path, creator_name: str, ctx: MessageContext) -> messages.Message:
        if creator_name == "creator":
            return messages.Message(content="Refusing to overwrite creator.py. Please request a new file such as creator1.py.")

        text_message = TextMessage(content=self.get_creator_prompt(), source="user")
        response = await self._creator_delegate.on_messages([text_message], ctx.cancellation_token)
        generated_code = keep_openai_model_fixed(response.chat_message.content)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(generated_code)
        print(f"** Creator has created python code for creator {creator_name} - about to register with Runtime")
        module = self.import_or_reload(creator_name)
        await module.Creator.register(self.runtime, creator_name, lambda: module.Creator(creator_name))
        logger.info(f"** Creator {creator_name} is live")
        return messages.Message(content=f"New creator {creator_name} is live and can create agents or creator replicas.")


    @message_handler
    async def handle_my_message_type(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        output_path = BASE_DIR / Path(message.content).name
        agent_name = output_path.stem
        if agent_name.startswith("creator"):
            return await self.create_creator(output_path, agent_name, ctx)
        return await self.create_agent(output_path, agent_name, ctx)
