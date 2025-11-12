#!/usr/bin/env python
import sys
import warnings
import time
from datetime import datetime

from tdd_qa_engineering_team.crew import TddQaEngineeringTeam

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """

    # copy_contexts()
    with open(f"output/user_stories.md", "r", encoding="utf-8") as f:
        user_stories = f.read()    

    with open(f"output/requirements_analysis.md", "r", encoding="utf-8") as f:
        requirements_analysis = f.read()    

    with open(f"output/DOM_elements.txt", "r", encoding="utf-8") as f:
        dom_elements = f.read()    
        
    with open(f"output/testcases.md", "r", encoding="utf-8") as f:
        test_cases = f.read()                    

    inputs = {
        'user_stories': user_stories,
        'application_url': 'http://127.0.0.1:7860',
        'requirements_analysis': requirements_analysis,
        'dom_elements': dom_elements,
        'test_cases': test_cases,
        'time_stamp': int(time.time()),
    }

    try:
        TddQaEngineeringTeam().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

def copy_file(dest_path: str, src_path: str):
    """
    Copy a file from src_path to dest_path.
    """
    try:
        with open(src_path, "r", encoding="utf-8") as src_file:
            content = src_file.read()
        with open(dest_path, "w", encoding="utf-8") as dest_file:
            dest_file.write(content)
    except Exception as e:
        raise Exception(f"An error occurred while copying file from {src_path} to {dest_path}: {e}")

def copy_contexts():
    """
    Copy context files from tdd_engineering_team to tdd_qa_engineering_team.
    """
    context_files = [
        "user_stories.md",
        "requirements_analysis.md"
    ]
    for file_name in context_files:
        copy_file(
            dest_path=f"/home/anhdanghoang/projects/agents/3_crew/community_contributions/adh_crew_labs/tdd_qa_engineering_team/output/{file_name}",
            src_path=f"/home/anhdanghoang/projects/agents/3_crew/community_contributions/adh_crew_labs/tdd_engineering_team/output/{file_name}"
        )