import gradio as gr
from dotenv import load_dotenv
from main import run_with_inputs

load_dotenv(override=True)


def run(destination_textbox, flight_textbox, hotel_textbox, trip_duration_textbox, 
    personal_interests_textbox, dining_preferences_restrictions_textbox, email_textbox):
    trip_inputs = {
        'destination': destination_textbox,
        'flight_information': flight_textbox,
        'hotel_location': hotel_textbox,
        'trip_duration': trip_duration_textbox,
        'personal_interests': personal_interests_textbox,
        'dining_preferences_restrictions': dining_preferences_restrictions_textbox, 
        'email_to': email_textbox
    }
    yield "AI Assists trip planning with 'personalized activity planner' and 'restaurant scout'.  It might take 3-5 minutes....."
    out = run_with_inputs(trip_inputs)
    yield f"##### Task Completed and email was sent to {email_textbox} ####"


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Daily Planner Personalizing Your Trip")
    gr.Markdown("#### The result will be output at the bottom of markdown area.")

    with gr.Row(scale=5):
        with gr.Column(scale=3):
            destination_textbox = gr.Textbox(label="Your trip destination with the airport code:")
        with gr.Column(scale=2):
            flight_textbox = gr.Textbox(label="Your departing flight, date and time:")
    with gr.Row(scale=5):
        with gr.Column(scale=3):
            hotel_textbox = gr.Textbox(label="Hotel location:")
        with gr.Column(scale=2):
            trip_duration_textbox = gr.Textbox(label="Trip duration:")

    personal_interests_textbox = gr.Textbox(label="""
    What are you interested at: historic, cultural or pop sites? The level of physical activities?
    How far are you willing to travel to? Be more specific.
    """)
    dining_preferences_restrictions_textbox = gr.Textbox(label="Any dining restrictions or preferences?")
    email_textbox = gr.Textbox(label="Your email address:", type="email")

    run_button = gr.Button("Submit", variant="primary")
    report = gr.Markdown(label="Daily planner output")
    run_button.click(fn=run, inputs=[destination_textbox, flight_textbox, hotel_textbox, trip_duration_textbox, 
    personal_interests_textbox, dining_preferences_restrictions_textbox, email_textbox], outputs=report)

ui.launch(inbrowser=True)

