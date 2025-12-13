#!/usr/bin/env python
import sys
import warnings
import os
from datetime import datetime

from engineering_team.crew import EngineeringTeam

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

requirements= """
A web page language validation system.
The system should allow users to input a list of web pages (URLs starting with https://).
The system should fetch the HTML content of each page and extract the visible text.
The system should detect the language of the page text.
The system should compare the detected language with the language specified in the HTML <html lang=""> attribute.
The system should highlight pages where the detected language does not match the HTML lang attribute.
The system should provide a dashboard that shows:
    - The total number of links checked
    - The percentage of pages with matching languages
    - The percentage of pages with mismatched languages
The system should allow users to see details of each page, including URL, detected language, HTML lang attribute, and whether it matches.
The system should handle network errors gracefully and report pages that cannot be fetched.
The system should support basic input validation to ensure only valid HTTPS URLs are processed.
"""
modules = [
    {"module_name": "dashboard", "class_name": "Dashboard"},
    {"module_name": "page_input", "class_name": "PageInput"}
]


def run():
    """
    Run the research crew.
    """
    inputs = {
        'requirements': requirements,
        'modules': modules
    }

    # Create and run the crew
    result = EngineeringTeam().crew().kickoff(inputs=inputs)


if __name__ == "__main__":
    run()