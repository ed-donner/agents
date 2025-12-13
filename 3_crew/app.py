import gradio as gr

def run_app_flow(input):
    return input

with gr.Blocks() as demo:
    with gr.Tab('App Requirements'):
        textbox = gr.Textbox(placeholder="Please enter app requirements")
        button = gr.Button('Create app files')
        textbox_output=gr.Textbox(placeholder="Please enter app requirements")
        button.click(fn=run_app_flow, inputs=[textbox], outputs=[textbox_output])


demo.launch()
