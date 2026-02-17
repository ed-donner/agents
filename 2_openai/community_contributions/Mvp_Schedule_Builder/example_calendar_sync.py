"""
Example usage of GoogleCalendarIntegration with SchedulerAgent output.

This demonstrates how to sync a Schedule created by the SchedulerAgent
to Google Calendar.
"""

import logging
from product_agents.scheduler_agent import SchedulerAgent, Schedule, Activity
from tools import GoogleCalendarIntegration

# Configure logging
logging.basicConfig(level=logging.INFO)

def example_usage():
    """Example of syncing scheduler output to Google Calendar."""
    
    # Example: Create a sample schedule (normally this would come from SchedulerAgent)
    sample_activities = [
        Activity(
            name="Project Setup & Planning",
            start_date="2024-11-15",
            end_date="2024-11-17",
            description="Initialize project structure, setup development environment"
        ),
        Activity(
            name="Database Design",
            start_date="2024-11-18",
            end_date="2024-11-20",
            description="Design database schema and setup database connections"
        ),
        Activity(
            name="API Development",
            start_date="2024-11-21",
            end_date="2024-11-25",
            description="Develop core API endpoints and business logic"
        ),
        Activity(
            name="Frontend Development",
            start_date="2024-11-26",
            end_date="2024-11-30",
            description="Build user interface and integrate with API"
        ),
        Activity(
            name="Testing & Deployment",
            start_date="2024-12-01",
            end_date="2024-12-05",
            description="Comprehensive testing and production deployment"
        )
    ]
    
    sample_schedule = Schedule(
        calendar_name="MVP Development Schedule",
        activities=sample_activities
    )
    
    try:
        # Initialize Google Calendar integration
        # Note: You'll need credentials.json from Google Cloud Console
        calendar_service = GoogleCalendarIntegration(
            credentials_file='credentials.json',
            token_file='token.json'
        )
        
        # Sync the schedule to Google Calendar
        result = calendar_service.sync_schedule(sample_schedule)
        
        print(f"✅ Successfully synced schedule!")
        print(f"Calendar ID: {result['calendar_id']}")
        print(f"Events created: {result['total_events']}/{result['activities_processed']}")
        print(f"Event IDs: {result['event_ids']}")
        
    except Exception as e:
        print(f"❌ Failed to sync schedule: {e}")

def sync_scheduler_agent_output():
    """Example of using actual SchedulerAgent output."""
    
    # Create scheduler agent
    scheduler = SchedulerAgent()
    
    # Example functional requirements (normally from ProductManagerAgent)
    requirements = """
    Functional Requirements for MVP:
    1. User registration and authentication system
    2. Product catalog with search functionality
    3. Shopping cart and checkout process
    4. Payment integration
    5. Order management system
    6. Admin dashboard for product management
    """
    
    try:
        # Get schedule from agent (this would be async in real usage)
        # schedule = await scheduler.agent.run(requirements)
        
        # For demo, we'll use the sample schedule
        print("📅 Using sample schedule for demo...")
        example_usage()
        
    except Exception as e:
        print(f"❌ Failed to generate or sync schedule: {e}")

if __name__ == "__main__":
    example_usage()