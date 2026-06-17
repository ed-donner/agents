"""
Week 8 App — Code Agent UI
Paste a problem description + failing tests, watch the agent make them pass.
Run: python app.py
"""

import gradio as gr
from dotenv import load_dotenv
from code_agent import run_code_agent

load_dotenv(override=True)

DEFAULT_PROBLEM = """Write a function `is_palindrome(s: str) -> bool` that returns True
if the string is a palindrome (ignoring case and non-alphanumeric characters)."""

DEFAULT_TESTS = """def test_simple():
    assert is_palindrome("racecar") == True
    assert is_palindrome("hello") == False

def test_case_insensitive():
    assert is_palindrome("Racecar") == True

def test_with_spaces():
    assert is_palindrome("A man a plan a canal Panama") == True

def test_empty():
    assert is_palindrome("") == True
"""


def solve(problem: str, tests: str, model: str, max_iter: int, max_cost: float):
    log_lines = []

    class VerboseCapture:
        def write(self, msg):
            log_lines.append(msg)
        def flush(self):
            pass

    import sys
    old_stdout = sys.stdout
    sys.stdout = VerboseCapture()

    run = run_code_agent(
        problem=problem,
        tests=tests,
        max_iterations=int(max_iter),
        max_cost_usd=float(max_cost),
        model=model,
        verbose=True,
    )

    sys.stdout = old_stdout

    status = "✅ PASSED" if run.passed else "❌ FAILED"
    summary = (
        f"{status} — {run.iterations} iteration(s) — "
        f"${run.total_cost_usd:.4f} — {run.total_tokens} tokens"
    )
    log_text = "".join(log_lines)
    return run.solution, summary, log_text


with gr.Blocks(title="Week 8 — Code Agent") as demo:
    gr.Markdown("# Week 8: Code Agent\nDescribe what to build. Paste your tests. The agent writes code and fixes it until they pass.")

    with gr.Row():
        with gr.Column():
            problem_box = gr.Textbox(label="Problem description", value=DEFAULT_PROBLEM, lines=6)
            tests_box = gr.Textbox(label="pytest tests (no import needed)", value=DEFAULT_TESTS, lines=12)
            with gr.Row():
                model_dd = gr.Dropdown(
                    ["gpt-4o-mini", "gpt-4o", "claude-3-5-haiku-20241022"],
                    value="gpt-4o-mini",
                    label="Model",
                )
                max_iter = gr.Slider(1, 15, value=8, step=1, label="Max iterations")
                max_cost = gr.Slider(0.01, 2.0, value=0.50, step=0.01, label="Max cost ($)")
            run_btn = gr.Button("Run agent", variant="primary")
        with gr.Column():
            solution_box = gr.Code(label="Final solution", language="python", lines=20)
            status_box = gr.Textbox(label="Status")
            log_box = gr.Textbox(label="Agent log", lines=10)

    run_btn.click(
        solve,
        inputs=[problem_box, tests_box, model_dd, max_iter, max_cost],
        outputs=[solution_box, status_box, log_box],
    )

if __name__ == "__main__":
    demo.launch()
