#!/usr/bin/env python3
"""
Example usage of AI Visual Art Studio IDE
Demonstrates the simplified functionality using OpenAI Agents SDK with delegation flow
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.art_studio import ArtStudio


async def main():
    """Main example function demonstrating delegation flow"""
    
    print("🎨 AI Visual Art Studio IDE - Delegation Flow Example")
    print("=" * 60)
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your_api_key_here")
        return
    
    try:
        # Initialize the Art Studio
        print("\n🚀 Initializing Art Studio...")
        art_studio = ArtStudio()
        
        # Display studio status
        status = art_studio.get_studio_status()
        print(f"\n📊 Studio Status:")
        print(f"   Total Agents: {status['total_agents']}")
        print(f"   OpenAI Agents SDK: {status['openai_agents_sdk']}")
        print(f"   Tracing Enabled: {status['tracing_enabled']}")
        print(f"   Delegation Flow: {status['delegation_flow']}")
        print(f"   Initialized: {status['initialized_at']}")
        
        # Display available agents and their delegation capabilities
        agents = art_studio.get_agents()
        print(f"\n🤖 Available Agents with Delegation Capabilities:")
        for agent_id, agent in agents.items():
            agent_info = art_studio.get_agent_info(agent_id)
            print(f"   - {agent.name}: {agent.description}")
            print(f"     Can delegate to: {', '.join(agent_info['can_delegate_to'])}")
        
        # Example 1: Execute a single agent
        print(f"\n🎯 Example 1: Executing Concept Artist Agent")
        concept_result = await art_studio.execute_agent(
            "concept_artist",
            "Create a concept for a futuristic cityscape with flying cars and neon lights"
        )
        print(f"✅ Concept Artist completed")
        print(f"   Input: {concept_result['input'][:50]}...")
        print(f"   Output: {concept_result['output'][:100]}...")
        
        # Example 2: Execute delegation flow
        print(f"\n🔄 Example 2: Executing Delegation Flow")
        print("   Starting with Concept Artist, agents will delegate as needed...")
        
        delegation_result = await art_studio.execute_delegation_flow(
            "Design a magical forest scene with glowing mushrooms and fairy lights",
            "concept_artist"
        )
        
        print(f"✅ Delegation flow completed")
        print(f"   Primary Agent: {delegation_result['primary_agent']}")
        print(f"   Total Iterations: {delegation_result['total_iterations']}")
        print(f"   Delegation Chain: {len(delegation_result['delegation_chain'])} steps")
        print(f"   Final Output: {delegation_result['final_output'][:100]}...")
        
        # Show delegation chain details
        print(f"\n📋 Delegation Chain Details:")
        for i, step in enumerate(delegation_result['delegation_chain']):
            print(f"   Step {i+1}: {step['agent_name']}")
            print(f"     Input: {step['input'][:50]}...")
            print(f"     Output: {step['output'][:80]}...")
            print()
        
        # Example 3: Show tracing capabilities
        print(f"\n🔍 Example 3: Tracing and Debug Information")
        trace_logs = art_studio.get_trace_logs()
        print(f"   Trace Logs: {len(trace_logs)} entries")
        for log in trace_logs:
            print(f"   - {log['message']} ({log['timestamp']})")
        
        # Example 4: Demonstrate different delegation patterns
        print(f"\n🔄 Example 4: Different Delegation Patterns")
        print("   Let's see how different primary agents handle the same task...")
        
        # Try with Sketch Artist as primary
        sketch_delegation = await art_studio.execute_delegation_flow(
            "Create a steampunk robot character design",
            "sketch_artist"
        )
        print(f"   Sketch Artist as primary: {sketch_delegation['total_iterations']} iterations")
        
        # Try with Curator as primary
        curator_delegation = await art_studio.execute_delegation_flow(
            "Evaluate and improve a landscape painting",
            "curator"
        )
        print(f"   Curator as primary: {curator_delegation['total_iterations']} iterations")
        
        # Display results summary
        print(f"\n📈 Results Summary:")
        print(f"   - Single Agent Executions: 1")
        print(f"   - Delegation Flows: 3")
        print(f"   - Total Steps Executed: {len(delegation_result['delegation_chain']) + len(sketch_delegation['delegation_chain']) + len(curator_delegation['delegation_chain'])}")
        print(f"   - Tracing Enabled: {status['tracing_enabled']}")
        print(f"   - Delegation Flow: {status['delegation_flow']}")
        
        print(f"\n🎉 Delegation flow examples completed successfully!")
        print(f"💡 Key Benefits of Delegation Flow:")
        print(f"   - Agents decide when to delegate based on task requirements")
        print(f"   - No fixed order - natural collaboration emerges")
        print(f"   - Each agent focuses on their expertise")
        print(f"   - Flexible and intelligent workflow orchestration")
        print(f"\n🚀 Try running the Gradio interface with: python main.py")
        print(f"🔍 All agent executions and delegations are automatically traced")
        
    except Exception as e:
        print(f"❌ Error in example: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
