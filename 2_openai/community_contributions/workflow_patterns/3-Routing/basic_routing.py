import asyncio

from agents import (
    InputGuardrailTripwireTriggered,
    Runner,
    RunResult,
    TResponseInputItem,
    trace,
)
from build_agents import routing_agent
from rich.console import Console
from rich.markdown import Markdown

# from IPython.display import Markdown, display

console = Console()


async def main() -> None:
    history: list[TResponseInputItem] = []
    print("\n" + "-" * 72)
    print("Welcome to Code Tutor! Ask me anything about Python, JavaScript, or SQL.")
    print("Type 'quit' or 'exit' to end the conversation.")
    print("-" * 72)

    while True:
        message_str: str = input("\nYou: ")
        if not message_str or message_str.lower() in ["quit", "exit", "thanks", "bye"]:
            print("\nAssistant: Goodbye!")
            break

        current_input = history + [{"role": "user", "content": message_str}]

        with trace(workflow_name="Coding tutor routing"):
            try:
                result: RunResult = await Runner.run(
                    starting_agent=routing_agent,
                    input=current_input,
                )
            except InputGuardrailTripwireTriggered as e:
                print("INFO | Guardrail | check_if_on_topic | Tripwire triggered!")
                error_message = e.guardrail_result.output.output_info[
                    "Found_Unexpected_Message"
                ].clarification_message
                print(f"INFO | {error_message}")
                continue

        print("\n")
        print("-" * 10)
        print("Assistant:")
        print("-" * 10)
        console.print(Markdown(markup=result.final_output))
        history = result.to_input_list()
        # print(f"\nINFO | Message History: {history}")


if __name__ == "__main__":
    asyncio.run(main())
