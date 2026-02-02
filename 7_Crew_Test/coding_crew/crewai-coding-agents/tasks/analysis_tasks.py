"""
Analysis and planning tasks
"""
from typing import Optional, List
from crewai import Task, Agent
from models.requirements import ComplexStackRequest


class AnalysisTasks:
    """Tasks for project analysis and planning"""
    
    @staticmethod
    def requirement_analysis(
        agent: Agent,
        request: ComplexStackRequest
    ) -> Task:
        """Create requirement analysis task"""
        return Task(
            description=f"""
            Perform a comprehensive analysis of the project requirements:
            
            PROJECT DETAILS:
            ================
            Name: {request.project_name}
            Description: {request.description}
            
            TECHNICAL REQUIREMENTS:
            =======================
            Backend: {request.backend_language} with {request.backend_framework}
            API Type: {request.api_type}
            Frontend: {request.frontend_framework}
            SSR Required: {request.ssr_required}
            
            DATABASE:
            =========
            Primary: {request.database.primary_db}
            Cache: {request.database.cache_db}
            Search: {request.database.search_db}
            
            INFRASTRUCTURE:
            ===============
            Environment: {request.infrastructure.environment}
            Cloud Provider: {request.infrastructure.cloud_provider}
            High Availability: {request.infrastructure.high_availability}
            
            SECURITY:
            =========
            Authentication: {request.security.authentication}
            Authorization: {request.security.authorization}
            Compliance: {request.security.compliance}
            
            Analyze these requirements and provide:
            1. Technical feasibility assessment
            2. Risk analysis
            3. Resource requirements
            4. Timeline estimates
            5. Recommended approach
            """,
            expected_output="""
            Comprehensive analysis document with:
            - Executive summary
            - Technical feasibility report
            - Risk matrix with mitigation strategies
            - Resource and skill requirements
            - Recommended timeline with milestones
            - Success criteria and KPIs
            """,
            agent=agent
        )
    
    @staticmethod
    def architecture_design(
        agent: Agent,
        request: ComplexStackRequest,
        context: Optional[List[Task]] = None
    ) -> Task:
        """Create architecture design task"""
        return Task(
            description=f"""
            Based on the analyzed requirements, design the system architecture:
            
            PROJECT: {request.project_name}
            
            KEY REQUIREMENTS:
            - Scalability: Support growing user base
            - Performance: Low latency responses
            - Reliability: High availability ({request.infrastructure.high_availability})
            - Security: {request.security.authentication}, {request.security.authorization}
            
            CONSTRAINTS:
            - Cloud Provider: {request.infrastructure.cloud_provider}
            - Backend: {request.backend_language}/{request.backend_framework}
            - Frontend: {request.frontend_framework}
            - Database: {request.database.primary_db}
            
            Design should include:
            1. High-level architecture diagram (describe in text)
            2. Component breakdown
            3. Data flow design
            4. Integration patterns
            5. Scalability strategy
            6. Security architecture
            """,
            expected_output="""
            Complete architecture design document:
            - Architecture diagram description
            - Component specifications
            - API contracts overview
            - Data model design
            - Integration patterns
            - Security measures
            - Scalability approach
            - Deployment architecture
            """,
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def task_decomposition(
        agent: Agent,
        request: ComplexStackRequest,
        context: Optional[List[Task]] = None
    ) -> Task:
        """Decompose project into development tasks"""
        return Task(
            description=f"""
            Based on the architecture design, decompose the project into detailed tasks:
            
            PROJECT: {request.project_name}
            
            Break down the project into:
            1. Backend development tasks
            2. Frontend development tasks
            3. Database tasks
            4. Infrastructure tasks
            5. CI/CD pipeline tasks
            6. Testing tasks
            7. Documentation tasks
            
            For each task, specify:
            - Task name and description
            - Required skills/agent type
            - Dependencies on other tasks
            - Estimated effort (hours)
            - Priority level
            - Acceptance criteria
            """,
            expected_output="""
            Detailed task breakdown:
            - Categorized task list
            - Task dependencies graph
            - Effort estimates
            - Priority assignments
            - Sprint/phase groupings
            - Critical path identification
            """,
            agent=agent,
            context=context or []
        )
