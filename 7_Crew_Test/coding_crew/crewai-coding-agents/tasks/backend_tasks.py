"""
Backend development tasks
"""
from typing import Optional, List, Dict, Any
from crewai import Task, Agent


class BackendTasks:
    """Tasks for backend development"""
    
    @staticmethod
    def create_project_structure(
        agent: Agent,
        language: str,
        framework: str,
        project_name: str
    ) -> Task:
        """Create backend project structure"""
        return Task(
            description=f"""
            Create the project structure for a {language} {framework} application:
            
            Project Name: {project_name}
            
            Create:
            1. Directory structure following best practices
            2. Configuration files (pyproject.toml, go.mod, package.json, etc.)
            3. Environment configuration (.env.example)
            4. Docker configuration (Dockerfile, docker-compose.yml)
            5. Basic application setup with health check endpoint
            6. Logging configuration
            7. Error handling middleware
            """,
            expected_output="""
            Complete project structure with:
            - All necessary directories
            - Configuration files
            - Basic application code
            - Docker setup
            - README with setup instructions
            """,
            agent=agent
        )
    
    @staticmethod
    def implement_models(
        agent: Agent,
        entities: List[Dict[str, Any]],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Implement data models/schemas"""
        return Task(
            description=f"""
            Implement data models for the following entities:
            
            Entities:
            {entities}
            
            Requirements:
            1. Create Pydantic/struct models with validation
            2. Include all necessary fields with proper types
            3. Add documentation/comments
            4. Implement relationships between models
            5. Add serialization/deserialization methods
            """,
            expected_output="""
            Complete model implementations:
            - Base models with common fields
            - Entity-specific models
            - Request/Response schemas
            - Validation logic
            - Type definitions
            """,
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def implement_services(
        agent: Agent,
        services: List[Dict[str, Any]],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Implement service layer"""
        return Task(
            description=f"""
            Implement service layer for the following services:
            
            Services:
            {services}
            
            Requirements:
            1. Implement business logic
            2. Add proper error handling
            3. Include logging
            4. Implement caching where appropriate
            5. Add transaction management
            6. Write unit tests
            """,
            expected_output="""
            Complete service implementations:
            - Service classes with methods
            - Business logic implementation
            - Error handling
            - Unit tests
            - Documentation
            """,
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def implement_api(
        agent: Agent,
        endpoints: List[Dict[str, Any]],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Implement API endpoints"""
        return Task(
            description=f"""
            Implement API endpoints:
            
            Endpoints:
            {endpoints}
            
            Requirements:
            1. RESTful design principles
            2. Input validation
            3. Proper HTTP status codes
            4. Error responses
            5. API documentation (OpenAPI/Swagger)
            6. Rate limiting where needed
            7. Authentication/Authorization checks
            """,
            expected_output="""
            Complete API implementation:
            - Route definitions
            - Controller/Handler implementations
            - Request/Response handling
            - Validation middleware
            - API documentation
            - Integration tests
            """,
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def implement_authentication(
        agent: Agent,
        auth_type: str,
        context: Optional[List[Task]] = None
    ) -> Task:
        """Implement authentication system"""
        return Task(
            description=f"""
            Implement {auth_type} authentication system:
            
            Requirements:
            1. User registration and login
            2. Token generation and validation
            3. Password hashing and security
            4. Token refresh mechanism
            5. Logout/token invalidation
            6. Multi-factor authentication (optional)
            7. Rate limiting for auth endpoints
            """,
            expected_output="""
            Complete authentication implementation:
            - Auth service/module
            - Token management
            - Password security
            - Auth middleware
            - Auth endpoints
            - Security tests
            """,
            agent=agent,
            context=context or []
        )
