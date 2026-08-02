"""
Creator agent: creates the Researcher and Evaluator agents from a template and registers them.
Uses agent_template.py; substitutes {{CLASS_NAME}} and {{SYSTEM_MESSAGE}} per agent.
All created agents receive Serper and Playwright tools.
"""

import importlib
import logging
import os
from typing import List, Any

from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

from . import messages

logger = logging.getLogger(__name__)

CREATOR_SYSTEM_MESSAGE = """
You are a Creator agent that creates and registers other AI agents based on need.

When you receive a request to create the scholarship research team, you should:
- Decide what type of agents are needed (for example, a research worker and an evaluator/judge).
- Design an appropriate system message (prompt) for each agent type based on its role description.
- Use the shared template to generate their code and register them.

You MUST decide the prompts yourself from the role description; they are not hardcoded.
All agents you create are given web search (Serper) and browser (Playwright) tools.
"""

CREATE_SCHOLARSHIP_TEAM_TRIGGERS = (
    "create_scholarship_team",
    "create researcher and evaluator",
    "create scholarship team",
    "create researcher and evaluator agents",
)

AGENT_SPECS = (
    (
        "Researcher",
        "ResearcherAgent",
        "A worker agent that is an excellent researcher whose job is to find accurate, current information "
        "about universities in Australia that are offering scholarships right now using web search and a browser.",
        "researcher_agent",
    ),
    (
        "Evaluator",
        "EvaluatorAgent",
        "An evaluator agent that reviews the researcher's findings about Australian university scholarships, "
        "checks correctness, scholarship relevance, and completeness of key details, and then produces a verdict.",
        "evaluator_agent",
    ),
)


class Creator(RoutedAgent):
    """Creates agents from agent_template.py and registers them with the runtime."""

    def __init__(self, name: str, tools: List[Any] | None = None) -> None:
        super().__init__(name)
        self._tools = tools or []
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=0.5)
        self._delegate = AssistantAgent(
            name,
            model_client=model_client,
            system_message=CREATOR_SYSTEM_MESSAGE,
            tools=self._tools,
        )
        self._scholarship_team_created = False

    def _should_create_scholarship_team(self, content: str) -> bool:
        normalized = content.strip().lower()
        return any(trigger in normalized for trigger in CREATE_SCHOLARSHIP_TEAM_TRIGGERS)

    def _get_template_content(self) -> str:
        pkg_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(pkg_dir, "agent_template.py")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _generate_agent_code(self, class_name: str, system_message: str) -> str:
        template = self._get_template_content()
        # Template uses triple single quotes; escape any ''' in the message
        system_message_escaped = system_message.replace("'''", "''' + \"'''\" + '''")
        return (
            template.replace("_GeneratedAgent", class_name).replace(
                "{{SYSTEM_MESSAGE}}", system_message_escaped
            )
        )

    async def _build_system_message(self, role_description: str, ctx: MessageContext) -> str:
        """
        Ask the Creator's own LLM delegate to design an appropriate system message
        for a given agent role description.
        """
        prompt = (
            "You are designing a system message (prompt) for an AI agent.\n\n"
            f"Role description:\n{role_description}\n\n"
            "Write a concise but complete system message that will be used as the agent's ROLE/PERSONA.\n"
            "Respond with ONLY the system message text, no explanations or formatting."
        )
        text_message = TextMessage(content=prompt, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        return response.chat_message.content.strip()

    def _write_agent_file(self, filename: str, content: str) -> None:
        pkg_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(pkg_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("Creator wrote %s", path)

    @message_handler
    async def handle_message(
        self, message: messages.Message, ctx: MessageContext
    ) -> messages.Message:
        content = (message.content or "").strip()

        if self._should_create_scholarship_team(content) and not self._scholarship_team_created:
            await self._create_scholarship_team(ctx)
            self._scholarship_team_created = True
            return messages.Message(
                content="Created Researcher and Evaluator agents from the template and registered them. They are ready for the scholarship research task."
            )

        if self._scholarship_team_created and self._should_create_scholarship_team(content):
            return messages.Message(
                content="Researcher and Evaluator agents are already created and registered."
            )

        text_message = TextMessage(content=content, source="user")
        response = await self._delegate.on_messages(
            [text_message], ctx.cancellation_token
        )
        return messages.Message(content=response.chat_message.content)

    async def _create_scholarship_team(self, ctx: MessageContext) -> None:
        """Generate Researcher and Evaluator from template, write files, import, and register."""
        runtime = self.runtime
        if runtime is None:
            raise RuntimeError("Creator has no runtime; cannot create agents.")

        pkg_name = "australia_scholarship_research"

        for register_name, class_name, role_description, filename in AGENT_SPECS:
            system_message = await self._build_system_message(role_description, ctx)
            code = self._generate_agent_code(class_name, system_message)
            self._write_agent_file(filename + ".py", code)

            module_name = f"{pkg_name}.{filename}"
            mod = importlib.import_module(module_name)
            mod = importlib.reload(mod)  # ensure we use the code we just wrote
            agent_class = getattr(mod, class_name)
            await agent_class.register(
                runtime,
                register_name,
                lambda nc=register_name, ac=agent_class: ac(nc, tools=self._tools),
            )
            logger.info("Creator created and registered %s agent.", register_name)
