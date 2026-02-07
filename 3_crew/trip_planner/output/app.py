import gradio as gr
import json

class TripDashboard:
    def __init__(self):
        self.trips = []

    def submit_trip(self, source_location, trip_start_date, trip_end_date, trip_type, destination_weather, trip_preferences):
        trip = {
            "source_location": source_location,
            "trip_start_date": trip_start_date,
            "trip_end_date": trip_end_date,
            "trip_type": trip_type,
            "destination_weather": destination_weather,
            "trip_preferences": trip_preferences
        }
        
        self.trips.append(trip)
        self.log_event(trip)
        return "Trip submitted successfully!", trip

    def log_event(self, trip):
        with open('events.jsonl', 'a') as f:
            json.dump(trip, f)
            f.write('\n')

def create_dashboard():
    dashboard = TripDashboard()
    
    with gr.Blocks() as demo:
        gr.Markdown("### Trip Planning Dashboard")
        
        source_location = gr.Textbox(label="Trip Source Location", placeholder="Enter your source location")
        trip_start_date = gr.Textbox(label="Trip Start Date", placeholder="YYYY-MM-DD")
        trip_end_date = gr.Textbox(label="Trip End Date", placeholder="YYYY-MM-DD")
        trip_type = gr.Radio(label="Type of Trip", choices=["Domestic", "International", "Both"])
        destination_weather = gr.Radio(label="Destination Weather", choices=["Sunny", "Cold", "Snow"])
        trip_preferences = gr.Textbox(label="Trip Preferences", placeholder="Enter your preferences")

        submit_btn = gr.Button("Submit")
        output = gr.Textbox(label="Output", interactive=False)

        def submit_callback(source_location, trip_start_date, trip_end_date, trip_type, destination_weather, trip_preferences):
            return dashboard.submit_trip(source_location, trip_start_date, trip_end_date, trip_type, destination_weather, trip_preferences)

        submit_btn.click(fn=submit_callback, inputs=[source_location, trip_start_date, trip_end_date, trip_type, destination_weather, trip_preferences], outputs=output)

    demo.launch()

if __name__ == "__main__":
    create_dashboard()