from pathlib import Path

import gradio as gr

from repo_onboarding_sidekick import (
    DEFAULT_SUCCESS_CRITERIA,
    RepoOnboardingSidekick,
    openrouter_model_label,
)

# Default to course repo root (agents/) when running from this folder layout
_DEFAULT_REPO = str(Path(__file__).resolve().parents[3])


async def setup(repo_path: str):
    root = (repo_path or "").strip() or _DEFAULT_REPO
    sidekick = RepoOnboardingSidekick()
    await sidekick.setup(root)
    return sidekick, f"**OpenRouter** · `{openrouter_model_label()}` · **Repo:** `{root}`"


async def process_message(sidekick, message, success_criteria, repo_path, history):
    root = (repo_path or "").strip() or _DEFAULT_REPO
    if getattr(sidekick, "repo_root", None) != root:
        await sidekick.setup(root)
    results = await sidekick.run_superstep(message, success_criteria, history)
    return results, sidekick


async def reset(repo_path: str):
    root = (repo_path or "").strip() or _DEFAULT_REPO
    agent = RepoOnboardingSidekick()
    await agent.setup(root)
    return "", DEFAULT_SUCCESS_CRITERIA, None, agent, f"Reset · **OpenRouter** · `{openrouter_model_label()}` · **Repo:** `{root}`"


def free_resources(sidekick):
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Cleanup: {e}")


with gr.Blocks(title="Repo onboarding Sidekick", theme=gr.themes.Default(primary_hue="teal")) as ui:
    gr.Markdown(
        "## Repo onboarding Sidekick\n"
        "Explores a **local** repository with read-only tools, then answers onboarding questions.\n\n"
        "Uses **OpenRouter** (`OPENROUTER_API_KEY`). Large repos may be slow to search."
    )
    sidekick = gr.State(delete_callback=free_resources)
    status = gr.Markdown(value="")

    repo_path = gr.Textbox(
        label="Repository path (absolute or ~)",
        value=_DEFAULT_REPO,
        placeholder="Path to clone or project root",
    )

    with gr.Row():
        chatbot = gr.Chatbot(label="Chat", height=380, type="messages")
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(
                show_label=False,
                placeholder="e.g. Where should I start if I want to add a new Sidekick tool?",
            )
        with gr.Row():
            success_criteria = gr.Textbox(
                label="Success criteria (optional)",
                value=DEFAULT_SUCCESS_CRITERIA,
                lines=6,
            )
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go", variant="primary")

    ui.load(setup, [repo_path], [sidekick, status])
    message.submit(
        process_message,
        [sidekick, message, success_criteria, repo_path, chatbot],
        [chatbot, sidekick],
    )
    go_button.click(
        process_message,
        [sidekick, message, success_criteria, repo_path, chatbot],
        [chatbot, sidekick],
    )
    reset_button.click(
        reset,
        [repo_path],
        [message, success_criteria, chatbot, sidekick, status],
    )


if __name__ == "__main__":
    ui.launch(inbrowser=True)
