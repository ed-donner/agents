"""Gradio app for BudgetBuy AI."""

from __future__ import annotations

import os

import gradio as gr
from dotenv import load_dotenv

from manager import BudgetBuyManager

load_dotenv(override=True)


async def run_budgetbuy(
    request: str,
    budget_ngn: int,
    email: str,
    push_enabled: bool,
):
    if not request.strip():
        yield "Enter your shopping request."
        return
    if not os.environ.get("OPENAI_API_KEY"):
        yield "Set `OPENAI_API_KEY` in your environment or `.env` file."
        return

    lines: list[str] = []
    async for chunk in BudgetBuyManager().run(
        user_request=request.strip(),
        budget_ngn=int(budget_ngn),
        email=email.strip(),
        push_enabled=bool(push_enabled),
    ):
        if chunk.startswith("[status] "):
            lines.append(chunk.removeprefix("[status] "))
        else:
            lines.append("---\n\n" + chunk)
        yield "\n\n".join(lines)


with gr.Blocks(title="BudgetBuy AI", theme=gr.themes.Default(primary_hue="green")) as ui:
    gr.Markdown(
        "# BudgetBuy AI (Gadgets)\n\n"
        "Agentic gadget shopping assistant: **Planner -> Research -> Comparison**.\n\n"
        "Example:\n"
        "`I need the best gaming laptop for coding and light video editing.`"
    )
    request = gr.Textbox(
        label="Which gadget do you want to buy?",
        placeholder="Describe the gadget, usage, and must-haves.",
        lines=3,
    )
    budget = gr.Number(label="Budget (NGN)", value=2700000, precision=0)
    email = gr.Textbox(
        label="Notify email (optional)",
        placeholder="you@example.com",
    )
    push = gr.Checkbox(label="Send push notification", value=False)
    run = gr.Button("Find best option", variant="primary")
    output = gr.Markdown(label="Result")

    run.click(
        fn=run_budgetbuy,
        inputs=[request, budget, email, push],
        outputs=output,
    )
    request.submit(
        fn=run_budgetbuy,
        inputs=[request, budget, email, push],
        outputs=output,
    )

if __name__ == "__main__":
    ui.launch(inbrowser=True)

