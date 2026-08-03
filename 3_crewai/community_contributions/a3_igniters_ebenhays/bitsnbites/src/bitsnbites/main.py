#!/usr/bin/env python
import sys
import warnings
import random
from datetime import datetime
from bitsnbites.crew import Bitsnbites

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the crew.
    """
    inputs = {
        "country": random.choice(
            [
                "Ghana",
                "Nigeria",
                "Kenya",
                "South Africa",
                "Egypt",
                "Rwanda",
                "Tanzania",
                "Uganda",
                "Zimbabwe",
                "Malawi",
                "Mozambique",
                "Angola",
                "Zambia",
                "Namibia",
                "Botswana",
                "Swaziland",
                "Lesotho",
            ]
        ),
        "current_year": str(datetime.now().year),
    }

    try:
        Bitsnbites().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")
