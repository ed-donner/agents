#!/usr/bin/env python3
"""
Orchestrator-Workers Workflow Demo

This file demonstrates the orchestrator-workers workflow pattern from Anthropic's
"Building Effective Agents" blog post. This pattern is different from the 
evaluator-optimizer pattern used in lab 2.

In the orchestrator-workers workflow:
- A central LLM (orchestrator) dynamically breaks down a complex task into subtasks
- Specialized worker LLMs handle each subtask independently
- The orchestrator synthesizes all worker results into a final report

This is ideal for complex tasks where you can't predict the subtasks needed in advance.
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic
from typing import List, Dict, Any

# Load environment variables
load_dotenv(override=True)

class OrchestratorWorkersWorkflow:
    """
    Implements the orchestrator-workers workflow pattern.
    
    This pattern is well-suited for complex tasks where you can't predict 
    the subtasks needed in advance. The orchestrator determines the subtasks 
    based on the specific input, making it more flexible than predefined workflows.
    """
    
    def __init__(self):
        """Initialize the workflow with API clients."""
        self.openai = OpenAI()
        self.claude = Anthropic()
        
        # Initialize API keys
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        
        # Initialize specialized clients
        if self.google_api_key:
            self.gemini = OpenAI(
                api_key=self.google_api_key, 
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
        
        if self.deepseek_api_key:
            self.deepseek = OpenAI(
                api_key=self.deepseek_api_key, 
                base_url="https://api.deepseek.com/v1"
            )
            
        if self.groq_api_key:
            self.groq = OpenAI(
                api_key=self.groq_api_key, 
                base_url="https://api.groq.com/openai/v1"
            )
    
    def orchestrate_task_breakdown(self, complex_task: str) -> List[Dict[str, Any]]:
        """
        The orchestrator breaks down the complex task into specific subtasks.
        
        Args:
            complex_task: The complex task description
            
        Returns:
            List of subtask dictionaries with id, description, expertise_required, and output_format
        """
        orchestrator_prompt = f"""
You are an expert project manager and analyst. Your task is to break down this complex analysis into specific subtasks that can be handled by specialized workers.

TASK: {complex_task}

Break this down into 3-4 specific, focused subtasks that different specialists can work on independently. 
For each subtask, specify:
- The specific question or analysis needed
- What type of expertise is required
- What format the output should be in

