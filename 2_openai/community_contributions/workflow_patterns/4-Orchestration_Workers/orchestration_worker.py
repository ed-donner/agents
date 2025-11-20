import asyncio
from typing import Any, Tuple

import gradio as gr
from agents import (
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    Runner,
    RunResult,
    TResponseInputItem,
    gen_trace_id,
    trace,
)
from build_agents import planner_agent, routing_agent, search_agent, writer_agent
from rich.console import Console
from rich.markdown import Markdown

console = Console()


class ResearchManager:
    # The run method now assumes the query is pre-validated.
    async def run(self, query: str) -> str:
        """
        Runs the full research process on a pre-validated query.
        Returns a markdown string of the report.
        """
        # This trace block covers the actual research, not the validation.
        with trace(workflow_name="Research trace"):
            # Step 1: Proceed directly to planning. The topic check is done outside.
            plan: list[dict] = await self._plan_searches(query=query)
            results = await self._perform_searches(plan)
            report = await self._write_report(query, results)

            return report.markdown_report

    # This method will be called from the main loop and checks the validity of the query.
    async def _topic_check(self, query: str) -> Tuple[bool, str]:
        """
        Checks if the query is on-topic.
        Returns (True, query) on success.
        Returns (False, clarification_message) on failure.
        """
        try:
            # The input must be in the chat history format for the guardrail.
            formatted_input = [{"role": "user", "content": query}]
            await Runner.run(starting_agent=routing_agent, input=formatted_input)

            # If the guardrail does NOT trigger an exception, the topic is on.
            return (True, query)

        except InputGuardrailTripwireTriggered as e:
            print("INFO | Guardrail | Topic check tripwire triggered.")

            try:
                clarification_msg = e.guardrail_result.output.output_info[
                    "Found_Unexpected_Message"
                ].clarification_message
            except (AttributeError, KeyError):
                # If the expected structure isn't there, just use the default message.
                print(
                    "INFO | Guardrail | Could not extract specific message, using default."
                )
                clarification_msg = "Your request seems to be off-topic."

            # print(f"INFO | Guardrail | Clarification message: {clarification_msg}")
            return (False, clarification_msg)

    async def _plan_searches(self, query: str):
        result = await Runner.run(planner_agent, f"Query: {query}")
        print(f"INFO | Planning result: {result.final_output.searches}")
        return result.final_output.searches

    async def _perform_searches(self, searches: list):
        print(f"INFO | Performing searches")
        tasks = [asyncio.create_task(self._search(item)) for item in searches]
        summaries = await asyncio.gather(*tasks)
        # print(f"INFO | Search results: {summaries}")
        return summaries

    async def _search(self, item: Any) -> str:
        print(f"INFO | - Searching for: {item.query}")
        res = await Runner.run(search_agent, item.query)
        return res.final_output

    async def _write_report(self, query: str, summaries: list[str]) -> Any:
        print(f"INFO | Writing report for query: {query}")
        joined = "\n".join(summaries)
        output = await Runner.run(
            writer_agent, f"Original query: {query}\nResearch:\n{joined}"
        )
        return output.final_output


async def main() -> None:
    history: list[TResponseInputItem] = []
    print("\n" + "-" * 98)
    print(
        "Welcome to Coding Syllabus Generator! Ask me to generate syllabi about Python, JavaScript, or SQL."
    )
    print("Type 'quit' or 'exit' to end the conversation.")
    print("-" * 98)

    # Instantiate the manager once, outside the loop.
    manager = ResearchManager()

    while True:
        message_str: str = input("\nYou: ")
        if not message_str or message_str.lower() in ["quit", "exit", "thanks", "bye"]:
            print("\nAssistant: Goodbye!")
            break

        # The validation logic is here in the main loop.
        final_result_string = ""
        try:
            # Step 1: Check if the topic is valid.
            is_on_topic, check_result = await manager._topic_check(query=message_str)

            # Step 2: If the topic is not valid, print the clarification and continue the loop.
            if not is_on_topic:
                # The 'check_result' is the clarification_message in this case.
                final_result_string = check_result
            else:
                # Step 3: If the topic IS valid, run the full research process.
                print("\nINFO | Topic is valid. Starting research...")
                # The 'check_result' is the original query here, but we can just use message_str.
                final_result_string = await manager.run(query=message_str)

        except Exception as e:
            # General error handling for the entire process
            final_result_string = f"An unexpected error occurred: {e}"
            # print(f"ERROR | {final_result_string}")

        # This block now prints either the final report or the clarification message.
        print("\n" + "-" * 10)
        print("Assistant:")
        print("-" * 10)
        console.print(Markdown(markup=final_result_string))


if __name__ == "__main__":
    asyncio.run(main())
