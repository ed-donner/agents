"""
Example: Simple project generation
"""
from models.requirements import ComplexStackRequest
from crews import AnalysisCrew


def main():
    """Run a simple project analysis"""
    
    # Define project requirements
    request = ComplexStackRequest(
        project_name="Todo API",
        description="A simple todo list API with CRUD operations",
        backend_language="python",
        backend_framework="FastAPI",
        frontend_framework="react"
    )
    
    # Create and run analysis crew
    crew = AnalysisCrew(request)
    result = crew.run()
    
    print("Analysis Result:")
    print(result)


if __name__ == "__main__":
    main()
