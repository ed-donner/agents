#!/usr/bin/env python
import sys
import warnings
from trip_planner.crews.trip_planner.crew import TripPlanner
from trip_planner.crews.create_dashboard.crew import CreateDashboard
import os
from dotenv import load_dotenv
import time 

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

load_dotenv(override=True)

dashboard_requirements= """
        Create a trip planning dashboard. The dashboard should allow users to input trip source location, trip_start_date and trip_end_date, type of trip (domestic or international or both), destination weather (sunny, cold, snow), trip preferences.
        The dashboard should allow the user to submit these details using a submit button. Do not let user input anything other than the fields mentioned above.
    """
module_name= "trip_dashboard.py"
class_name= "TripDashboard"

def run():
    inputs={'dashboard_requirements': dashboard_requirements, 'module_name': module_name, 'class_name': class_name}
    CreateDashboard().crew().kickoff(inputs=inputs)

    print(os.getcwd())
    #Excecute app.py from terminal after CreateDashboard creates it.
    while True:
        if os.path.exists('output/events.jsonl'):
            with open('output/events.jsonl') as f:
                user_inputs = f.read().strip()
            time.sleep(4)

            if user_inputs:
                print(user_inputs)
                inputs={'user_inputs': user_inputs, 'module_name': module_name, 'class_name': class_name}
                TripPlanner().crew().kickoff(inputs=inputs)
                break;


if __name__=="__main__":
    run()