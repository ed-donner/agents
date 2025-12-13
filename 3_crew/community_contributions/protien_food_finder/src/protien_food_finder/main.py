#!/usr/bin/env python
import sys
import os
import warnings

from datetime import datetime
from dotenv import load_dotenv

from protien_food_finder.crew import ProtienFoodFinder

# Load environment variables from .env file
load_dotenv()

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Validate required API keys are set
def validate_api_keys():
    """Validate that required API keys are configured."""
    missing_keys = []
    
    if not os.getenv("GOOGLE_API_KEY"):
        missing_keys.append("GOOGLE_API_KEY")
    if not os.getenv("SERPER_API_KEY"):
        missing_keys.append("SERPER_API_KEY")
    
    if missing_keys:
        raise ValueError(
            f"Missing required API keys: {', '.join(missing_keys)}\n"
            f"Please set them in your .env file or environment variables."
        )
    
    print("✅ API keys validated successfully\n")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the protein food finder crew with DYNAMIC workflow.
    The crew will:
    1. Find stores near your location
    2. Dynamically create specialist agents for each store
    3. Search for products in parallel (if configured)
    4. Validate and recommend the best options
    """
    # Validate API keys before running
    validate_api_keys()

    inputs = {
        'location': 'Belmont, CA 94002',
        'dietary_preferences': '''
        - High protein (20g+ per serving)
        - No beef, pork, turkey, or tuna
        - Chicken, fish (not tuna), salmon, shrimp, eggs, plant-based allowed
        - Gluten-free preferred
        - Reduced/low sugar (5-10g max)
        - Frozen and shelf stable products allowed
        '''
    }

    # Option to use legacy workflow
    use_dynamic = os.getenv("USE_DYNAMIC_WORKFLOW", "true").lower() == "true"

    try:
        print("\n" + "="*80)
        print(f"🚀 Starting Protein Food Finder Crew ({'DYNAMIC' if use_dynamic else 'LEGACY'} mode)")
        print("="*80 + "\n")
        print(f"📍 Location: {inputs['location']}")
        print(f"🥗 Dietary Preferences: {inputs['dietary_preferences']}")
        print("\n" + "="*80 + "\n")

        # Create crew instance
        crew_instance = ProtienFoodFinder()

        if use_dynamic:
            # Use dynamic workflow - builds crew based on found stores
            print("⚙️  Using DYNAMIC workflow (store-based agents)")
            print("   - Will find stores first")
            print("   - Create one specialist agent per store")
            print("   - Continue even if some stores fail\n")

            # Build and run dynamic crew
            dynamic_crew = crew_instance.build_dynamic_crew(
                location=inputs['location'],
                dietary_preferences=inputs['dietary_preferences']
            )
            result = dynamic_crew.kickoff(inputs=inputs)
        else:
            # Use legacy workflow - static agents
            print("⚙️  Using LEGACY workflow (static agents)\n")
            result = crew_instance.crew().kickoff(inputs=inputs)
        
        print("\n" + "="*80)
        print("✅ CREW EXECUTION COMPLETED")
        print("="*80 + "\n")
        
        print("📊 FINAL RESULTS:")
        print("-" * 80)
        print(result)
        print("-" * 80 + "\n")
        
        # If result has tasks_output, print each task result
        if hasattr(result, 'tasks_output') and result.tasks_output:
            print("\n" + "="*80)
            print("📋 INDIVIDUAL TASK OUTPUTS")
            print("="*80 + "\n")
            
            for i, task_output in enumerate(result.tasks_output, 1):
                print(f"\n{'='*80}")
                print(f"Task {i}: {task_output.description if hasattr(task_output, 'description') else 'N/A'}")
                print(f"{'='*80}")
                print(f"Agent: {task_output.agent if hasattr(task_output, 'agent') else 'N/A'}")
                print(f"\nOutput:")
                print("-" * 80)
                print(task_output.raw if hasattr(task_output, 'raw') else task_output)
                print("-" * 80 + "\n")
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    # Validate API keys before training
    validate_api_keys()
    
    inputs = {
        'location': 'Belmont, CA 94002',
        'dietary_preferences': '''
        - High protein goal: 20g+ per serving
        - No dietary restrictions
        '''
    }
    try:
        ProtienFoodFinder().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    # Validate API keys before replaying
    validate_api_keys()
    
    try:
        ProtienFoodFinder().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    # Validate API keys before testing
    validate_api_keys()
    
    inputs = {
        'location': 'Belmont, CA 94002',
        'dietary_preferences': '''
        - High protein goal: 20g+ per serving
        - No dietary restrictions
        '''
    }
    
    try:
        ProtienFoodFinder().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")
