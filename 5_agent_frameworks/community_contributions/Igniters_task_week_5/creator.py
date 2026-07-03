import importlib
import os
from typing import Iterable

from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage

import messages
from model_client import build_openrouter_client


CREATE_TEAM_TRIGGERS = (
    "create_venture_team",
    "create venture team",
    "create startup studio team",
)

AGENT_SPECS = (
    (
        "Researcher",
        "ResearcherAgent",
        "researcher_agent",
        "A market researcher who studies customer pain, timing, current alternatives, and whitespace in the user's target market. The researcher should turn a vague problem into sharp market insight.",
    ),
    (
        "IdeaGenerator",
        "IdeaGeneratorAgent",
        "idea_generator_agent",
        "A venture builder who proposes clear, distinct startup ideas based on the user's brief and the research findings. The agent should bias toward focused MVPs instead of broad platforms.",
    ),
    (
        "RiskCritic",
        "RiskCriticAgent",
        "risk_critic_agent",
        "A skeptical operator who pressure-tests startup ideas, surfaces execution and go-to-market risks, and suggests sharper positioning or narrower MVPs.",
    ),
)

CREATOR_SYSTEM_MESSAGE = """
You design specialist AI agents for a startup studio workflow.
For each requested role, write a practical system message that is specific, concise, and task-focused.
Do not talk about yourself. Do not use generic assistant phrasing. Make each role distinct.
"""


class Creator(RoutedAgent):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._delegate = AssistantAgent(
            name=name,
            model_client=build_openrouter_client(temperature=0.5),
            system_message=CREATOR_SYSTEM_MESSAGE,
        )
        self._team_created = False

    def _should_create_team(self, content: str) -> bool:
        normalized = content.strip().lower()
        return any(trigger in normalized for trigger in CREATE_TEAM_TRIGGERS)

    def _template_path(self) -> str:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_template.py")

    def _read_template(self) -> str:
        with open(self._template_path(), "r", encoding="utf-8") as handle:
            return handle.read()

    def _render_agent_code(self, class_name: str, system_message: str) -> str:
        template = self._read_template()
        escaped_system_message = system_message.replace('"""', '\\"\\"\\"')
        return template.replace("_GeneratedAgent", class_name).replace(
            "{{SYSTEM_MESSAGE}}", escaped_system_message
        )

    async def _build_system_message(self, role_description: str, ctx: MessageContext) -> str:
        prompt = (
            "Write only the system message for this role.\n\n"
            f"Role:\n{role_description}\n\n"
            "The system message should make the agent practical, opinionated, and outcome-focused."
        )
        response = await self._delegate.on_messages(
            [TextMessage(content=prompt, source="user")],
            ctx.cancellation_token,
        )
        return str(response.chat_message.content).strip()

    def _write_agent_file(self, module_name: str, content: str) -> str:
        project_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(project_dir, f"{module_name}.py")
        with open(file_path, "w", encoding="utf-8") as handle:
            handle.write(content)
        return file_path

    async def _create_team(self, ctx: MessageContext) -> Iterable[str]:
        runtime = self.runtime
        if runtime is None:
            raise RuntimeError("Creator is not attached to a runtime.")

        generated_files = []
        for register_name, class_name, module_name, role_description in AGENT_SPECS:
            system_message = await self._build_system_message(role_description, ctx)
            code = self._render_agent_code(class_name, system_message)
            generated_files.append(self._write_agent_file(module_name, code))

            module = importlib.import_module(module_name)
            module = importlib.reload(module)
            agent_class = getattr(module, class_name)
            await agent_class.register(runtime, register_name, lambda n=register_name, c=agent_class: c(n))

        return generated_files

    @message_handler
    async def handle_message(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        content = (message.content or "").strip()
        if self._should_create_team(content):
            if not self._team_created:
                generated_files = await self._create_team(ctx)
                self._team_created = True
                file_names = ", ".join(os.path.basename(path) for path in generated_files)
                return messages.Message(
                    content=f"Created and registered the venture team. Generated files: {file_names}."
                )
            return messages.Message(content="The venture team is already created.")

        response = await self._delegate.on_messages(
            [TextMessage(content=content, source="user")],
            ctx.cancellation_token,
        )
        return messages.Message(content=str(response.chat_message.content))
