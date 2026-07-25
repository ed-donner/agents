#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from interview.crew import Interview

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Run the crew. All candidates answer the SAME questions, then the interviewer
    compares them and recommends which candidate to hire.
    """
    company_name = "Microsoft"
    candidates = [
        {
            'candidate_name': "John Smith",
            'background': 'Recent CS graduate at George Washington University with an Applied AI internship at Gusto in SF'
        },
        {
            'candidate_name': "Jane Doe",
            'background': 'Recent CS and Math graduate at Whitman College; College soccer player; a firmware engineer internship at HP in Vancouver, WA'
        }
    ]

    interview = Interview()

    # Phase 1: Generate ONE set of questions for all candidates
    print("Phase 1: Generating interview questions...")
    try:
        questions_result = interview.crew_phase1_questions().kickoff(
            inputs={'company_name': company_name}
        )
        interview_questions = questions_result.raw
    except Exception as e:
        raise Exception(f"Phase 1 failed: {e}")

    # Phase 2: Each candidate answers the SAME questions
    candidates_answers = []
    for candidate in candidates:
        print(f"Phase 2: {candidate['candidate_name']} answering questions...")
        try:
            result = interview.crew_phase2_answer().kickoff(inputs={
                'company_name': company_name,
                'background': candidate['background'],
                'candidate_name': candidate['candidate_name'],
                'interview_questions': interview_questions
            })
            candidates_answers.append({
                'name': candidate['candidate_name'],
                'background': candidate['background'],
                'answers': result.raw
            })
            print(f"  -> {candidate['candidate_name']} complete")
        except Exception as e:
            raise Exception(f"Phase 2 failed for {candidate['candidate_name']}: {e}")

    # Phase 3: Interviewer compares all candidates and recommends who to hire
    print("Phase 3: Comparing candidates and making hiring decision...")
    candidates_summary = "\n\n---\n\n".join(
        f"## Candidate: {c['name']}\n**Background:** {c['background']}\n\n**Answers:**\n{c['answers']}"
        for c in candidates_answers
    )
    try:
        hire_result = interview.crew_phase3_hire().kickoff(inputs={
            'company_name': company_name,
            'candidates_summary': candidates_summary
        })
        print(f"\nHiring Decision:\n{hire_result.raw}")
    except Exception as e:
        raise Exception(f"Phase 3 failed: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        Interview().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        Interview().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        Interview().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

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
        "topic": "",
        "current_year": ""
    }

    try:
        result = Interview().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
