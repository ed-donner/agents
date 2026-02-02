"""
Main entry point for CrewAI Coding Agents
"""
import sys
import asyncio
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from loguru import logger

from models.requirements import ComplexStackRequest, DatabaseRequirement, InfrastructureRequirement, SecurityRequirement
from workflows import ProjectWorkflow
from crews import DevelopmentCrew, AnalysisCrew
from config.settings import settings


# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level
)
logger.add("logs/crewai_agents.log", rotation="10 MB", retention="7 days")

# CLI app
app = typer.Typer(
    name="crewai-coding-agents",
    help="AI-powered coding agent ecosystem using CrewAI"
)
console = Console()


def create_sample_request() -> ComplexStackRequest:
    """Create a sample project request for demonstration"""
    return ComplexStackRequest(
        project_name="E-Commerce Platform",
        description="A modern e-commerce platform with user authentication, product catalog, shopping cart, and order management",
        backend_language="python",
        backend_framework="FastAPI",
        api_type="REST",
        frontend_framework="react",
        ssr_required=False,
        database=DatabaseRequirement(
            primary_db={"type": "postgresql", "version": "15"},
            cache_db={"type": "redis", "version": "7"},
            search_db={"type": "elasticsearch", "version": "8"}
        ),
        infrastructure=InfrastructureRequirement(
            environment="cloud",
            cloud_provider="AWS",
            regions=["us-east-1"],
            high_availability=True
        ),
        security=SecurityRequirement(
            authentication="JWT",
            authorization="RBAC",
            encryption=True
        ),
        cicd_platform="github_actions",
        deployment_strategy="rolling",
        monitoring_stack=["prometheus", "grafana", "loki"]
    )


@app.command()
def analyze(
    project_name: str = typer.Option("Demo Project", help="Project name"),
    description: str = typer.Option("A demo project", help="Project description"),
    backend: str = typer.Option("python", help="Backend language"),
    frontend: str = typer.Option("react", help="Frontend framework")
):
    """
    Run analysis phase only to get architecture and task breakdown
    """
    console.print(Panel.fit(
        "[bold blue]CrewAI Coding Agents - Analysis Mode[/bold blue]\n"
        f"Project: {project_name}",
        border_style="blue"
    ))
    
    request = ComplexStackRequest(
        project_name=project_name,
        description=description,
        backend_language=backend,
        backend_framework="FastAPI" if backend == "python" else "gin",
        frontend_framework=frontend
    )
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Running analysis...", total=None)
        
        try:
            analysis_crew = AnalysisCrew(request)
            result = analysis_crew.run()
            
            progress.update(task, description="Analysis complete!")
            
            # Display results
            console.print("\n[bold green]Analysis Results:[/bold green]")
            console.print(result.get("analysis", "No analysis output"))
            
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            raise typer.Exit(1)


@app.command()
def develop(
    project_name: str = typer.Option("Demo Project", help="Project name"),
    description: str = typer.Option("A demo project", help="Project description"),
    backend: str = typer.Option("python", help="Backend language"),
    frontend: str = typer.Option("react", help="Frontend framework"),
    output_dir: Optional[str] = typer.Option(None, help="Output directory")
):
    """
    Run full development workflow with all agents
    """
    console.print(Panel.fit(
        "[bold green]CrewAI Coding Agents - Development Mode[/bold green]\n"
        f"Project: {project_name}",
        border_style="green"
    ))
    
    request = ComplexStackRequest(
        project_name=project_name,
        description=description,
        backend_language=backend,
        backend_framework="FastAPI" if backend == "python" else "gin",
        frontend_framework=frontend
    )
    
    def on_progress(progress_data):
        """Handle progress updates"""
        phase = progress_data.get("phase", "unknown")
        status = progress_data.get("status", "unknown")
        console.print(f"  [{phase}] {status}")
    
    workflow = ProjectWorkflow(
        request=request,
        output_dir=output_dir,
        on_progress=on_progress
    )
    
    console.print("\n[bold]Starting development workflow...[/bold]\n")
    
    try:
        results = workflow.run_full_development()
        
        # Display summary
        summary = results.get("summary", {})
        
        table = Table(title="Development Complete", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Project", summary.get("project_name", "N/A"))
        table.add_row("Completed At", summary.get("completed_at", "N/A"))
        table.add_row("Phases", f"{summary.get('phases_completed', 0)}/{summary.get('total_phases', 0)}")
        table.add_row("Output Directory", summary.get("output_directory", "N/A"))
        
        console.print("\n")
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def demo():
    """
    Run a demonstration with sample project
    """
    console.print(Panel.fit(
        "[bold magenta]CrewAI Coding Agents - Demo Mode[/bold magenta]\n"
        "Running with sample e-commerce project",
        border_style="magenta"
    ))
    
    request = create_sample_request()
    
    # Show request details
    table = Table(title="Project Configuration", show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Project Name", request.project_name)
    table.add_row("Backend", f"{request.backend_language}/{request.backend_framework}")
    table.add_row("Frontend", request.frontend_framework)
    table.add_row("Database", str(request.database.primary_db))
    table.add_row("Cloud", request.infrastructure.cloud_provider)
    table.add_row("CI/CD", request.cicd_platform)
    
    console.print(table)
    
    if typer.confirm("\nProceed with analysis?"):
        analysis_crew = AnalysisCrew(request)
        result = analysis_crew.run()
        console.print("\n[bold green]Analysis Complete![/bold green]")
        console.print(result.get("analysis", ""))


@app.command()
def status():
    """
    Show system status and configuration
    """
    console.print(Panel.fit(
        "[bold]CrewAI Coding Agents - System Status[/bold]",
        border_style="blue"
    ))
    
    table = Table(show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("LLM Provider", settings.default_llm_provider)
    table.add_row("LLM Model", settings.default_llm_model)
    table.add_row("API Key Set", "✓" if settings.openai_api_key else "✗")
    table.add_row("Verbose Mode", str(settings.crewai_verbose))
    table.add_row("Memory Enabled", str(settings.crewai_memory))
    table.add_row("Output Directory", settings.output_dir)
    table.add_row("Log Level", settings.log_level)
    
    console.print(table)


if __name__ == "__main__":
    app()
