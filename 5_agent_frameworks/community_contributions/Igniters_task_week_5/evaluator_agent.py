import json

from pydantic import ValidationError
from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage

import messages
from model_client import build_openrouter_client
from schemas import VentureEvaluation


EVALUATOR_SYSTEM_MESSAGE = """
You are the investment committee for an AI venture studio.
Review the research, the proposed ideas, and the critique.
Rank the ideas by practical opportunity, clarity of customer pain, monetization potential, and MVP feasibility.
Prefer ideas that can be launched narrowly and validated quickly.
Return only valid structured output.
"""


class EvaluatorAgent(RoutedAgent):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._delegate = AssistantAgent(
            name=name,
            model_client=build_openrouter_client(
                temperature=0.2,
                response_format=VentureEvaluation,
            ),
            system_message=EVALUATOR_SYSTEM_MESSAGE,
        )

    @message_handler
    async def handle_message(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        response = await self._delegate.on_messages(
            [TextMessage(content=message.content, source="user")],
            ctx.cancellation_token,
        )
        raw_content = str(response.chat_message.content)
        try:
            parsed = VentureEvaluation.model_validate_json(raw_content)
            return messages.Message(content=parsed.model_dump_json(indent=2))
        except ValidationError:
            try:
                parsed = VentureEvaluation.model_validate(json.loads(raw_content))
                return messages.Message(content=parsed.model_dump_json(indent=2))
            except (ValidationError, json.JSONDecodeError) as exc:
                raise RuntimeError(f"Evaluator failed to return valid VentureEvaluation JSON. Raw output: {raw_content}") from exc
