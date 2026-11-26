import gradio as gr
import database
from config import LINKEDIN_URL, NAME, SHOW_ADMIN_TAB
from twin import Twin

EXAMPLES = [
    "¿Podría resumir su experiencia profesional?",
    "¿Qué herramientas de automatización de pruebas utiliza?",
    "What certifications do you hold?",
    "¿Está disponible para trabajar en modalidad remota?",
]

CSS = """
footer { display: none !important; }
.gradio-container { max-width: 900px !important; margin: 0 auto !important; }
"""

DESCRIPTION = f"""
# {NAME} | Digital Twin

Converse con el gemelo digital de IA de **{NAME}**, QA Engineer, sobre su trayectoria profesional.
Las respuestas se basan en su [perfil de LinkedIn]({LINKEDIN_URL}) y en una base de conocimientos verificada.
Cada respuesta es revisada por un agente evaluador antes de mostrarse, para evitar información inventada.
"""

twin = Twin()


def load_tables():
    return (
        database.fetch_rows("faq"),
        database.fetch_rows("unknown_questions"),
        database.fetch_rows("contacts"),
    )


with gr.Blocks(title=f"{NAME} | Digital Twin") as demo:
    gr.Markdown(DESCRIPTION)

    with gr.Tab("Chat"):
        review = gr.Markdown("The evaluator's review of the last reply will appear here.", render=False)
        gr.ChatInterface(
            twin.chat,
            additional_outputs=[review],
            examples=EXAMPLES,
            chatbot=gr.Chatbot(height=480, show_label=False),
        )
        with gr.Accordion("Evaluator review of the last reply", open=False):
            review.render()

    if SHOW_ADMIN_TAB:
        with gr.Tab("Database"):
            refresh = gr.Button("Refresh")
            gr.Markdown("### FAQ (approved answers)")
            faq_table = gr.Dataframe(headers=["Question", "Answer", "Times used", "Created"], interactive=False, wrap=True)
            gr.Markdown("### Unanswered questions")
            unknown_table = gr.Dataframe(headers=["Question", "Created"], interactive=False, wrap=True)
            gr.Markdown("### Contacts")
            contacts_table = gr.Dataframe(headers=["Email", "Name", "Notes", "Created"], interactive=False, wrap=True)
            tables = [faq_table, unknown_table, contacts_table]
            refresh.click(load_tables, outputs=tables)
            demo.load(load_tables, outputs=tables)


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(), css=CSS)
