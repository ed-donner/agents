#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from interview.crew import Interview

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the crew.
    """
    job_description = """
    About the role:
We're building the next generation of AI-powered products and we need someone who actually understands how agentic systems work — not just someone who wraps an API call and calls it AI. You'll design and ship multi-agent pipelines, RAG systems, and LLM-powered features that real users depend on.

What you'll do:
Design and build multi-agent workflows using LangGraph and LangChain
Build and optimize RAG pipelines with vector databases like Pinecone
Develop and integrate MCP servers to extend agent capabilities
Ship full-stack AI features with Next.js frontends backed by Python services
Prototype fast, iterate faster — we value working demos over perfect specs


What we're looking for:
Hands-on experience with LangChain, LangGraph, or similar agentic frameworks
Strong Python — you should be comfortable building and shipping Python services
Familiarity with vector DBs, embeddings, and how RAG actually works under the hood
Real projects > degrees. Show us something you built.
Startup mindset — you're comfortable with ambiguity and moving fast
Nice to have:


Experience with Anthropic API or Claude-based systems
Prior startup experience or co-founding something (even early stage)
Contributions to open-source AI tooling
"""
    inputs = {
        "job_description": job_description,
    }

    try:
        Interview().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


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
