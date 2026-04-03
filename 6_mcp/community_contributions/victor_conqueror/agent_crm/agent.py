"""AgentCRM runner: CLI or `python agent.py --ui` for Gradio."""

import argparse
import asyncio
import os
from contextlib import AsyncExitStack

import gradio as gr
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv

from mcp_params import all_agentcrm_server_params
from paths import PACKAGE_DIR, REPO_ROOT
from prompts import sales_agent_instructions, user_task_prompt

load_dotenv(REPO_ROOT / ".env", override=False)
load_dotenv(PACKAGE_DIR / ".env", override=False)

MAX_TURNS = 35


async def run_agentcrm(
    rep_name: str,
    gmail_thread_id: str | None = None,
    account_hint: str | None = None,
    extra_context: str | None = None,
    model: str | None = None,
) -> str:
    params_list = all_agentcrm_server_params()
    model_name = model or os.getenv("AGENTCRM_MODEL", "gpt-4o-mini")

    async with AsyncExitStack() as stack:
        servers = [
            await stack.enter_async_context(
                MCPServerStdio(p, client_session_timeout_seconds=180)
            )
            for p in params_list
        ]
        agent = Agent(
            name="AgentCRM",
            instructions=sales_agent_instructions(rep_name),
            model=model_name,
            mcp_servers=servers,
        )
        prompt = user_task_prompt(rep_name, gmail_thread_id, account_hint, extra_context)
        result = await Runner.run(agent, prompt, max_turns=MAX_TURNS)
        return result.final_output or ""


def _gradio_brief(rep: str, thread: str, account: str, note: str, model: str) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        return "Set OPENAI_API_KEY in your `.env` file."
    rep = (rep or "").strip()
    if not rep:
        return "Enter rep name."
    return asyncio.run(
        run_agentcrm(
            rep_name=rep,
            gmail_thread_id=(thread or "").strip() or None,
            account_hint=(account or "").strip() or None,
            extra_context=(note or "").strip() or None,
            model=(model or "").strip() or None,
        )
    )


def _launch_ui() -> None:
    with gr.Blocks(title="AgentCRM") as ui:
        gr.Markdown("# AgentCRM\nCRM + optional Gmail & Calendar MCP.")
        with gr.Row():
            rep = gr.Textbox(label="Rep name", placeholder="Alex")
            account = gr.Textbox(label="Account (optional)", placeholder="Acme Corp")
        thread = gr.Textbox(label="Gmail thread id (optional)", placeholder="…")
        note = gr.Textbox(label="Extra context (optional)", lines=3)
        model = gr.Textbox(label="Model (optional)", placeholder="gpt-4o-mini")
        btn = gr.Button("Generate briefing", variant="primary")
        out = gr.Markdown()
        btn.click(fn=_gradio_brief, inputs=[rep, thread, account, note, model], outputs=[out])
    ui.launch(inbrowser=True)


async def _cli_main(args: argparse.Namespace) -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY in .env at repo root (or this folder).")
        return
    out = await run_agentcrm(
        rep_name=args.rep,
        gmail_thread_id=args.thread,
        account_hint=args.account,
        extra_context=args.note,
        model=args.model,
    )
    print(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="AgentCRM — context-aware sales assistant")
    parser.add_argument("--ui", action="store_true", help="Open Gradio instead of one-shot CLI")
    parser.add_argument("--rep", help="Sales rep name (required for CLI)")
    parser.add_argument("--thread", default=None, help="Gmail thread id")
    parser.add_argument("--account", default=None, help="Account / company hint")
    parser.add_argument("--note", default=None, help="Extra context")
    parser.add_argument("--model", default=None, help="Model override")
    args = parser.parse_args()

    if args.ui:
        _launch_ui()
        return
    if not args.rep:
        parser.error("--rep is required unless you use --ui")
    asyncio.run(_cli_main(args))


if __name__ == "__main__":
    main()
