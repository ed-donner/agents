#!/usr/bin/env python
import sys
import warnings

from homepage_builder.crew import ResearcherCrew, ScraperCrew, BuildAndReviewCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def _run_pipeline(inputs):
    # Step 1: Research – find N businesses
    research_result = ResearcherCrew().crew().kickoff(inputs=inputs)

    if not research_result.pydantic:
        raise Exception("Researcher crew failed to return pydantic output.")

    businesses = research_result.pydantic.businesses
    business_dicts = [{"name": b.name, "url": b.url, "sector": b.sector} for b in businesses]

    print(f"Found {len(business_dicts)} businesses. Scraping each website...")

    # Step 2: Scrape – visit each business website in parallel workers via kickoff_for_each
    ScraperCrew().crew().kickoff_for_each(inputs=business_dicts)

    print("Scraping done. Running build + review pipeline for each business...")

    # Step 3: Build, review, and amend – one unified hierarchical crew per business
    result = BuildAndReviewCrew().crew().kickoff_for_each(inputs=business_dicts)
    return result


def run():
    """
    Run the crew.
    """
    inputs = {
        'number_of_businesses': '<Number of local businesses to find>',
        'geographical_area': '<Geographical area to search for businesses>'
    }

    try:
        _run_pipeline(inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        'number_of_businesses': 3,
        'geographical_area': 'San Francisco'
    }
    try:
        ResearcherCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        ResearcherCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        'number_of_businesses': 3,
        'geographical_area': 'San Francisco'
    }

    try:
        ResearcherCrew().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        'number_of_businesses': 3,
        'geographical_area': 'San Francisco'
    }

    try:
        result = _run_pipeline(inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
