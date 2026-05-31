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

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(TRACE_LOGGER_NAME)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


# Tool function that reads creator.py
def read_creator_template() -> str:
    """Reads creator.py and returns its contents so the LLM can use it as a template."""
    with open("creator.py", "r", encoding="utf-8") as f:
        return f.read()



class Creator(RoutedAgent):

    # Change this system message to reflect the unique characteristics of this creator agent
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

    # Change this system message to reflect the unique characteristics of this creator agent when creating another Creator agent
    creator_system_message = """
    You are an Agent that creates new Creator Agents.
    You will receive the source code of an existing Creator agent as a template.
    Your job is to produce a variation of it — you may change the model temperature,
    or add small behavioural tweaks, 
    you should change the system message to reflect the unique characteristics and personality of this creator agent, 
    but you MUST keep:
      - The class named Creator
      - It inheriting from RoutedAgent
      - All method signatures identical
      - The read_creator_template tool registered on the delegate
    Respond only with python code, no other text, and no markdown code blocks.
    """

    def __init__(self, name) -> None:
        super().__init__(name)

        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=1.0)

        # for regular agents
        self._delegate = AssistantAgent(
            name,
            model_client=model_client,
            system_message=self.system_message,
        )

        # for creator agents
        self._creator_delegate = AssistantAgent(
            name + "_creator_maker",
            model_client=model_client,
            system_message=self.creator_system_message,
            tools=[read_creator_template],
        )


    def get_user_prompt(self):
        prompt = (
            "Please generate a new Agent based strictly on this template. Stick to the class structure. "
            "Respond only with the python code, no other text, and no markdown code blocks.\n\n"
            "Be creative about taking the agent in a new direction, but don't change method signatures.\n\n"
            "Here is the template:\n\n"
        )
        with open("agent.py", "r", encoding="utf-8") as f:
            template = f.read()
        return prompt + template


    def get_creator_prompt(self):
        prompt = (
            "Please generate a new Creator agent based on this template. "
            "Keep the class name as Creator and all method signatures identical. "
            "Respond only with python code, no other text, and no markdown code blocks.\n\n"
            "Here is the template:\n\n"
        )
        template = read_creator_template()
        return prompt + template



    @message_handler
    async def handle_my_message_type(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        filename = message.content
        agent_name = filename.split(".")[0]

        # make a creator agent if the filename starts with "creator" (e.g. "creator2.py"), otherwise make a regular agent
        if filename.startswith("creator"):
            print(f"** Creator is making a new Creator agent: {filename}")
            text_message = TextMessage(content=self.get_creator_prompt(), source="user")
            response = await self._creator_delegate.on_messages([text_message], ctx.cancellation_token)
            code = response.chat_message.content
            with open(filename, "w", encoding="utf-8") as f:
                f.write(code)
            module = importlib.import_module(agent_name)
            await module.Creator.register(self.runtime, agent_name, lambda: module.Creator(agent_name))
            logger.info(f"** Creator {agent_name} is live")
            return messages.Message(content=f"New creator {agent_name} is ready.")

        else:
            text_message = TextMessage(content=self.get_user_prompt(), source="user")
            response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
            code = response.chat_message.content
            with open(filename, "w", encoding="utf-8") as f:
                f.write(code)
            module = importlib.import_module(agent_name)
            await module.Agent.register(self.runtime, agent_name, lambda: module.Agent(agent_name))
            logger.info(f"** Agent {agent_name} is live")
            result = await self.send_message(messages.Message(content="Give me an idea"), AgentId(agent_name, "default"))
            return messages.Message(content=f"Created by: {self.id.type} | Agent: {agent_name}\n\n{result.content}")