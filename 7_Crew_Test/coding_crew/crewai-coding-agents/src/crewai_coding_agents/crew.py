#!/usr/bin/env python
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from models.requirements import (
    ComplexStackRequest,
    DatabaseRequirement,
    InfrastructureRequirement,
    SecurityRequirement
)
from config.settings import EnvironmentType
from crews.analysis_crew import AnalysisCrew
from utils.output_manager import OutputManager

def run():
    """
    Run the crew with a simple demo project.
    """
    # Create a simple request
    request = ComplexStackRequest(
        project_name="Demo E-Commerce Platform",
        description="A modern e-commerce platform with microservices architecture",
        backend_language="python",
        backend_framework="fastapi",
        api_type="REST",
        frontend_framework="react",
        ssr_required=True,
        database=DatabaseRequirement(
            primary_db={"type": "postgresql", "version": "15"},
            cache_db={"type": "redis", "version": "7"},
            replication=True
        ),
        infrastructure=InfrastructureRequirement(
            environment=EnvironmentType.CLOUD,
            cloud_provider="aws",
            regions=["us-east-1"],
            high_availability=True,
            disaster_recovery=True
        ),
        security=SecurityRequirement(
            authentication="jwt",
            authorization="rbac",
            encryption=True,
            waf=True,
            ddos_protection=True,
            compliance=["PCI-DSS", "GDPR"]
        ),
        cicd_platform="github-actions",
        deployment_strategy="blue-green",
        monitoring_stack=["prometheus", "grafana", "elk"],
        rate_limiting=True
    )
    
    print("🚀 Starting Analysis Crew...")
    print(f"📝 Project: {request.project_name}")
    print(f"📋 Description: {request.description}")
    print("-" * 80)
    
    # Initialize output manager
    output_mgr = OutputManager()
    project_dir = output_mgr.create_project_output(request.project_name)
    
    print(f"📁 Output directory created: {project_dir}")
    print("-" * 80)
    
    crew = AnalysisCrew(request)
    result = crew.run()
    
    print("-" * 80)
    print("✅ Analysis Complete!")
    
    # Save results
    print("\n💾 Saving results...")
    
    # Save analysis
    if hasattr(result, 'tasks_output') and result.tasks_output:
        for i, task_output in enumerate(result.tasks_output):
            output_file = project_dir / "analysis" / f"task_{i+1}_output.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# Task {i+1} Output\n\n")
                f.write(f"**Description:** {task_output.description}\n\n")
                f.write(f"## Result\n\n")
                f.write(str(task_output.raw))
            print(f"  ✅ Saved: {output_file.name}")
    
    # Create project README
    output_mgr.create_project_readme(project_dir, {
        'name': request.project_name,
        'description': request.description
    })
    
    # Save execution summary
    summary = {
        'project_name': request.project_name,
        'description': request.description,
        'backend': f"{request.backend_language}/{request.backend_framework}",
        'frontend': request.frontend_framework,
        'database': str(request.database.primary_db),
        'cloud_provider': request.infrastructure.cloud_provider,
        'status': 'completed',
        'output_directory': str(project_dir)
    }
    output_mgr.save_execution_summary(project_dir, summary)
    
    print(f"\n🎉 All results saved to: {project_dir}")
    print(f"📊 Result: {result}")
    print("\n🎉 Crew execution completed successfully!")
    
    return result

def train():
    """
    Train the crew for a given number of iterations.
    """
    print("⚠️  Training not yet implemented for this crew structure.")
    print("💡 Use 'python main.py demo' for a demonstration instead.")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    print("⚠️  Replay not yet implemented for this crew structure.")
    print("💡 Use 'python main.py demo' for a demonstration instead.")

def test():
    """
    Test the crew execution and returns the results.
    """
    print("⚠️  Test not yet implemented for this crew structure.")
    print("💡 Use 'python main.py demo' for a demonstration instead.")
