"""
Testing and QA tasks
"""
from typing import Optional, List, Dict, Any
from crewai import Task, Agent


class TestingTasks:
    """Tasks for testing and quality assurance"""
    
    @staticmethod
    def create_test_strategy(
        agent: Agent,
        project_config: Dict[str, Any]
    ) -> Task:
        """Create testing strategy"""
        return Task(
            description=f"""
            Create a comprehensive testing strategy for:
            
            Project:
            {project_config}
            
            Define:
            1. Testing levels (unit, integration, e2e)
            2. Coverage requirements
            3. Testing tools and frameworks
            4. Test data management
            5. CI/CD integration
            6. Performance testing approach
            7. Security testing approach
            """,
            expected_output="""
            Complete testing strategy document:
            - Test pyramid definition
            - Tool selection rationale
            - Coverage targets
            - Test environment requirements
            - CI/CD integration plan
            - Timeline and milestones
            """,
            agent=agent
        )
    
    @staticmethod
    def implement_unit_tests(
        agent: Agent,
        components: List[str],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Implement unit tests"""
        return Task(
            description=f"""
            Implement unit tests for:
            
            Components:
            {components}
            
            Requirements:
            1. Test all public methods
            2. Cover edge cases
            3. Mock external dependencies
            4. Achieve >80% coverage
            5. Use descriptive test names
            6. Include setup/teardown
            """,
            expected_output="""
            Complete unit test suite:
            - Test files for each component
            - Mock definitions
            - Test utilities/helpers
            - Coverage report configuration
            """,
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def implement_integration_tests(
        agent: Agent,
        api_endpoints: List[Dict[str, Any]],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Implement integration tests"""
        return Task(
            description=f"""
            Implement integration tests for:
            
            Endpoints:
            {api_endpoints}
            
            Requirements:
            1. Test API endpoints
            2. Test database operations
            3. Test external service integrations
            4. Use test containers
            5. Proper test data setup/cleanup
            6. Authentication testing
            """,
            expected_output="""
            Complete integration test suite:
            - API test files
            - Database test utilities
            - Test containers configuration
            - Test fixtures
            """,
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def implement_e2e_tests(
        agent: Agent,
        user_flows: List[Dict[str, Any]],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Implement E2E tests"""
        return Task(
            description=f"""
            Implement E2E tests for:
            
            User Flows:
            {user_flows}
            
            Requirements:
            1. Test critical user journeys
            2. Cross-browser testing
            3. Mobile responsiveness
            4. Performance assertions
            5. Visual regression (optional)
            6. Accessibility checks
            """,
            expected_output="""
            Complete E2E test suite:
            - Playwright/Cypress test files
            - Page objects
            - Test fixtures
            - CI configuration
            """,
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def implement_performance_tests(
        agent: Agent,
        performance_config: Dict[str, Any],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Implement performance tests"""
        return Task(
            description=f"""
            Implement performance tests for:
            
            Configuration:
            {performance_config}
            
            Requirements:
            1. Load testing scenarios
            2. Stress testing
            3. Endurance testing
            4. Spike testing
            5. Define SLOs and thresholds
            6. CI/CD integration
            """,
            expected_output="""
            Complete performance test suite:
            - k6/JMeter test scripts
            - Threshold definitions
            - Result analysis scripts
            - CI configuration
            """,
            agent=agent,
            context=context or []
        )
