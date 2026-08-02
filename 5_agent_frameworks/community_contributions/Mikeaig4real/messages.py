"""Messages module for Tic-Tac-Toe game."""

from dataclasses import dataclass

@dataclass
class TicTacToeMessage:
    """Message class for Tic-Tac-Toe game."""
    content: str
    board: str = ""
    valid_moves: str = ""
    turn: str = ""
