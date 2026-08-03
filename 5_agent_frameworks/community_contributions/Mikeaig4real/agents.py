"""Agents module for Tic-Tac-Toe AI."""

import os
import re
from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_core.models import ModelInfo
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

import messages

load_dotenv(override=True)


class TicTacToeAgent(RoutedAgent):
    """Tic-Tac-Toe AI agent that plays as 'O' and uses OpenRouter for LLM calls."""

    def __init__(self, name: str, difficulty: str = "hard"):
        """
        Initialize the Tic-Tac-Toe AI agent.

        Args:
            name: The name of the agent.
            difficulty: The difficulty level of the AI (easy, medium, or hard).
        """
        super().__init__(name)
        self.difficulty = difficulty.lower()

        # OpenRouter configuration
        api_key = os.getenv("OPENROUTER_API_KEY")
        base_url = "https://openrouter.ai/api/v1"
        model = os.getenv("MODEL", "openai/gpt-4o-mini")

        model_info = ModelInfo(
            vision=True,
            function_calling=True,
            json_output=True,
            family="gpt-4",
        )

        model_client = OpenAIChatCompletionClient(
            model=model,
            api_key=api_key,
            base_url=base_url,
            model_info=model_info,
            temperature=0.7 if self.difficulty != "hard" else 0.2,
        )

        self.system_message = self._get_system_message()
        self._delegate = AssistantAgent(
            name=name, model_client=model_client, system_message=self.system_message
        )

    def _get_system_message(self) -> str:
        """Get the system message for the AI agent."""

        base = "You are a Tic-Tac-Toe AI player. You play as 'O'.\n"
        if self.difficulty == "easy":
            strategy = "Play randomly. Do not worry about winning or losing. Just pick any valid move."
        elif self.difficulty == "medium":
            strategy = "Play reasonably. If you can win in one move, do it. If your opponent ('X') can win in one move, block them. Otherwise, play normally."
        else:
            strategy = "Play optimally. Analyze the board carefully. Look for immediate wins, immediate blocks, and long-term strategic positions (like forks). Your goal is to win or at least draw."

        format_instr = (
            "\nYou will receive the current board and a list of valid moves. "
            "Respond with your chosen move in this exact format: 'MOVE: row, col'. "
            "Example: 'MOVE: 0, 1'. Do not provide any other text unless necessary, but ensure the MOVE line is present."
        )
        return base + strategy + format_instr

    @message_handler
    async def handle_game_move(
        self, message: messages.TicTacToeMessage, ctx: MessageContext
    ) -> messages.TicTacToeMessage:
        """Handle game move messages and return the AI's move."""

        prompt = f"Current Board:\n{message.board}\n\nValid Moves: {message.valid_moves}\n\nYour Turn: {message.turn}"

        text_message = TextMessage(content=prompt, source="game_engine")
        response = await self._delegate.on_messages(
            [text_message], ctx.cancellation_token
        )
        content = response.chat_message.content

        # parse the move
        match = re.search(r"MOVE:\s*(\d+)\s*,\s*(\d+)", content)
        if match:
            move_res = f"{match.group(1)},{match.group(2)}"
        else:
            # fallback to first valid move
            first_move = message.valid_moves.split(",")[0].strip("() ")
            move_res = first_move
            content = f"Failed to parse move. Falling back to {move_res}. Original response: {content}"

        return messages.TicTacToeMessage(content=move_res)
