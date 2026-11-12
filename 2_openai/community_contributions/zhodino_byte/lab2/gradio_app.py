import gradio as gr

from agent_service import run_agent

with gr.Blocks() as demo:
    gr.Markdown("# Sales Manager Agent")

    prompt = gr.Textbox(
        label="Задание",
        lines=8,
        placeholder="Введите задание для агента",
    )

    submit = gr.Button("Запустить")
    output = gr.Textbox(label="Результат", lines=15)

    submit.click(
        fn=run_agent,
        inputs=prompt,
        outputs=output,
        concurrency_limit=1,
    )


if __name__ == "__main__":
    demo.queue().launch(
        server_name="127.0.0.1",
    )
