"""Main application file for the Tic-Tac-Toe game."""

import gradio as gr
from autogen_core import SingleThreadedAgentRuntime, AgentId
import game_engine
import messages
import agents

# Global game state
engine = None
runtime = None
agent_id = None


async def init_game(n, k, difficulty):
    """Initialize the game and register the AI agent."""
    global engine, runtime, agent_id
    engine = game_engine.TicTacToeEngine(n, k)
    runtime = SingleThreadedAgentRuntime()
    
    agent_name = "TicTacToeAI"
    await agents.TicTacToeAgent.register(
        runtime, 
        agent_name,
        lambda: agents.TicTacToeAgent(agent_name, difficulty)
    )
    runtime.start()
    agent_id = AgentId(agent_name, "default")
    return engine.get_board_string(), f"Game started! Grid: {n}x{n}, Win: {k}. Your turn (X)."


def ui():
    """Create the Gradio UI for the Tic-Tac-Toe game."""
    MAX_N = 10
    with gr.Blocks(title="AutoGen Tic-Tac-Toe", css=".board-btn { min-width: 50px; height: 50px; font-size: 20px; font-weight: bold; }") as demo:
        gr.Markdown("# 🕹️ AutoGen Tic-Tac-Toe")
        gr.Markdown("Play against an AI agent powered by AutoGen and OpenRouter.")
        
        with gr.Row():
            n_input = gr.Number(value=3, label="Grid Size (n, max 10)", precision=0)
            k_input = gr.Number(value=3, label="Win Count (k)", precision=0)
            diff_input = gr.Dropdown(choices=["easy", "medium", "hard"], value="hard", label="Difficulty")
            start_btn = gr.Button("Start Game", variant="primary")
            
        status_display = gr.Textbox(label="Status", value="Configure and Start the game!", interactive=False)
        
        # Board Grid
        buttons = []
        with gr.Column(visible=False) as board_container:
            for r in range(MAX_N):
                with gr.Row():
                    row_buttons = []
                    for c in range(MAX_N):
                        btn = gr.Button(".", elem_classes="board-btn", visible=False)
                        row_buttons.append(btn)
                    buttons.append(row_buttons)

        async def start_game_ui(n, k, difficulty):
            """Start the game when the start button is clicked."""
            n = int(min(n, MAX_N))
            board_str, status = await init_game(n, k, difficulty)
            
            updates = [gr.update(visible=True)] # For board_container
            for r in range(MAX_N):
                for c in range(MAX_N):
                    if r < n and c < n:
                        updates.append(gr.update(value=".", visible=True, interactive=True))
                    else:
                        updates.append(gr.update(visible=False))
            updates.append(status)
            return updates

        async def make_move_ui(r, c):
            """Handle a move made by the human/AI player."""
            # human move
            if engine is None:
                yield [gr.update() for _ in range(MAX_N * MAX_N)] + ["Please start the game first!"]
                return

            if not engine.make_move(r, c, 'X'):
                yield [gr.update() for _ in range(MAX_N * MAX_N)] + ["Invalid move!"]
                return

            # update ui
            def get_updates(status):
                ups = []
                for row in range(MAX_N):
                    for col in range(MAX_N):
                        if row < engine.n and col < engine.n:
                            val = engine.board[row][col]

                            # disable if not empty or game over
                            inter = (val == '.' and "wins" not in status.lower() and "draw" not in status.lower())
                            ups.append(gr.update(value=val, interactive=inter))
                        else:
                            ups.append(gr.update(visible=False))
                return ups + [status]

            yield get_updates("AI is thinking...")

            # check if human won
            winner = engine.check_winner()
            if winner:
                yield get_updates(f"Player {winner} wins!")
                return
            if engine.is_draw():
                yield get_updates("It's a draw!")
                return

            # ai move
            try:
                board_str = engine.get_board_string()
                valid_moves = str(engine.get_valid_moves())
                msg = messages.TicTacToeMessage(content="Your move", board=board_str, valid_moves=valid_moves, turn="O")
                
                response = await runtime.send_message(msg, agent_id)
                move_parts = response.content.split(',')
                a_row, a_col = int(move_parts[0]), int(move_parts[1])
                
                engine.make_move(a_row, a_col, 'O')
                
                winner = engine.check_winner()

                if winner:
                    yield get_updates(f"Player {winner} (AI) wins!")
                elif engine.is_draw():
                    yield get_updates("It's a draw!")
                else:
                    yield get_updates(f"AI played ({a_row}, {a_col}). Your turn.")
            except Exception as e:
                yield get_updates(f"AI Error: {str(e)}")

        # start button
        start_btn.click(
            fn=start_game_ui,
            inputs=[n_input, k_input, diff_input],
            outputs=[board_container] + [btn for row in buttons for btn in row] + [status_display]
        )
        
        # board buttons
        for r in range(MAX_N):
            for c in range(MAX_N):

                def create_handler(row, col):
                    async def handler():
                        async for val in make_move_ui(row, col):
                            yield val
                    return handler
                
                buttons[r][c].click(
                    fn=create_handler(r, c),
                    outputs=[btn for row in buttons for btn in row] + [status_display]
                )
        
    return demo

if __name__ == "__main__":
    demo = ui()
    demo.launch()
