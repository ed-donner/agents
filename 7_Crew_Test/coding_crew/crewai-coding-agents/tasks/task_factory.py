"""
Task Factory for creating CrewAI tasks
"""
from typing import List, Dict, Any, Optional
from crewai import Task, Agent
from models.requirements import ComplexStackRequest


class TaskFactory:
    """Factory for creating project tasks"""
    
    @staticmethod
    def create_analysis_task(
        agent: Agent,
        request: ComplexStackRequest,
        context: Optional[List[Task]] = None
    ) -> Task:
        """Create requirement analysis task"""
        return Task(
            description=f"""
            Analyze the following project requirements and create a detailed technical specification:
            
            Project: {request.project_name}
            Description: {request.description}
            
            Backend: {request.backend_language} with {request.backend_framework}
            Frontend: {request.frontend_framework}
            Database: {request.database.model_dump_json()}
            Infrastructure: {request.infrastructure.model_dump_json()}
            
            Your analysis should include:
            1. Detailed component breakdown
            2. Technology stack recommendations
            3. Architecture pattern suggestions
            4. Potential challenges and mitigation strategies
            5. Development timeline estimates
            """,
            expected_output="""
            A comprehensive technical specification document including:
            - System architecture overview
            - Component specifications
            - Technology stack details
            - API design guidelines
            - Data model overview
            - Infrastructure requirements
            - Security considerations
            - Timeline and milestones
            """,
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def create_architecture_task(
        agent: Agent,
        request: ComplexStackRequest,
        context: Optional[List[Task]] = None
    ) -> Task:
        """Create architecture design task"""
        return Task(
            description=f"""
            Design the system architecture for:
            
            Project: {request.project_name}
            
            Requirements:
            - Backend: {request.backend_language}/{request.backend_framework}
            - Frontend: {request.frontend_framework}
            - Database: {request.database.primary_db}
            - Cache: {request.database.cache_db}
            - Infrastructure: {request.infrastructure.cloud_provider}
            - Microservices: {request.microservices or 'Not specified'}
            
            Design a scalable, maintainable architecture that:
            1. Follows best practices for the chosen stack
            2. Supports high availability requirements
            3. Enables horizontal scaling
            4. Provides clear separation of concerns
            """,
            expected_output="""
            Complete architecture design including:
            - System architecture diagram description
            - Component interaction flows
            - Data flow diagrams
            - API gateway design
            - Service mesh configuration (if applicable)
            - Database schema overview
            - Caching strategy
            - Security architecture
            """,
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def create_backend_task(
        agent: Agent,
        component: str,
        specifications: Dict[str, Any],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Create backend development task"""
        return Task(
            description=f"""
            Implement the {component} backend component with the following specifications:
            
            {specifications}
            
            Requirements:
            1. Follow clean code principles
            2. Implement proper error handling
            3. Add comprehensive logging
            4. Include input validation
            5. Write unit tests for all functions
            6. Add API documentation
            """,
            expected_output=f"""
            Complete implementation of {component} including:
            - Model/Schema definitions
            - Service layer with business logic
            - Controller/Router with endpoints
            - Unit tests with high coverage
            - API documentation
            """,
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def create_frontend_task(
        agent: Agent,
        component: str,
        specifications: Dict[str, Any],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Create frontend development task"""
        return Task(
            description=f"""
            Implement the {component} frontend component with the following specifications:
            
            {specifications}
            
            Requirements:
            1. Follow component-based architecture
            2. Implement responsive design
            3. Ensure accessibility (WCAG 2.1)
            4. Add proper state management
            5. Write component tests
            6. Optimize for performance
            """,
            expected_output=f"""
            Complete implementation of {component} including:
            - React/Angular/Vue component code
            - Styling (CSS/Tailwind/Styled Components)
            - State management integration
            - Component tests
            - Storybook stories (if applicable)
            """,
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def create_database_task(
        agent: Agent,
        database_config: Dict[str, Any],
        entities: List[Dict[str, Any]],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Create database design task"""
        return Task(
            description=f"""
            Design and implement the database schema for:
            
            Database Configuration:
            {database_config}
            
            Entities:
            {entities}
            
            Requirements:
            1. Optimize for read/write patterns
            2. Design proper indexes
            3. Implement referential integrity
            4. Plan for data growth
            5. Create migration scripts
            """,
            expected_output="""
            Complete database implementation including:
            - Schema definitions (DDL)
            - Index definitions
            - Migration scripts
            - Seed data scripts
            - Query optimization recommendations
            """,
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def create_infrastructure_task(
        agent: Agent,
        infra_config: Dict[str, Any],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Create infrastructure task"""
        return Task(
            description=f"""
            Design and implement infrastructure for:
            
            Configuration:
            {infra_config}
            
            Requirements:
            1. High availability setup
            2. Auto-scaling configuration
            3. Security best practices
            4. Cost optimization
            5. Monitoring and alerting
            """,
            expected_output="""
            Complete infrastructure implementation including:
            - Terraform/Pulumi configurations
            - Kubernetes manifests
            - Networking setup
            - Security configurations
            - Monitoring stack setup
            """,
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def create_cicd_task(
        agent: Agent,
        cicd_config: Dict[str, Any],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Create CI/CD pipeline task"""
        return Task(
            description=f"""
            Design and implement CI/CD pipelines for:
            
            Configuration:
            {cicd_config}
            
            Requirements:
            1. Automated testing at all stages
            2. Security scanning (SAST, DAST)
            3. Container image building
            4. Deployment automation
            5. Rollback capabilities
            """,
            expected_output="""
            Complete CI/CD implementation including:
            - Pipeline configuration files
            - Build scripts
            - Deployment scripts
            - Environment configurations
            - Rollback procedures
            """,
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def create_testing_task(
        agent: Agent,
        test_config: Dict[str, Any],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Create testing task"""
        return Task(
            description=f"""
            Design and implement comprehensive test suites for:
            
            Configuration:
            {test_config}
            
            Requirements:
            1. Unit tests with high coverage
            2. Integration tests for APIs
            3. E2E tests for critical flows
            4. Performance test scripts
            5. Security test cases
            """,
            expected_output="""
            Complete test implementation including:
            - Unit test suites
            - Integration test suites
            - E2E test suites
            - Performance test scripts
            - Test documentation
            """,
            agent=agent,
            context=context or []
        )
