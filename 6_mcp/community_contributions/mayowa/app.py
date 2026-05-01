from typing import List
import gradio as gr
from dotenv import load_dotenv

load_dotenv(override=True)

from clarifier import Clarifier
from research_manager import ResearchManager


class App:
    def __init__(self):
        self.init_agents()


    def init_agents(self) -> None:
        self.clarifier = Clarifier()


    async def handle_user_input(self, query: str, history: List[gr.ChatMessage]):
        if self.clarifier.questions is None:
            await self.clarifier.run(query)

            if self.clarifier.exception:
                yield self.clarifier.exception, gr.skip()
                self.init_agents()
                return

            self.research_manager = ResearchManager(
                query=query,
                clarifying_questions=list(self.clarifier.questions),
            )
            yield self.clarifier.questions.popleft(), "Clarifying questions started (1/3)."
            return

        self.clarifier.answers.append(query)

        if len(self.clarifier.answers) < 3:
            yield self.clarifier.questions.popleft(), f'Clarifying answer recorded ({len(self.clarifier.answers)}/3).'
            return

        self.research_manager.clarifying_answers = list(self.clarifier.answers)

        yield "All clarifying questions answered. Starting research...", "Please wait while we perform the research..."

        status_response = ""
        chat_response = ""

        try:
            async for chunk in self.research_manager.run():
                if chunk["type"] == "report":
                    yield '', chunk["content"]
                else:
                    if chunk['type'] == "status":
                        status_response = status_response + "\n" + chunk['content']
                        yield '', status_response
                    elif chunk['type'] == "chat":
                        chat_response = chat_response + "\n" + chunk['content']
                        yield chat_response, gr.skip()
        except Exception as exc:
            yield f"Research failed: {exc}", status_response
            self.init_agents()
            return

        yield chat_response + "\nResearch complete. The report is shown below.\nFeel free to research another topic.", gr.skip()
        self.init_agents()


    def run(self) -> None:
        with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
            refresh_trigger = gr.State(0)

            @gr.render(inputs=refresh_trigger)
            def render_chat_interface(_count):
                gr.ChatInterface(
                    fn=self.handle_user_input,
                    additional_outputs=[status],
                    title="Deep Research with MCP",
                    description="What topic would you like to research?",
                    examples=[
                        "What are the effects of AI on the software engineering industry?",
                        "What are the differences between a DevOps engineer and a software engineer?",
                    ],
                    type="messages",
                )

            button = gr.Button("Restart", variant="secondary")
            button.click(lambda x: x + 1, refresh_trigger, refresh_trigger)
            button.click(fn=self.init_agents)

            status = gr.Markdown("Report", label="Status")

            ui.launch()


app = App()

if __name__ == "__main__":
    app.run()
