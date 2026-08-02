"""Tic-Tac-Toe game engine for n x n grid with k-in-a-row win condition."""

from typing import List, Optional, Tuple

class TicTacToeEngine:
    """Tic-Tac-Toe game engine for n x n grid with k-in-a-row win condition."""
    def __init__(self, n: int = 3, k: int = 3):
        """
        Initialize the Tic-Tac-Toe engine.
        :param n: Grid size (n x n)
        :param k: Number of consecutive marks to win
        """
        self.n = n
        self.k = k
        self.board = [['.' for _ in range(n)] for _ in range(n)]
        self.current_turn = 'X'  # X starts

    def get_board_string(self) -> str:
        """Returns a string representation of the board for LLM input."""
        res = "  " + " ".join(str(i) for i in range(self.n)) + "\n"
        for i, row in enumerate(self.board):
            res += f"{i} " + " ".join(row) + "\n"
        return res

    def get_valid_moves(self) -> List[Tuple[int, int]]:
        """Returns a list of (row, col) tuples representing empty spots."""
        moves = []
        for r in range(self.n):
            for c in range(self.n):
                if self.board[r][c] == '.':
                    moves.append((r, c))
        return moves

    def make_move(self, row: int, col: int, marker: str) -> bool:
        """Applies a move if valid. Returns True if successful."""
        if 0 <= row < self.n and 0 <= col < self.n and self.board[row][col] == '.':
            self.board[row][col] = marker
            return True
        return False

    def check_winner(self) -> Optional[str]:
        """Returns the winner ('X' or 'O') if there is one, else None."""
        # horizontal, vertical, and diagonal checks
        n, k = self.n, self.k
        for r in range(n):
            for c in range(n):
                marker = self.board[r][c]
                if marker == '.':
                    continue
                # directions: (dr, dc)
                directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
                for dr, dc in directions:
                    count = 1
                    for i in range(1, k):
                        nr, nc = r + dr * i, c + dc * i
                        if 0 <= nr < n and 0 <= nc < n and self.board[nr][nc] == marker:
                            count += 1
                        else:
                            break
                    if count >= k:
                        return marker
        return None

    def is_draw(self) -> bool:
        """Returns True if the board is full and there's no winner."""
        if self.check_winner():
            return False
        return all(self.board[r][c] != '.' for r in range(self.n) for c in range(self.n))

    def reset(self):
        """Resets the board to its initial state."""
        self.board = [['.' for _ in range(self.n)] for _ in range(self.n)]
        self.current_turn = 'X'
