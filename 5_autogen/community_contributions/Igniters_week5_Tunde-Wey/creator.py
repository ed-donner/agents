"""
Creator: uses AgentChat (AssistantAgent) to emit Python modules that define Core RoutedAgents,
then registers each module on the same distributed worker runtime.
"""

from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path

from autogen_core import TRACE_LOGGER_NAME, AgentId, MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

import messages

load_dotenv(override=True)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(TRACE_LOGGER_NAME)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

_ROOT = Path(__file__).resolve().parent
_TEMPLATE_PATH = _ROOT / "agent_template.py"


def _strip_code_fence(text: str) -> str:
    t = text.strip()
    if not t.startswith("```"):
        return t
    lines = t.split("\n")
    if lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


class Creator(RoutedAgent):
    system_message = """
    You are the Creator: you output a single Python module that defines class Agent (RoutedAgent) using AutoGen Core
    and an AgentChat AssistantAgent as internal delegate, exactly like the template you are given.
    Each file will be registered under a runtime type name equal to the filename without .py (e.g. scout.py -> "scout").
    The collaboration roster is fixed: scout, synthesizer, closer. They must import and use `messages.random_peer_excluding`
    and/or `messages.agent_by_name` so peers can message each other by those names.
    Give each generated agent a distinct persona (e.g. market scout vs offer synthesizer vs GTM closer) but keep:
    - class name Agent
    - __init__(self, name)
    - one @message_handler async def handle_message(self, message: messages.Message, ctx: MessageContext) -> messages.Message
    Respond with Python source only — no markdown fences, no explanation.
    """

    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=1.0)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)

    def get_user_prompt(self, module_stem: str) -> str:
        template = _TEMPLATE_PATH.read_text(encoding="utf-8")
        roster = ", ".join(messages.ROSTER)
        return (
            f"Generate the full contents of `{module_stem}.py`.\n"
            f"The agent's runtime type / name will be exactly `{module_stem}`.\n"
            f"Collaboration peers (must remain messageable via messages.ROSTER / agent_by_name): {roster}.\n"
            "Goal of the team: converge on a commercial business idea for the AI agents industry.\n\n"
            "Strictly preserve imports that the template uses (adjust only if required for validity).\n"
            "Respond only with Python code, no markdown.\n\n"
            f"Template to adapt (unique system_message and persona for role `{module_stem}`):\n\n{template}"
        )

    @message_handler
    async def handle_my_message_type(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        filename = message.content.strip()
        if not filename.endswith(".py"):
            filename = f"{filename}.py"
        module_stem = Path(filename).stem

        text_message = TextMessage(content=self.get_user_prompt(module_stem), source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        code = _strip_code_fence(response.chat_message.content)

        out_path = _ROOT / filename
        out_path.write_text(code, encoding="utf-8")
        print(f"** Creator wrote {out_path.name} — registering on distributed runtime **")

        compile(code, str(out_path), "exec")

        if module_stem in sys.modules:
            module = importlib.reload(sys.modules[module_stem])
        else:
            sys.path.insert(0, str(_ROOT))
            module = importlib.import_module(module_stem)

        await module.Agent.register(self.runtime, module_stem, lambda: module.Agent(module_stem))
        logger.info("** Agent %s is live **", module_stem)

        ping = await self.send_message(
            messages.Message(content="Briefly state your role in one sentence."),
            AgentId(module_stem, "default"),
        )
        return messages.Message(content=f"Registered `{module_stem}`.\nInitial reply:\n{ping.content}")
