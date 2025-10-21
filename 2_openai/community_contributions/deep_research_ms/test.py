import gradio as gr

def process_data(name, age):
    """Function that returns multiple values to update multiple components"""
    
    # Generate different outputs
    greeting = f"Hello, {name}!"
    status = f"Processing complete for {name}, age {age}"
    category = "Adult" if int(age) >= 18 else "Minor"
    summary = f"{name} is {age} years old and is classified as: {category}"
    
    # Return tuple of values - one for each output component
    return greeting, status, category, summary

with gr.Blocks() as demo:
    gr.Markdown("# Multiple Component Update Example")
    
    with gr.Row():
        with gr.Column():
            name_input = gr.Textbox(label="Name", placeholder="Enter your name")
            age_input = gr.Number(label="Age", value=25)
            submit_btn = gr.Button("Submit")
        
        with gr.Column():
            greeting_output = gr.Textbox(label="Greeting")
            status_output = gr.Textbox(label="Status")
            category_output = gr.Textbox(label="Category")
            summary_output = gr.Textbox(label="Summary")
    
    # Click event that updates multiple components
    # The outputs list corresponds to the return values from the function
    submit_btn.click(
        fn=process_data,
        inputs=[name_input, age_input],
        outputs=[greeting_output, status_output, category_output, summary_output]
    )


demo.launch()