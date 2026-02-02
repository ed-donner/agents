"""
Main Development Crew - Orchestrates all agents for project development
"""
from typing import List, Dict, Any, Optional
from crewai import Crew, Process
from loguru import logger

from agents import (
    TeamManagerAgent,
    AnalystAgent,
    BackendEngineerFactory,
    FrontendEngineerFactory,
    DevOpsEngineer,
    SystemEngineer,
    DatabaseEngineer,
    QAEngineer
)
from tasks import (
    TaskFactory,
    AnalysisTasks,
    BackendTasks,
    FrontendTasks,
    InfrastructureTasks,
    TestingTasks
)
from models.requirements import ComplexStackRequest
from models.project import Project, TaskDefinition
from config.settings import settings, TaskStatus


class DevelopmentCrew:
    """
    Main crew that orchestrates all development agents
    """
    
    def __init__(self, request: ComplexStackRequest):
        self.request = request
        self.project = Project(
            name=request.project_name,
            description=request.description
        )
        
        # Initialize agents
        self._init_agents()
        
        # Track crew execution
        self.crew: Optional[Crew] = None
        self.results: Dict[str, Any] = {}
        
        logger.info(f"Initialized DevelopmentCrew for project: {request.project_name}")
    
    def _init_agents(self):
        """Initialize all required agents based on request"""
        logger.info("Initializing agents...")
        
        # Core agents
        self.manager = TeamManagerAgent()
        self.analyst = AnalystAgent()
        
        # Backend engineer based on language
        self.backend_engineer = BackendEngineerFactory.create(
            self.request.backend_language
        )
        
        # Frontend engineer based on framework
        self.frontend_engineer = FrontendEngineerFactory.create(
            self.request.frontend_framework
        )
        
        # Infrastructure agents
        self.devops_engineer = DevOpsEngineer()
        self.system_engineer = SystemEngineer()
        
        # Database engineer
        self.db_engineer = DatabaseEngineer()
        
        # QA engineer
        self.qa_engineer = QAEngineer()
        
        logger.info("All agents initialized successfully")
    
    def _create_analysis_tasks(self) -> List:
        """Create analysis phase tasks"""
        tasks = []
        
        # Requirement analysis
        tasks.append(
            AnalysisTasks.requirement_analysis(
                agent=self.manager.get_agent(),
                request=self.request
            )
        )
        
        # Architecture design
        tasks.append(
            AnalysisTasks.architecture_design(
                agent=self.manager.get_agent(),
                request=self.request,
                context=[tasks[0]]
            )
        )
        
        # Task decomposition
        tasks.append(
            AnalysisTasks.task_decomposition(
                agent=self.manager.get_agent(),
                request=self.request,
                context=[tasks[0], tasks[1]]
            )
        )
        
        return tasks
    
    def _create_backend_tasks(self, context: List = None) -> List:
        """Create backend development tasks"""
        tasks = []
        
        # Project structure
        tasks.append(
            BackendTasks.create_project_structure(
                agent=self.backend_engineer.get_agent(),
                language=self.request.backend_language,
                framework=self.request.backend_framework,
                project_name=self.request.project_name
            )
        )
        
        # Models
        tasks.append(
            BackendTasks.implement_models(
                agent=self.backend_engineer.get_agent(),
                entities=[
                    {"name": "User", "fields": ["id", "email", "name"]},
                    {"name": "Item", "fields": ["id", "name", "description"]}
                ],
                context=[tasks[0]] + (context or [])
            )
        )
        
        # Services
        tasks.append(
            BackendTasks.implement_services(
                agent=self.backend_engineer.get_agent(),
                services=[
                    {"name": "UserService", "methods": ["create", "get", "update", "delete"]},
                    {"name": "ItemService", "methods": ["create", "get", "list", "update", "delete"]}
                ],
                context=[tasks[0], tasks[1]] + (context or [])
            )
        )
        
        # API endpoints
        tasks.append(
            BackendTasks.implement_api(
                agent=self.backend_engineer.get_agent(),
                endpoints=[
                    {"path": "/users", "methods": ["GET", "POST"]},
                    {"path": "/users/{id}", "methods": ["GET", "PUT", "DELETE"]},
                    {"path": "/items", "methods": ["GET", "POST"]},
                    {"path": "/items/{id}", "methods": ["GET", "PUT", "DELETE"]}
                ],
                context=tasks + (context or [])
            )
        )
        
        # Authentication
        tasks.append(
            BackendTasks.implement_authentication(
                agent=self.backend_engineer.get_agent(),
                auth_type=self.request.security.authentication,
                context=tasks + (context or [])
            )
        )
        
        return tasks
    
    def _create_frontend_tasks(self, context: List = None) -> List:
        """Create frontend development tasks"""
        tasks = []
        
        # Project structure
        tasks.append(
            FrontendTasks.create_project_structure(
                agent=self.frontend_engineer.get_agent(),
                framework=self.request.frontend_framework,
                project_name=self.request.project_name
            )
        )
        
        # Components
        tasks.append(
            FrontendTasks.implement_components(
                agent=self.frontend_engineer.get_agent(),
                components=[
                    {"name": "Button", "type": "ui"},
                    {"name": "Card", "type": "ui"},
                    {"name": "Form", "type": "ui"},
                    {"name": "Table", "type": "ui"},
                    {"name": "Modal", "type": "ui"}
                ],
                context=[tasks[0]] + (context or [])
            )
        )
        
        # Pages
        tasks.append(
            FrontendTasks.implement_pages(
                agent=self.frontend_engineer.get_agent(),
                pages=[
                    {"name": "Home", "route": "/"},
                    {"name": "Login", "route": "/login"},
                    {"name": "Dashboard", "route": "/dashboard"},
                    {"name": "UserList", "route": "/users"},
                    {"name": "UserDetail", "route": "/users/:id"}
                ],
                context=tasks + (context or [])
            )
        )
        
        # State management
        tasks.append(
            FrontendTasks.implement_state_management(
                agent=self.frontend_engineer.get_agent(),
                state_config={
                    "type": "redux" if self.request.frontend_framework == "react" else "pinia",
                    "slices": ["auth", "users", "items"]
                },
                context=tasks + (context or [])
            )
        )
        
        # API integration
        tasks.append(
            FrontendTasks.implement_api_integration(
                agent=self.frontend_engineer.get_agent(),
                api_config={
                    "base_url": "/api",
                    "endpoints": ["auth", "users", "items"]
                },
                context=tasks + (context or [])
            )
        )
        
        return tasks
    
    def _create_infrastructure_tasks(self, context: List = None) -> List:
        """Create infrastructure tasks"""
        tasks = []
        
        # Infrastructure design
        tasks.append(
            InfrastructureTasks.design_infrastructure(
                agent=self.system_engineer.get_agent(),
                infra_config=self.request.infrastructure.model_dump()
            )
        )
        
        # Terraform
        tasks.append(
            InfrastructureTasks.implement_terraform(
                agent=self.system_engineer.get_agent(),
                resources=[
                    {"type": "vpc", "name": "main"},
                    {"type": "eks", "name": "main"},
                    {"type": "rds", "name": "main"}
                ],
                context=[tasks[0]] + (context or [])
            )
        )
        
        # Kubernetes
        tasks.append(
            InfrastructureTasks.implement_kubernetes(
                agent=self.devops_engineer.get_agent(),
                services=[
                    {"name": "backend", "port": 8080},
                    {"name": "frontend", "port": 3000}
                ],
                context=tasks + (context or [])
            )
        )
        
        # CI/CD
        tasks.append(
            InfrastructureTasks.implement_cicd(
                agent=self.devops_engineer.get_agent(),
                cicd_config={
                    "platform": self.request.cicd_platform,
                    "stages": ["test", "build", "deploy"],
                    "environments": ["staging", "production"]
                },
                context=tasks + (context or [])
            )
        )
        
        # Monitoring
        tasks.append(
            InfrastructureTasks.implement_monitoring(
                agent=self.devops_engineer.get_agent(),
                monitoring_config={
                    "stack": self.request.monitoring_stack,
                    "services": ["backend", "frontend", "database"]
                },
                context=tasks + (context or [])
            )
        )
        
        return tasks
    
    def _create_testing_tasks(self, context: List = None) -> List:
        """Create testing tasks"""
        tasks = []
        
        # Test strategy
        tasks.append(
            TestingTasks.create_test_strategy(
                agent=self.qa_engineer.get_agent(),
                project_config={
                    "backend": self.request.backend_language,
                    "frontend": self.request.frontend_framework
                }
            )
        )
        
        # Unit tests
        tasks.append(
            TestingTasks.implement_unit_tests(
                agent=self.qa_engineer.get_agent(),
                components=["UserService", "ItemService", "AuthService"],
                context=[tasks[0]] + (context or [])
            )
        )
        
        # Integration tests
        tasks.append(
            TestingTasks.implement_integration_tests(
                agent=self.qa_engineer.get_agent(),
                api_endpoints=[
                    {"path": "/users", "methods": ["GET", "POST"]},
                    {"path": "/items", "methods": ["GET", "POST"]}
                ],
                context=tasks + (context or [])
            )
        )
        
        # E2E tests
        tasks.append(
            TestingTasks.implement_e2e_tests(
                agent=self.qa_engineer.get_agent(),
                user_flows=[
                    {"name": "User Registration", "steps": ["visit", "fill", "submit"]},
                    {"name": "Login", "steps": ["visit", "fill", "submit"]},
                    {"name": "Create Item", "steps": ["login", "navigate", "fill", "submit"]}
                ],
                context=tasks + (context or [])
            )
        )
        
        return tasks
    
    def _create_database_tasks(self, context: List = None) -> List:
        """Create database tasks"""
        tasks = []
        
        # Database schema
        tasks.append(
            TaskFactory.create_database_task(
                agent=self.db_engineer.get_agent(),
                database_config=self.request.database.model_dump(),
                entities=[
                    {
                        "name": "users",
                        "fields": [
                            {"name": "id", "type": "uuid", "primary_key": True},
                            {"name": "email", "type": "string", "unique": True},
                            {"name": "name", "type": "string"},
                            {"name": "password_hash", "type": "string"}
                        ]
                    },
                    {
                        "name": "items",
                        "fields": [
                            {"name": "id", "type": "uuid", "primary_key": True},
                            {"name": "name", "type": "string"},
                            {"name": "description", "type": "text"},
                            {"name": "user_id", "type": "uuid", "foreign_key": "users.id"}
                        ]
                    }
                ],
                context=context
            )
        )
        
        return tasks
    
    def build_crew(self) -> Crew:
        """Build the complete development crew"""
        logger.info("Building development crew...")
        
        # Create all tasks in order
        analysis_tasks = self._create_analysis_tasks()
        database_tasks = self._create_database_tasks(context=analysis_tasks)
        backend_tasks = self._create_backend_tasks(context=analysis_tasks + database_tasks)
        frontend_tasks = self._create_frontend_tasks(context=analysis_tasks)
        infrastructure_tasks = self._create_infrastructure_tasks(context=analysis_tasks)
        testing_tasks = self._create_testing_tasks(context=backend_tasks + frontend_tasks)
        
        # Combine all tasks
        all_tasks = (
            analysis_tasks +
            database_tasks +
            backend_tasks +
            frontend_tasks +
            infrastructure_tasks +
            testing_tasks
        )
        
        # Get all agents
        all_agents = [
            self.manager.get_agent(),
            self.analyst.get_agent(),
            self.backend_engineer.get_agent(),
            self.frontend_engineer.get_agent(),
            self.devops_engineer.get_agent(),
            self.system_engineer.get_agent(),
            self.db_engineer.get_agent(),
            self.qa_engineer.get_agent()
        ]
        
        # Create the crew
        self.crew = Crew(
            agents=all_agents,
            tasks=all_tasks,
            process=Process.sequential,  # or Process.hierarchical
            verbose=settings.crewai_verbose,
            memory=settings.crewai_memory,
            max_rpm=settings.crewai_max_rpm
        )
        
        logger.info(f"Crew built with {len(all_agents)} agents and {len(all_tasks)} tasks")
        
        return self.crew
    
    def run(self) -> Dict[str, Any]:
        """Execute the crew and return results"""
        if not self.crew:
            self.build_crew()
        
        logger.info("Starting crew execution...")
        
        try:
            result = self.crew.kickoff()
            
            self.results = {
                "status": "success",
                "output": result,
                "project": self.project.model_dump()
            }
            
            logger.info("Crew execution completed successfully")
            
        except Exception as e:
            logger.error(f"Crew execution failed: {str(e)}")
            self.results = {
                "status": "error",
                "error": str(e),
                "project": self.project.model_dump()
            }
        
        return self.results
    
    async def run_async(self) -> Dict[str, Any]:
        """Execute the crew asynchronously"""
        if not self.crew:
            self.build_crew()
        
        logger.info("Starting async crew execution...")
        
        try:
            result = await self.crew.kickoff_async()
            
            self.results = {
                "status": "success",
                "output": result,
                "project": self.project.model_dump()
            }
            
            logger.info("Async crew execution completed successfully")
            
        except Exception as e:
            logger.error(f"Async crew execution failed: {str(e)}")
            self.results = {
                "status": "error",
                "error": str(e),
                "project": self.project.model_dump()
            }
        
        return self.results
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress"""
        return self.project.get_progress()
