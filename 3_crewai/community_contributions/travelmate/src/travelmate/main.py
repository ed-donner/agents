import sys
import warnings
from datetime import datetime
from travelmate.crew import Travelmate
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Run the crew.
    """
    inputs = {
        'location': 'Zermatt,Switzerland',
        'current_year': str(datetime.now().year),
        'typeOfTourism': 'adventurous'
    }
    
    try:
        Travelmate().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")
