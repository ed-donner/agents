"""
Gradio UI for the AI Sidekick personal co-worker agent.
"""

import gradio as gr

from .graph import Graph


class App:
    def __init__(self, title: str = "Sidekick", theme: str = "emerald"):
        self.title = title
        self.theme = theme
        self.ui = self._build_ui()

    def _build_ui(self) -> gr.Blocks:
        """
        Build and wire up the Gradio interface.
        """
        theme = gr.themes.Default(primary_hue=self.theme)
        with gr.Blocks(title=self.title, theme=theme) as ui:
            gr.Markdown("## Sidekick Personal Co-Worker")
            sidekick = gr.State(delete_callback=self._free_resources)

            with gr.Row():
                chatbot = gr.Chatbot(label="Sidekick", height=300, type="messages")
            with gr.Group():
                with gr.Row():
                    message = gr.Textbox(
                        show_label=False, placeholder="Your request to the Sidekick"
                    )
                with gr.Row():
                    success_criteria = gr.Textbox(
                        show_label=False,
                        placeholder="What are your success criteria?",
                    )
            with gr.Row():
                reset_button = gr.Button("Reset", variant="stop")
                go_button = gr.Button("Go!", variant="primary")

            ui.load(self._setup, [], [sidekick])
            message.submit(
                self._process_message,
                [sidekick, message, success_criteria, chatbot],
                [chatbot, sidekick],
            )
            success_criteria.submit(
                self._process_message,
                [sidekick, message, success_criteria, chatbot],
                [chatbot, sidekick],
            )
            go_button.click(
                self._process_message,
                [sidekick, message, success_criteria, chatbot],
                [chatbot, sidekick],
            )
            reset_button.click(
                self._reset, [], [message, success_criteria, chatbot, sidekick]
            )

        return ui

    async def _setup(self):
        """
        Initialize the sidekick graph on UI load.
        """
        sidekick = Graph()
        await sidekick.setup()
        return sidekick

    async def _process_message(self, sidekick, message, success_criteria, history):
        """
        Handle user message submission.
        """
        results = await sidekick.run_superstep(
            message, success_criteria, history
        )
        return results, sidekick

    async def _reset(self):
        """
        Reset the conversation and create a new sidekick instance.
        """
        new_sidekick = Graph()
        await new_sidekick.setup()
        return "", "", None, new_sidekick

    def _free_resources(self, sidekick):
        """
        Clean up resources when the sidekick state is discarded.
        """
        print("Cleaning up")
        try:
            if sidekick:
                sidekick.cleanup()
        except Exception as e:
            print(f"Exception during cleanup: {e}")

    def launch(self, **kwargs):
        """
        Launch the Gradio interface.
        """
        self.ui.launch(**kwargs)


if __name__ == "__main__":
    app = App()
    app.launch(inbrowser=True)
