"""
Frontend development tasks
"""
from typing import Optional, List, Dict, Any
from crewai import Task, Agent


class FrontendTasks:
    """Tasks for frontend development"""
    
    @staticmethod
    def create_project_structure(
        agent: Agent,
        framework: str,
        project_name: str
    ) -> Task:
        """Create frontend project structure"""
        return Task(
            description=f"""
            Create the project structure for a {framework} application:
            
            Project Name: {project_name}
            
            Create:
            1. Directory structure following best practices
            2. Package configuration
            3. Build tool setup (Vite/Webpack/etc.)
            4. ESLint/Prettier configuration
            5. TypeScript configuration
            6. State management setup
            7. Routing configuration
            8. Testing setup (Jest/Vitest)
            """,
            expected_output="""
            Complete project structure with:
            - All necessary directories (components, pages, hooks, utils, etc.)
            - Configuration files
            - Basic application shell
            - Development tooling
            - README with setup instructions
            """,
            agent=agent
        )
    
    @staticmethod
    def implement_components(
        agent: Agent,
        components: List[Dict[str, Any]],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Implement UI components"""
        return Task(
            description=f"""
            Implement the following UI components:
            
            Components:
            {components}
            
            Requirements:
            1. Responsive design
            2. Accessibility (WCAG 2.1)
            3. Reusable and composable
            4. Proper prop typing
            5. Loading and error states
            6. Unit tests
            """,
            expected_output="""
            Complete component implementations:
            - Component code with props/types
            - Styling (CSS/Tailwind/Styled)
            - Storybook stories (if applicable)
            - Unit tests
            - Documentation
            """,
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def implement_pages(
        agent: Agent,
        pages: List[Dict[str, Any]],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Implement page components"""
        return Task(
            description=f"""
            Implement the following pages:
            
            Pages:
            {pages}
            
            Requirements:
            1. Proper layout and composition
            2. Data fetching integration
            3. Loading states
            4. Error handling
            5. SEO meta tags
            6. Responsive design
            """,
            expected_output="""
            Complete page implementations:
            - Page components
            - Data fetching logic
            - Layout integration
            - Route configuration
            - Tests
            """,
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def implement_state_management(
        agent: Agent,
        state_config: Dict[str, Any],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Implement state management"""
        return Task(
            description=f"""
            Implement state management:
            
            Configuration:
            {state_config}
            
            Requirements:
            1. Global state store setup
            2. Actions and reducers/slices
            3. Selectors for derived state
            4. Async actions for API calls
            5. Persistence if needed
            6. DevTools integration
            """,
            expected_output="""
            Complete state management:
            - Store configuration
            - State slices/modules
            - Actions and reducers
            - Selectors
            - Hooks for accessing state
            - Tests
            """,
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def implement_api_integration(
        agent: Agent,
        api_config: Dict[str, Any],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Implement API integration"""
        return Task(
            description=f"""
            Implement API integration layer:
            
            Configuration:
            {api_config}
            
            Requirements:
            1. API client setup (axios/fetch)
            2. Request/Response interceptors
            3. Error handling
            4. Authentication token management
            5. Request caching
            6. Retry logic
            """,
            expected_output="""
            Complete API integration:
            - API client configuration
            - Service modules for each endpoint
            - Error handling utilities
            - Auth interceptors
            - Types for API responses
            - Tests
            """,
            agent=agent,
            context=context or []
        )
