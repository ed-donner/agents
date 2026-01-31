import argparse
from typing import Any

import gradio as gr
from dotenv import (
    find_dotenv,
    load_dotenv,
)
from .agent import run_agent
from .util import configure_logging


load_dotenv(find_dotenv(), override=True)


# Gradio chat interface function requires 2 parameters: message and history
# but history is managed by the OpenAI Agent SDK instead of Gradio
async def chat(message: str, history: Any) -> str:  # pylint: disable=unused-argument
    return await run_agent(message)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="OpenAI Agent SDK Tutorial Chat Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--log-file",
        "-l",
        type=str,
        help="Write logs to a file instead of the console",
    )
    args = parser.parse_args()
    if args.log_file:
        args.debug = True
    configure_logging(level="DEBUG" if args.debug else "INFO", log_file=args.log_file)
    gr.ChatInterface(chat).launch()


if __name__ == "__main__":
    main()
