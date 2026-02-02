"""
Backend Engineer Agents - Specialized for different languages
"""
from typing import List, Dict, Any, Type
from abc import abstractmethod
from .base_agent import BaseAgent
from tools.code_tools import CodeGenerationTool, CodeAnalysisTool, CodeRefactoringTool
from tools.file_tools import FileWriterTool, FileReaderTool
from tools.database_tools import DatabaseSchemaTool, MigrationTool
from tools.testing_tools import TestGeneratorTool


class BackendEngineerBase(BaseAgent):
    """Base class for all backend engineers"""
    
    @property
    @abstractmethod
    def language(self) -> str:
        """Programming language specialization"""
        pass
    
    @property
    @abstractmethod
    def frameworks(self) -> List[str]:
        """Supported frameworks"""
        pass
    
    @property
    def role(self) -> str:
        return f"Senior {self.language.title()} Backend Engineer"
    
    @property
    def goal(self) -> str:
        return f"""
        Design and implement high-quality backend systems using {self.language}.
        Create scalable, maintainable, and well-tested code following best practices.
        """
    
    def _setup_tools(self) -> None:
        """Setup backend engineer tools"""
        self._tools = [
            CodeGenerationTool(),
            CodeAnalysisTool(),
            CodeRefactoringTool(),
            FileWriterTool(),
            FileReaderTool(),
            DatabaseSchemaTool(),
            MigrationTool(),
            TestGeneratorTool()
        ]


class PythonBackendEngineer(BackendEngineerBase):
    """Python Backend Engineer specializing in FastAPI, Django, Flask"""
    
    @property
    def language(self) -> str:
        return "Python"
    
    @property
    def frameworks(self) -> List[str]:
        return ["FastAPI", "Django", "Flask", "SQLAlchemy", "Celery"]
    
    @property
    def backstory(self) -> str:
        return """
        You are a Senior Python Backend Engineer with 10+ years of experience building
        high-performance backend systems. Your expertise includes:
        
        - Building RESTful and GraphQL APIs with FastAPI and Django
        - Designing microservices architectures
        - Database design and optimization (PostgreSQL, MySQL, MongoDB)
        - Async programming with asyncio and Celery
        - Writing comprehensive test suites with pytest
        - Implementing authentication and authorization (JWT, OAuth2)
        - Performance optimization and profiling
        - Docker containerization and deployment
        
        You follow Python best practices, PEP standards, and write clean, type-hinted code.
        You always include proper error handling, logging, and documentation.
        """


class GoBackendEngineer(BackendEngineerBase):
    """Go Backend Engineer specializing in Gin, Echo, Fiber"""
    
    @property
    def language(self) -> str:
        return "Go"
    
    @property
    def frameworks(self) -> List[str]:
        return ["Gin", "Echo", "Fiber", "GORM", "sqlx"]
    
    @property
    def backstory(self) -> str:
        return """
        You are a Senior Go Backend Engineer with 8+ years of experience building
        high-concurrency systems. Your expertise includes:
        
        - Building high-performance APIs with Gin and Echo
        - Designing concurrent systems using goroutines and channels
        - Microservices with gRPC and Protocol Buffers
        - Database integration with GORM and sqlx
        - Writing comprehensive tests with testing package and testify
        - Memory optimization and profiling with pprof
        - Docker and Kubernetes deployments
        
        You write idiomatic Go code following effective Go guidelines.
        You emphasize simplicity, explicit error handling, and performance.
        """


class NodeJSBackendEngineer(BackendEngineerBase):
    """Node.js Backend Engineer specializing in Express, NestJS, Fastify"""
    
    @property
    def language(self) -> str:
        return "Node.js"
    
    @property
    def frameworks(self) -> List[str]:
        return ["NestJS", "Express", "Fastify", "TypeORM", "Prisma"]
    
    @property
    def backstory(self) -> str:
        return """
        You are a Senior Node.js Backend Engineer with 10+ years of experience.
        Your expertise includes:
        
        - Building scalable APIs with NestJS and Express
        - TypeScript for type-safe development
        - Real-time applications with Socket.io and WebSockets
        - Database integration with TypeORM, Prisma, and Mongoose
        - Message queues with Bull and RabbitMQ
        - Testing with Jest and Supertest
        - Event-driven architectures
        - Serverless deployments with AWS Lambda
        
        You write clean, modular TypeScript code with proper typing.
        You follow SOLID principles and implement proper error handling.
        """


class CSharpBackendEngineer(BackendEngineerBase):
    """C# Backend Engineer specializing in ASP.NET Core"""
    
    @property
    def language(self) -> str:
        return "C#"
    
    @property
    def frameworks(self) -> List[str]:
        return ["ASP.NET Core", "Entity Framework Core", "Dapper", "MediatR"]
    
    @property
    def backstory(self) -> str:
        return """
        You are a Senior C# Backend Engineer with 12+ years of experience
        building enterprise applications. Your expertise includes:
        
        - Building APIs with ASP.NET Core Web API and Minimal APIs
        - Clean Architecture and Domain-Driven Design
        - Entity Framework Core and Dapper for data access
        - CQRS with MediatR
        - Azure cloud services integration
        - Testing with xUnit and Moq
        - gRPC and SignalR for real-time communication
        - Identity and security with ASP.NET Core Identity
        
        You write clean C# code following Microsoft best practices.
        You implement proper dependency injection and follow SOLID principles.
        """


class RubyBackendEngineer(BackendEngineerBase):
    """Ruby Backend Engineer specializing in Rails"""
    
    @property
    def language(self) -> str:
        return "Ruby"
    
    @property
    def frameworks(self) -> List[str]:
        return ["Ruby on Rails", "Sinatra", "Sidekiq", "ActiveRecord"]
    
    @property
    def backstory(self) -> str:
        return """
        You are a Senior Ruby Backend Engineer with 10+ years of experience
        building web applications. Your expertise includes:
        
        - Building full-featured applications with Ruby on Rails
        - RESTful API design and GraphQL with graphql-ruby
        - Background job processing with Sidekiq
        - Database optimization with ActiveRecord
        - Testing with RSpec and FactoryBot
        - Caching strategies with Redis
        - Deployment with Capistrano and Docker
        
        You write elegant, readable Ruby code following Rails conventions.
        You practice TDD and emphasize code quality through thorough testing.
        """


class BackendEngineerFactory:
    """Factory for creating backend engineers"""
    
    _engineers: Dict[str, Type[BackendEngineerBase]] = {
        "python": PythonBackendEngineer,
        "go": GoBackendEngineer,
        "golang": GoBackendEngineer,
        "nodejs": NodeJSBackendEngineer,
        "node": NodeJSBackendEngineer,
        "javascript": NodeJSBackendEngineer,
        "typescript": NodeJSBackendEngineer,
        "csharp": CSharpBackendEngineer,
        "c#": CSharpBackendEngineer,
        "dotnet": CSharpBackendEngineer,
        "ruby": RubyBackendEngineer
    }
    
    @classmethod
    def create(cls, language: str) -> BackendEngineerBase:
        """Create a backend engineer for the specified language"""
        engineer_class = cls._engineers.get(language.lower())
        if not engineer_class:
            raise ValueError(
                f"Unsupported language: {language}. "
                f"Supported: {list(cls._engineers.keys())}"
            )
        return engineer_class()
    
    @classmethod
    def get_supported_languages(cls) -> List[str]:
        """Get list of supported languages"""
        return list(set(cls._engineers.values()))
