"""
This is a self replicating-creator that uses itself as a template to create Agents.
It achieves this by passing its own source code as the template to the LLM through the use 
of the inspect module.
"""

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


class Creator(RoutedAgent):

    system_message = """
    ou are a Recursive Agent Creator. Your goal is to generate Python code for a NEW agent that can ALSO create agents \
    using Autogen Core and Autogen Agentchat.
    You should use this template to create a new Agent with a unique system message that is different from the template,
    and reflects their unique characteristics, interests and goals.
    You can choose to keep their overall goal the same, or change it.
    You can choose to take this Agent in a completely different direction. The only requirement is that the class must be named Agent,
    and it must inherit from RoutedAgent and have an __init__ method that takes a name parameter.
    initialize self.delegate property to use gpt-4o-mini with a temperature of 0.7 model_client.
    craft a an appriopriate system message that portrays the llm as a creative entrepreneur that come up with a new business idea using Agentic AI, or refine an existing idea.
    Also avoid environmental interests - try to mix up the business verticals so that every agent is different.
    Respond only with the python code, no other text, and no markdown code blocks.
    The class MUST be named 'Agent' and inherit from 'RoutedAgent'.
    It MUST include a 'handle_my_message_type' method with the '@message_handler' decorator.
    The handler logic must: 
        - Generate code for a child agent.
        - Save it to a file.
        - Import and register that child agent with the runtime.
    Give the new agent a unique niche (e.g., 'Supply Chain Architect' or 'FinTech Specialist').
    Output ONLY raw Python code. No markdown, no backticks.
    """


    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=1.0)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)

    def get_user_prompt(self): 
        template = inspect.getsource(self.__class__)
        
        prompt = "You are a self-replicating entity. Use the following source code as your blueprint. \
             Create a new 'Agent' class that maintains this exact functional structure but \
             evolves into a new industry vertical. Ensure the internal logic remains intact.\n\n\
             Respond only with the python code, no other text, and no markdown code blocks.\n\n\
             Be creative about taking the agent in a new direction, but don't change method signatures.\n\n\
             Here is the template:\n\n"
        
        return prompt + template
        

    @message_handler
    async def handle_my_message_type(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        filename = message.content
        agent_name = filename.split(".")[0]
        text_message = TextMessage(content=self.get_user_prompt(), source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(response.chat_message.content)
        print(f"** Creator has created python code for agent {agent_name} - about to register with Runtime")
        try:
            module = importlib.import_module(agent_name)
            await module.Agent.register(self.runtime, agent_name, lambda: module.Agent(agent_name))
            logger.info(f"** Agent {agent_name} is live")
            result = await self.send_message(messages.Message(content="Give me an idea"), AgentId(agent_name, "default"))
            return messages.Message(content=result.content)
            
        except Exception as e:
            return messages.Message(content=f"Replication failed: {str(e)}")

