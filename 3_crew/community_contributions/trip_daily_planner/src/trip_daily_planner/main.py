#!/usr/bin/env python
import os
import warnings

from datetime import datetime

from crew import TripDailyPlanner

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

os.makedirs('output', exist_ok=True)

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        'destination': 'Kraków, KRK',
        'dining_preferences_restrictions': 'No restriction',
        'personal_interests': 'Enjoy historic and cultural sites. An out-of-town day trip is fine. Include biking activities in one of days', 
        'hotel_location': 'Kraków Old Town',
        'flight_information': 'LH 1623, leaving at May 16nd, 2026, 13:20',
        'trip_duration': '4 days',
        'email_to': 'user@example.com',
    }
    
    try:
        TripDailyPlanner().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

def run_with_inputs(inputs):
    """
    Run the crew with the inputs.
    """
    try:
        TripDailyPlanner().crew().kickoff(inputs=inputs)
       
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")
