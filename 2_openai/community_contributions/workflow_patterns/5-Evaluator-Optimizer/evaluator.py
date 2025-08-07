import asyncio
from typing import Any, Tuple

import gradio as gr
from agents import Agent, ItemHelpers, Runner, TResponseInputItem, trace
from build_agents import evaluator, exercise_generator
from rich.console import Console
from rich.markdown import Markdown
from schemas import EvaluationFeedback

console = Console()


async def main() -> None:
    msg: str = input("What kind of coding exercise would you like? ")
    input_items: list[TResponseInputItem] = [{"content": msg, "role": "user"}]

    latest_outline: str | None = None

    # We'll run the entire workflow in a single trace
    with trace("LLM as a judge"):
        while True:
            exercise_result = await Runner.run(
                exercise_generator,
                input_items,
            )

            input_items = exercise_result.to_input_list()
            latest_outline = ItemHelpers.text_message_outputs(exercise_result.new_items)
            print("Exercise generated")

            evaluator_result = await Runner.run(evaluator, input_items)
            result: EvaluationFeedback = evaluator_result.final_output

            print(f"Evaluator score: {result.score}")

            if result.score == "pass":
                print("Coding exercise is good enough, exiting.")
                break

            print("Re-running with feedback")

            input_items.append(
                {"content": f"Feedback: {result.feedback}", "role": "user"}
            )

    console.print(Markdown(f"Final exercise: {latest_outline}"))


if __name__ == "__main__":
    asyncio.run(main())
