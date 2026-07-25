from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntimeHost
from agent import Agent
from creator import Creator
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntime
from autogen_core import AgentId
import messages
import asyncio
import json
import os
from datetime import datetime

# Configuration
HOW_MANY_AGENTS = 20
EVOLUTION_CYCLES = 3  # Number of times Creator evolves

async def create_and_message(worker, creator_id, i: int):
    """Create a new agent and capture its initial idea"""
    try:
        result = await worker.send_message(messages.Message(content=f"agent{i}.py"), creator_id)
        
        # Extract idea and lineage from result
        idea_content = result.content
        
        with open(f"idea{i}.md", "w") as f:
            f.write(f"# Idea from Agent {i}\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            f.write(f"{idea_content}\n")
        
        print(f"** Idea {i} saved to idea{i}.md")
        return {"agent": i, "idea": idea_content, "success": True}
        
    except Exception as e:
        print(f"** Failed to run worker {i} due to exception: {e}")
        return {"agent": i, "error": str(e), "success": False}

async def run_swarm_cycle(worker, creator_id, cycle_num: int):
    """Run one complete swarm cycle and collect all ideas"""
    print(f"\n{'='*60}")
    print(f"** SWARM CYCLE {cycle_num} STARTING")
    print(f"{'='*60}\n")
    
    coroutines = [create_and_message(worker, creator_id, i) for i in range(1, HOW_MANY_AGENTS+1)]
    results = await asyncio.gather(*coroutines)
    
    # Save cycle summary
    summary = {
        "cycle": cycle_num,
        "timestamp": datetime.now().isoformat(),
        "total_agents": HOW_MANY_AGENTS,
        "successful": len([r for r in results if r.get("success")]),
        "failed": len([r for r in results if not r.get("success")]),
        "results": results
    }
    
    with open(f"cycle_{cycle_num}_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"** Cycle {cycle_num} complete: {summary['successful']}/{HOW_MANY_AGENTS} agents successful")
    return summary

async def trigger_creator_evolution(worker, creator_id):
    """Trigger the Creator's self-evolution"""
    print(f"\n{'='*60}")
    print(f"** TRIGGERING CREATOR EVOLUTION")
    print(f"{'='*60}\n")
    
    try:
        result = await worker.send_message(
            messages.Message(content="EVOLVE"),
            creator_id
        )
        print(f"** Evolution result: {result.content}")
        return True
    except Exception as e:
        print(f"** Evolution failed: {e}")
        return False

async def main():
    print("="*60)
    print("RECURSIVE SELF-EVOLVING SWARM - STARTING")
    print("="*60)
    
    host = GrpcWorkerAgentRuntimeHost(address="localhost:50051")
    host.start() 
    worker = GrpcWorkerAgentRuntime(host_address="localhost:50051")
    await worker.start()
    
    # Register initial Creator
    print("\n** Registering Creator v1")
    result = await Creator.register(worker, "Creator", lambda: Creator("Creator", version=1))
    creator_id = AgentId("Creator", "default")
    
    all_cycle_summaries = []
    
    # Run evolution cycles
    for cycle in range(1, EVOLUTION_CYCLES + 1):
        # Run swarm cycle
        cycle_summary = await run_swarm_cycle(worker, creator_id, cycle)
        all_cycle_summaries.append(cycle_summary)
        
        # Trigger Creator evolution (except on last cycle)
        if cycle < EVOLUTION_CYCLES:
            # Wait for the swarm to settle
            await asyncio.sleep(2)
            
            # Trigger evolution
            await trigger_creator_evolution(worker, creator_id)
            
            # Wait for evolution to complete
            await asyncio.sleep(2)
    
    # Final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"** Completed {EVOLUTION_CYCLES} cycles")
    print(f"** Total agents created: {HOW_MANY_AGENTS * EVOLUTION_CYCLES}")
    
    # Load and display evolution log
    if os.path.exists("evolution_log.json"):
        with open("evolution_log.json", "r") as f:
            evolution_log = json.load(f)
        print(f"** Creator evolved {len(evolution_log.get('versions', []))} times")
        print(f"** Current Creator version: {evolution_log.get('current_version', 1)}")
    
    # Save final report
    final_report = {
        "timestamp": datetime.now().isoformat(),
        "total_cycles": EVOLUTION_CYCLES,
        "agents_per_cycle": HOW_MANY_AGENTS,
        "cycle_summaries": all_cycle_summaries
    }
    
    with open("final_report.json", "w") as f:
        json.dump(final_report, f, indent=2)
    
    print(f"** Final report saved to final_report.json")
    
    try:
        await worker.stop()
        await host.stop()
        print("** Runtime stopped successfully")
    except Exception as e:
        print(f"** Error stopping runtime: {e}")

if __name__ == "__main__":
    asyncio.run(main())
