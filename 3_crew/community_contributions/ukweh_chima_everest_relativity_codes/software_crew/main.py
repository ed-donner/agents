from crew import SoftwareEngineeringCrew
import os
from dotenv import load_dotenv

def run():
    load_dotenv(override=True)
    
    project_description = "A task management system with AI-powered task prioritization and real-time alerts."
    
    inputs = {
        'project_description': project_description
    }
    
    print(f"🚀 Starting Software Engineering Crew for: {project_description}")
    
    # In a real crewai run, this would be kicked off by CLI 
    # but for a contribution script we can invoke it here.
    result = SoftwareEngineeringCrew().crew().kickoff(inputs=inputs)
    
    print("\n✅ Crew results:")
    print(result)

if __name__ == "__main__":
    run()
