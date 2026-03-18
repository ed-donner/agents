"""Gradio app to test the ARES Architect Agent."""

import asyncio
import gradio as gr
from dotenv import load_dotenv
from agents import Runner
from ares_agents import architect_agent

load_dotenv()


def run_architect(query: str) -> str:
    """Run the Research Architect agent and display the plan."""
    if not query.strip():
        return "Please enter a research query."

    result = asyncio.run(Runner.run(architect_agent, input=query))
    plan = result.final_output
    parts: list[str] = [
        f"# {plan.original_query}\n",
        f"**Strategy:** {plan.summary}\n",
        "---\n",
    ]
    for i, task in enumerate(plan.tasks, 1):
        parts.append(
            f"### Task {i}: {task.title}\n"
            f"- **Query:** {task.query}\n"
            f"- **Goal:** {task.goal}\n"
        )

    return "\n".join(parts)


demo = gr.Interface(
    fn=run_architect,
    inputs=gr.Textbox(
        label="Research Query",
        placeholder="e.g. Analyze the impact of AI on healthcare diagnostics",
    ),
    outputs=gr.Markdown(label="Research Plan"),
    title="ARES — Architect Agent Test",
    description="Generate a structured research plan from your query.",
)

if __name__ == "__main__":
    demo.launch()
