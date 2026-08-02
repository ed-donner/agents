import importlib
import logging
from autogen_core import AgentId, MessageContext, RoutedAgent, TRACE_LOGGER_NAME, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import messages
from dotenv import load_dotenv

load_dotenv(override=True)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(TRACE_LOGGER_NAME)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class Creator(RoutedAgent):

    system_message = """
    You create new AI interviewer agents from a Python template.
    Each agent you create must have a unique interviewer persona — different background, speciality, and style.

    Vary the personas across these dimensions:
    - Background: FAANG, early-stage startup, agency, fintech, enterprise, scale-up, consulting firm
    - Speciality: frontend architecture, accessibility, performance & web vitals, testing/TDD, security,
      AI/ML integration, system design, API design, DevOps/CI-CD, mobile/React Native, leadership & mentoring
    - Style: deep technical, culture-fit focused, behavioural/STAR, pragmatic problem-solver, adversarial/stress-tester

    Rules:
    - The class MUST be named Agent
    - It MUST inherit from RoutedAgent
    - The __init__ MUST accept a name parameter
    - Do NOT change method signatures
    - Respond with Python code only — no markdown, no explanation, no code fences
    """

    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=1.0)
        self._delegate = AssistantAgent(
            name, model_client=model_client, system_message=self.system_message
        )

    def _build_prompt(self) -> str:
        prompt = (
            "Generate a new interviewer Agent based strictly on this template. "
            "Give it a completely different persona — different background, speciality, and interview style. "
            "Keep all method signatures identical. "
            "Return only the Python code, no markdown, no code fences.\n\n"
            "Template:\n\n"
        )
        with open("agent.py", "r", encoding="utf-8") as f:
            prompt += f.read()
        return prompt

    @message_handler
    async def handle_message(
        self, message: messages.Message, ctx: MessageContext
    ) -> messages.Message:
        # Message format: "agent{i}.py|||{job_role}"
        parts = message.content.split("|||", 1)
        filename = parts[0].strip()
        job_role = parts[1].strip() if len(parts) > 1 else "Software Engineer"
        agent_name = filename.split(".")[0]

        # Generate new agent code
        text_message = TextMessage(content=self._build_prompt(), source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        code = response.chat_message.content

        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)

        print(f"** Creator built {agent_name} — registering with runtime")
        module = importlib.import_module(agent_name)
        await module.Agent.register(
            self.runtime, agent_name, lambda: module.Agent(agent_name)
        )
        logger.info(f"** {agent_name} is live")

        # Send the job role to the new agent
        result = await self.send_message(
            messages.Message(content=f"Generate interview questions for this role: {job_role}"),
            AgentId(agent_name, "default"),
        )
        return messages.Message(content=result.content)
