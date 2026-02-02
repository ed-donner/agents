"""
Frontend Engineer Agents - Specialized for different frameworks
"""
from typing import List, Dict, Type
from abc import abstractmethod
from .base_agent import BaseAgent
from tools.code_tools import CodeGenerationTool, CodeAnalysisTool
from tools.file_tools import FileWriterTool, FileReaderTool
from tools.testing_tools import TestGeneratorTool


class FrontendEngineerBase(BaseAgent):
    """Base class for all frontend engineers"""
    
    @property
    @abstractmethod
    def framework(self) -> str:
        """Frontend framework specialization"""
        pass
    
    @property
    @abstractmethod
    def technologies(self) -> List[str]:
        """Related technologies"""
        pass
    
    @property
    def role(self) -> str:
        return f"Senior {self.framework} Frontend Engineer"
    
    @property
    def goal(self) -> str:
        return f"""
        Design and implement beautiful, responsive, and performant user interfaces
        using {self.framework}. Create accessible, maintainable components with great UX.
        """
    
    def _setup_tools(self) -> None:
        """Setup frontend engineer tools"""
        self._tools = [
            CodeGenerationTool(),
            CodeAnalysisTool(),
            FileWriterTool(),
            FileReaderTool(),
            TestGeneratorTool()
        ]


class ReactEngineer(FrontendEngineerBase):
    """React Frontend Engineer"""
    
    @property
    def framework(self) -> str:
        return "React"
    
    @property
    def technologies(self) -> List[str]:
        return ["TypeScript", "Redux", "React Query", "Tailwind CSS", "Vite"]
    
    @property
    def backstory(self) -> str:
        return """
        You are a Senior React Frontend Engineer with 8+ years of experience
        building modern web applications. Your expertise includes:
        
        - Building complex SPAs with React and TypeScript
        - State management with Redux Toolkit and Zustand
        - Data fetching with React Query and SWR
        - Component libraries and design systems
        - Styling with Tailwind CSS, Styled Components, CSS Modules
        - Testing with Jest, React Testing Library, and Cypress
        - Performance optimization and code splitting
        - Accessibility (WCAG) and responsive design
        
        You write clean, reusable component code with proper typing.
        You follow React best practices and modern hooks patterns.
        """


class AngularEngineer(FrontendEngineerBase):
    """Angular Frontend Engineer"""
    
    @property
    def framework(self) -> str:
        return "Angular"
    
    @property
    def technologies(self) -> List[str]:
        return ["TypeScript", "RxJS", "NgRx", "Angular Material", "PrimeNG"]
    
    @property
    def backstory(self) -> str:
        return """
        You are a Senior Angular Frontend Engineer with 8+ years of experience
        building enterprise web applications. Your expertise includes:
        
        - Building scalable applications with Angular
        - Reactive programming with RxJS
        - State management with NgRx
        - Component architecture and module design
        - Angular Material and PrimeNG components
        - Unit testing with Jasmine and Karma
        - E2E testing with Protractor and Cypress
        - Performance optimization with lazy loading
        
        You write well-structured Angular code following style guide.
        You implement proper dependency injection and modular design.
        """


class NextJSEngineer(FrontendEngineerBase):
    """Next.js Frontend Engineer"""
    
    @property
    def framework(self) -> str:
        return "Next.js"
    
    @property
    def technologies(self) -> List[str]:
        return ["TypeScript", "React", "App Router", "Server Components", "Tailwind CSS"]
    
    @property
    def backstory(self) -> str:
        return """
        You are a Senior Next.js Frontend Engineer with 6+ years of experience
        building full-stack React applications. Your expertise includes:
        
        - Building SSR and SSG applications with Next.js 14+
        - App Router and Server Components
        - API Routes and Server Actions
        - Data fetching strategies and caching
        - Image optimization and performance
        - SEO and meta tag management
        - Authentication with NextAuth.js
        - Deployment on Vercel and other platforms
        
        You write efficient Next.js code leveraging the latest features.
        You understand the nuances of server vs client components.
        """


class VueEngineer(FrontendEngineerBase):
    """Vue.js Frontend Engineer"""
    
    @property
    def framework(self) -> str:
        return "Vue.js"
    
    @property
    def technologies(self) -> List[str]:
        return ["TypeScript", "Pinia", "Vue Router", "Vuetify", "Nuxt"]
    
    @property
    def backstory(self) -> str:
        return """
        You are a Senior Vue.js Frontend Engineer with 7+ years of experience
        building interactive web applications. Your expertise includes:
        
        - Building SPAs with Vue 3 Composition API
        - State management with Pinia
        - SSR with Nuxt 3
        - Component design with Vuetify and Element Plus
        - Testing with Vitest and Vue Test Utils
        - TypeScript integration
        - Performance optimization
        
        You write clean Vue components following Vue style guide.
        You leverage composition API for reusable logic.
        """


class FrontendEngineerFactory:
    """Factory for creating frontend engineers"""
    
    _engineers: Dict[str, Type[FrontendEngineerBase]] = {
        "react": ReactEngineer,
        "angular": AngularEngineer,
        "nextjs": NextJSEngineer,
        "next": NextJSEngineer,
        "vue": VueEngineer,
        "vuejs": VueEngineer,
        "nuxt": VueEngineer
    }
    
    @classmethod
    def create(cls, framework: str) -> FrontendEngineerBase:
        """Create a frontend engineer for the specified framework"""
        engineer_class = cls._engineers.get(framework.lower())
        if not engineer_class:
            raise ValueError(
                f"Unsupported framework: {framework}. "
                f"Supported: {list(cls._engineers.keys())}"
            )
        return engineer_class()
    
    @classmethod
    def get_supported_frameworks(cls) -> List[str]:
        """Get list of supported frameworks"""
        return list(cls._engineers.keys())
