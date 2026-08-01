#!/usr/bin/env python
import os
import shutil
from dev_swarm.crew import DevSwarmCrew
from crewai import Crew, Process, Task
from dotenv import load_dotenv

load_dotenv()

def run():
    # 1. CLEAN WORKSPACE
    workspace_dir = 'project_output'
    src_dir = os.path.join(workspace_dir, 'src')
    
    if os.path.exists(workspace_dir):
        shutil.rmtree(workspace_dir)
    os.makedirs(src_dir, exist_ok=True)

    # Load Model strings
    manager_model = os.getenv("MANAGER_MODEL", "gpt-4o")

    print(f"## Phase 1: Discovery & Architecture Research using {manager_model}...")
    
    inputs = {
        'user_requirement': 'A high-speed real-time stock market tracker with SMS alerts using Twilio and Redis.'
    }

    # 2. RUN THE ARCHITECT (Discovery Phase)
    crew_instance = DevSwarmCrew()
    discovery_result = crew_instance.crew().kickoff(inputs=inputs)
    blueprint = discovery_result.pydantic

    print(f"\n## Blueprint Created: {blueprint.project_name}")

    # --- SAFETY LIMITER & BUDGET CONTROL ---
    MAX_AGENTS = 2  
    MAX_TASKS = 4   
    hiring_list = blueprint.required_agents[:MAX_AGENTS]
    task_list = blueprint.dynamic_tasks[:MAX_TASKS]

    # 3. DYNAMIC ASSEMBLY
    active_agents = { "Architect": crew_instance.architect() }
    for agent_schema in hiring_list:
        new_agent = crew_instance.hire_dynamic_agent(agent_schema)
        active_agents[agent_schema.role] = new_agent
        print(f"   -> Hired Specialist: {agent_schema.role}")

    # 4. ATOMIC EXECUTION LOOP (Phase 2)
    # Instead of one big crew, we run individual mini-crews for each file
    print(f"\n## Phase 2: Executing {len(task_list)} Atomic Build Tasks...")
    
    for t_schema in task_list:
        print(f"\n🛠️  Building Module: {t_schema.name}...")
        
        # Determine which agent is best for this task
        executing_agent = active_agents.get(t_schema.assigned_agent_role, active_agents["Architect"])
        
        atomic_task = Task(
            description=(
                f"GOAL: {t_schema.description}\n\n"
                f"CRITICAL REQUIREMENT: You MUST use the 'Advanced FileWriter' tool to save your code. "
                f"Do not simply output code in the chat. If you don't use the tool, you fail.\n"
                f"Save as: {t_schema.name}"
            ),
            expected_output=f"A confirmation message from the Advanced FileWriter tool that {t_schema.name} was saved.",
            agent=executing_agent
        )

        # Create a mini-crew for this specific file to prevent distractions
        mini_crew = Crew(
            agents=[executing_agent],
            tasks=[atomic_task],
            verbose=True,
            process=Process.sequential
        )
        
        mini_crew.kickoff()

    print("\n\n####################################")
    print("## MISSION ACCOMPLISHED: ALL FILES CREATED ##")
    print("####################################\n")

if __name__ == "__main__":
    run()