Respond with JSON only:
{{
    "subtasks": [
        {{
            "id": 1,
            "description": "specific question/analysis",
            "expertise_required": "type of specialist needed",
            "output_format": "desired output format"
        }}
    ]
}}
"""

        orchestrator_messages = [{"role": "user", "content": orchestrator_prompt}]
        
        response = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=orchestrator_messages,
        )
        
        orchestrator_plan = response.choices[0].message.content
        print("Orchestrator's Plan:")
        print(orchestrator_plan)
        
        # Parse the plan
        plan = json.loads(orchestrator_plan)
        subtasks = plan["subtasks"]
        
        print(f"\nOrchestrator identified {len(subtasks)} subtasks:")
        for subtask in subtasks:
            print(f"- {subtask['description']}")
            
        return subtasks
    
    def execute_worker_tasks(self, subtasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute each subtask with specialized worker LLMs.
        
        Args:
            subtasks: List of subtask dictionaries from the orchestrator
            
        Returns:
            List of worker results with subtask_id, description, expertise, result, and worker_model
        """
        worker_results = []
        
        for subtask in subtasks:
            print(f"\n--- Working on subtask {subtask['id']} ---")
            print(f"Description: {subtask['description']}")
            
            # Create a specialized prompt for this worker
            worker_prompt = f"""
You are a specialist in {subtask['expertise_required']}. 
Your task is: {subtask['description']}

Please provide your analysis in the following format: {subtask['output_format']}

Focus only on your area of expertise and provide a comprehensive, well-reasoned response.
"""
            
            worker_messages = [{"role": "user", "content": worker_prompt}]
            
            # Use different models for different workers to get diverse perspectives
            if subtask['id'] == 1:
                # Safety specialist - use Claude for careful analysis
                response = self.claude.messages.create(
                    model="claude-3-7-sonnet-latest", 
                    messages=worker_messages, 
                    max_tokens=800
                )
                worker_result = response.content[0].text
                worker_model = "claude-3-7-sonnet-latest"
                
            elif subtask['id'] == 2:
                # Economic specialist - use GPT-4 for analytical thinking
                response = self.openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=worker_messages
                )
                worker_result = response.choices[0].message.content
                worker_model = "gpt-4o-mini"
                
            elif subtask['id'] == 3:
                # Legal specialist - use Gemini for structured reasoning (if available)
                if hasattr(self, 'gemini'):
                    response = self.gemini.chat.completions.create(
                        model="gemini-2.0-flash",
                        messages=worker_messages
                    )
                    worker_result = response.choices[0].message.content
                    worker_model = "gemini-2.0-flash"
                else:
                    # Fallback to GPT-4 if Gemini not available
                    response = self.openai.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=worker_messages
                    )
                    worker_result = response.choices[0].message.content
                    worker_model = "gpt-4o-mini (fallback)"
                    
            else:
                # Additional specialists - use available models
                if hasattr(self, 'deepseek'):
                    response = self.deepseek.chat.completions.create(
                        model="deepseek-chat",
                        messages=worker_messages
                    )
                    worker_result = response.choices[0].message.content
                    worker_model = "deepseek-chat"
                else:
                    response = self.openai.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=worker_messages
                    )
                    worker_result = response.choices[0].message.content
                    worker_model = "gpt-4o-mini (additional)"
            
            print(f"Worker model: {worker_model}")
            print(f"Result: {worker_result[:200]}...")  # Show first 200 chars
            
            worker_results.append({
                "subtask_id": subtask['id'],
                "description": subtask['description'],
                "expertise": subtask['expertise_required'],
                "result": worker_result,
                "worker_model": worker_model
            })
            
        return worker_results
    
    def synthesize_results(self, complex_task: str, worker_results: List[Dict[str, Any]]) -> str:
        """
        The orchestrator synthesizes all worker results into a final report.
        
        Args:
            complex_task: The original complex task
            worker_results: Results from all workers
            
        Returns:
            Final synthesized report
        """
        synthesis_prompt = f"""
You are the project manager orchestrating this analysis. You have received detailed reports from {len(worker_results)} specialized workers.

ORIGINAL TASK: {complex_task}

WORKER REPORTS:
"""

        for result in worker_results:
            synthesis_prompt += f"""
WORKER {result['subtask_id']} - {result['expertise']}:
{result['result']}

---
"""

        synthesis_prompt += """
Your job is to synthesize these specialized analyses into a comprehensive, coherent final report.

Create a final report that:
1. Integrates all the worker perspectives
2. Identifies any conflicts or gaps between the analyses
3. Provides overall conclusions and recommendations
4. Is well-structured and easy to understand

Format your response as a professional report with clear sections and actionable insights.
"""

        synthesis_messages = [{"role": "user", "content": synthesis_prompt}]
        
        response = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=synthesis_messages,
        )
        
        final_report = response.choices[0].message.content
        return final_report
    
    def run_workflow(self, complex_task: str) -> Dict[str, Any]:
        """
        Run the complete orchestrator-workers workflow.
        
        Args:
            complex_task: The complex task to analyze
            
        Returns:
            Dictionary containing all workflow results
        """
        print("=" * 80)
        print("ORCHESTRATOR-WORKERS WORKFLOW")
        print("=" * 80)
        print(f"Task: {complex_task}")
        print("=" * 80)
        
        # Step 1: Orchestrator breaks down the task
        print("\n1. TASK BREAKDOWN")
        subtasks = self.orchestrate_task_breakdown(complex_task)
        
        # Step 2: Workers execute subtasks
        print("\n2. WORKER EXECUTION")
        worker_results = self.execute_worker_tasks(subtasks)
        
        # Step 3: Orchestrator synthesizes results
        print("\n3. RESULT SYNTHESIS")
        final_report = self.synthesize_results(complex_task, worker_results)
        
        print("\n" + "=" * 80)
        print("FINAL SYNTHESIZED REPORT")
        print("=" * 80)
        print(final_report)
        
        return {
            "original_task": complex_task,
            "subtasks": subtasks,
            "worker_results": worker_results,
            "final_report": final_report
        }


def compare_workflow_patterns():
    """
    Compare the evaluator-optimizer and orchestrator-workers patterns.
    """
    print("\n" + "=" * 80)
    print("COMPARISON OF WORKFLOW PATTERNS")
    print("=" * 80)

    print("1. EVALUATOR-OPTIMIZER (Lab 2):")
    print("   - Sends same task to multiple models")
    print("   - Uses judge to rank/compare responses")
    print("   - Good for: Quality improvement, model comparison")
    print("   - Trade-off: Higher cost, more complex evaluation")

    print("\n2. ORCHESTRATOR-WORKERS (This Demo):")
    print("   - Central LLM breaks down complex task")
    print("   - Specialized workers handle subtasks")
    print("   - Orchestrator synthesizes results")
    print("   - Good for: Complex tasks, diverse expertise, scalability")
    print("   - Trade-off: More complex orchestration, potential for coordination issues")


def main():
    """Main function to demonstrate the orchestrator-workers workflow."""
    
    # Example complex task
    complex_task = """
Analyze the ethical implications of autonomous vehicles in three key areas:
1. Safety and risk assessment
2. Economic and social impact
3. Legal and regulatory considerations

For each area, provide a detailed analysis with pros, cons, and recommendations.
"""
    
    # Initialize and run the workflow
    workflow = OrchestratorWorkersWorkflow()
    results = workflow.run_workflow(complex_task)
    
    # Compare patterns
    compare_workflow_patterns()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY OF IMPLEMENTED PATTERNS")
    print("=" * 80)

    print("✅ EVALUATOR-OPTIMIZER: Multiple models answer same question, judge ranks them")
    print("✅ ORCHESTRATOR-WORKERS: Central LLM breaks down task, workers handle subtasks, synthesis")

    print("\nOther patterns from the blog post that could be implemented:")
    print("🔲 PROMPT CHAINING: Sequential LLM calls with intermediate checks")
    print("🔲 ROUTING: Classify input and direct to specialized processes")
    print("🔲 PARALLELIZATION: Independent subtasks run simultaneously")
    print("🔲 AUTONOMOUS AGENTS: LLMs with tools operating independently")
    
    return results


if __name__ == "__main__":
    main()
