#!/usr/bin/env python
import os
import warnings

from engineering_team.crew import EngineeringTeam

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

requirements = """
A lightweight support ticketing system for a SaaS product.
The system should allow users to create, update, and close tickets with title,
description, priority, status, and requester email.
The system should allow assigning and unassigning tickets to support agents.
The system should support internal notes and public comments.
The system should track created_at, updated_at, and closed_at timestamps.
The system should allow listing tickets by status, priority, assignee, and requester.
The system should provide SLA checks (overdue if open longer than N hours).
The system should prevent invalid transitions (e.g., closing without a resolution note).
The system should provide summary metrics such as open count and average resolution time.
"""
module_name = "support_tickets.py"
class_name = "SupportTicketSystem"


def run():
    """
    Run the engineering crew.
    """
    inputs = {
        'requirements': requirements,
        'module_name': module_name,
        'class_name': class_name
    }

    # Create and run the crew
    result = EngineeringTeam().crew().kickoff(inputs=inputs)


if __name__ == "__main__":
    run()
