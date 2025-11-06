#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from researcher.crew import Researcher

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Run the crew.
    """
    inputs = {
        'topic': '''Design and develop a comprehensive Agentic AI system using the CrewAI framework to create an intelligent paralegal assistant specialized in NSW (Australia) property conveyancing. The system should orchestrate multiple AI agents to handle the complete conveyancing workflow from initial client engagement through settlement, integrating with existing APIs for contract review, VOI (Verification of Identity), property searches, certificate procurement, stamp duty calculations, and PEXA workspace management. The solution must establishing Australia's leading AI-powered conveyancing paralegal''',
        'current_year': str(datetime.now().year,),
        'output_pdf_path': '''output/report_vn.pdf'''
    }

    try:
        Researcher().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")
