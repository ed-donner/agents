set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     CrewAI Coding Agent Ecosystem - Setup Script             ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# Renk tanımları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Proje dizini
PROJECT_NAME="crewai-coding-agents"
PROJECT_DIR="$(pwd)/$PROJECT_NAME"

echo -e "${BLUE}📁 Creating project directory: $PROJECT_DIR${NC}"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Dizin yapısını oluştur
echo -e "${BLUE}📂 Creating directory structure...${NC}"

directories=(
    "config"
    "models"
    "agents/specialized"
    "tools"
    "tasks"
    "crews"
    "workflows"
    "templates/backend/python"
    "templates/backend/go"
    "templates/backend/nodejs"
    "templates/backend/csharp"
    "templates/frontend/react"
    "templates/frontend/angular"
    "templates/frontend/nextjs"
    "templates/infrastructure/terraform"
    "templates/infrastructure/kubernetes"
    "templates/infrastructure/ansible"
    "templates/cicd"
    "templates/database"
    "output"
    "logs"
    "tests"
    "examples"
)

for dir in "${directories[@]}"; do
    mkdir -p "$dir"
    echo -e "${GREEN}  ✓ Created: $dir${NC}"
done

# ============================================================
# DOSYA 1: requirements.txt
# ============================================================
echo -e "${BLUE}📄 Creating requirements.txt...${NC}"
cat > requirements.txt << 'EOF'
# CrewAI Core
crewai==0.30.11
crewai-tools==0.2.6

# LangChain
langchain>=0.1.0
langchain-openai>=0.0.8
langchain-anthropic>=0.1.1
langchain-community>=0.0.20

# Pydantic
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Async Support
asyncio>=3.4.3
aiohttp>=3.9.1
aiofiles>=23.2.1

# HTTP Client
httpx>=0.26.0
requests>=2.31.0

# CLI & UI
rich>=13.7.0
typer>=0.9.0
click>=8.1.7

# YAML & Templates
PyYAML>=6.0.1
Jinja2>=3.1.2

# Testing
pytest>=7.4.3
pytest-asyncio>=0.23.2
pytest-cov>=4.1.0
pytest-mock>=3.12.0

# Utilities
python-dotenv>=1.0.0
tenacity>=8.2.3

# Optional: Redis for caching
redis>=5.0.1

# Optional: Database
sqlalchemy>=2.0.23

# Logging
loguru>=0.7.2
EOF

# ============================================================
# DOSYA 2: .env.example
# ============================================================
echo -e "${BLUE}📄 Creating .env.example...${NC}"
cat > .env.example << 'EOF'
# LLM API Keys (Choose one or more)
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Default LLM Configuration
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-4-turbo-preview
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=4096

# CrewAI Settings
CREWAI_VERBOSE=true
CREWAI_MEMORY=true
CREWAI_MAX_RPM=10

# Application Settings
LOG_LEVEL=INFO
OUTPUT_DIR=./output
TEMPLATE_DIR=./templates

# Optional: Redis Cache
REDIS_URL=redis://localhost:6379

# Optional: Database
DATABASE_URL=sqlite:///./crewai_agents.db
EOF

# ============================================================
# DOSYA 3: config/__init__.py
# ============================================================
echo -e "${BLUE}📄 Creating config/__init__.py...${NC}"
cat > config/__init__.py << 'EOF'
from .settings import settings, Settings
from .llm_config import get_llm, LLMConfig

__all__ = ["settings", "Settings", "get_llm", "LLMConfig"]
EOF

# ============================================================
# DOSYA 4: config/settings.py
# ============================================================
echo -e "${BLUE}📄 Creating config/settings.py...${NC}"
cat > config/settings.py << 'EOF'
"""
Global settings and configuration management
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache


class EnvironmentType(str, Enum):
    """Deployment environment types"""
    CLOUD = "cloud"
    ONPREM = "onprem"
    HYBRID = "hybrid"


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentRole(str, Enum):
    """Available agent roles"""
    TEAM_MANAGER = "team_manager"
    ANALYST = "analyst"
    BACKEND_PYTHON = "backend_python"
    BACKEND_GO = "backend_go"
    BACKEND_NODEJS = "backend_nodejs"
    BACKEND_CSHARP = "backend_csharp"
    BACKEND_RUBY = "backend_ruby"
    FRONTEND_REACT = "frontend_react"
    FRONTEND_ANGULAR = "frontend_angular"
    FRONTEND_NEXTJS = "frontend_nextjs"
    DEVOPS = "devops"
    SYSTEM_ENGINEER = "system_engineer"
    CLOUD_ENGINEER = "cloud_engineer"
    DB_ENGINEER = "db_engineer"
    QA_ENGINEER = "qa_engineer"
    SECURITY_ENGINEER = "security_engineer"


class Settings(BaseSettings):
    """Application settings loaded from environment"""
    
    # LLM Configuration
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    default_llm_provider: str = Field(default="openai", alias="DEFAULT_LLM_PROVIDER")
    default_llm_model: str = Field(default="gpt-4-turbo-preview", alias="DEFAULT_LLM_MODEL")
    default_temperature: float = Field(default=0.7, alias="DEFAULT_TEMPERATURE")
    default_max_tokens: int = Field(default=4096, alias="DEFAULT_MAX_TOKENS")
    
    # CrewAI Settings
    crewai_verbose: bool = Field(default=True, alias="CREWAI_VERBOSE")
    crewai_memory: bool = Field(default=True, alias="CREWAI_MEMORY")
    crewai_max_rpm: int = Field(default=10, alias="CREWAI_MAX_RPM")
    
    # Application Settings
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    output_dir: str = Field(default="./output", alias="OUTPUT_DIR")
    template_dir: str = Field(default="./templates", alias="TEMPLATE_DIR")
    
    # Optional Services
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
EOF

# ============================================================
# DOSYA 5: config/llm_config.py
# ============================================================
echo -e "${BLUE}📄 Creating config/llm_config.py...${NC}"
cat > config/llm_config.py << 'EOF'
"""
LLM Configuration and Factory
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from .settings import settings


@dataclass
class LLMConfig:
    """LLM configuration container"""
    provider: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
):
    """
    Factory function to create LLM instances
    
    Args:
        provider: LLM provider (openai, anthropic)
        model: Model name
        temperature: Sampling temperature
        max_tokens: Maximum tokens for response
    
    Returns:
        LangChain LLM instance
    """
    provider = provider or settings.default_llm_provider
    model = model or settings.default_llm_model
    temperature = temperature if temperature is not None else settings.default_temperature
    max_tokens = max_tokens or settings.default_max_tokens
    
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.openai_api_key
        )
    elif provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.anthropic_api_key
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


# Predefined LLM configurations for different agent types
LLM_CONFIGS = {
    "manager": LLMConfig(
        provider="openai",
        model="gpt-4-turbo-preview",
        temperature=0.7,
        max_tokens=4096
    ),
    "coder": LLMConfig(
        provider="openai",
        model="gpt-4-turbo-preview",
        temperature=0.3,
        max_tokens=8192
    ),
    "analyst": LLMConfig(
        provider="openai",
        model="gpt-4-turbo-preview",
        temperature=0.5,
        max_tokens=4096
    ),
    "creative": LLMConfig(
        provider="openai",
        model="gpt-4-turbo-preview",
        temperature=0.8,
        max_tokens=4096
    )
}


def get_llm_for_role(role: str):
    """Get appropriate LLM for agent role"""
    config = LLM_CONFIGS.get(role, LLM_CONFIGS["coder"])
    return get_llm(
        provider=config.provider,
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens
    )
EOF

# ============================================================
# DOSYA 6: models/__init__.py
# ============================================================
echo -e "${BLUE}📄 Creating models/__init__.py...${NC}"
cat > models/__init__.py << 'EOF'
from .requirements import (
    DatabaseRequirement,
    InfrastructureRequirement,
    SecurityRequirement,
    QueueRequirement,
    ComplexStackRequest
)
from .project import (
    TaskDefinition,
    ProjectArchitecture,
    Project
)

__all__ = [
    "DatabaseRequirement",
    "InfrastructureRequirement",
    "SecurityRequirement",
    "QueueRequirement",
    "ComplexStackRequest",
    "TaskDefinition",
    "ProjectArchitecture",
    "Project"
]
EOF

# ============================================================
# DOSYA 7: models/requirements.py
# ============================================================
echo -e "${BLUE}📄 Creating models/requirements.py...${NC}"
cat > models/requirements.py << 'EOF'
"""
Request and requirement models for project configuration
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from config.settings import EnvironmentType


class DatabaseRequirement(BaseModel):
    """Database configuration requirements"""
    primary_db: Dict[str, Any] = Field(
        default={"type": "postgresql", "version": "15"},
        description="Primary database configuration"
    )
    cache_db: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Cache database (Redis, Memcached)"
    )
    search_db: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Search engine (Elasticsearch, OpenSearch)"
    )
    document_db: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Document database (MongoDB)"
    )
    replication: bool = Field(default=False, description="Enable database replication")
    sharding: bool = Field(default=False, description="Enable database sharding")


class InfrastructureRequirement(BaseModel):
    """Infrastructure configuration requirements"""
    environment: EnvironmentType = Field(
        default=EnvironmentType.CLOUD,
        description="Deployment environment type"
    )
    cloud_provider: Optional[str] = Field(
        default="AWS",
        description="Cloud provider (AWS, Azure, GCP)"
    )
    regions: List[str] = Field(
        default=["us-east-1"],
        description="Deployment regions"
    )
    high_availability: bool = Field(
        default=True,
        description="Enable high availability setup"
    )
    disaster_recovery: bool = Field(
        default=False,
        description="Enable disaster recovery"
    )
    kubernetes_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Kubernetes cluster configuration"
    )


class SecurityRequirement(BaseModel):
    """Security configuration requirements"""
    authentication: str = Field(
        default="JWT",
        description="Authentication method (JWT, OAuth2, SAML)"
    )
    authorization: str = Field(
        default="RBAC",
        description="Authorization method (RBAC, ABAC)"
    )
    encryption: bool = Field(
        default=True,
        description="Enable data encryption"
    )
    waf: bool = Field(
        default=False,
        description="Enable Web Application Firewall"
    )
    ddos_protection: bool = Field(
        default=False,
        description="Enable DDoS protection"
    )
    compliance: List[str] = Field(
        default=[],
        description="Compliance requirements (PCI-DSS, GDPR, SOC2)"
    )


class QueueRequirement(BaseModel):
    """Message queue configuration requirements"""
    type: str = Field(
        default="RabbitMQ",
        description="Queue type (RabbitMQ, Kafka, SQS)"
    )
    use_cases: List[str] = Field(
        default=[],
        description="Queue use cases"
    )
    expected_throughput: Optional[str] = Field(
        default=None,
        description="Expected message throughput"
    )


class ComplexStackRequest(BaseModel):
    """Complete project stack request"""
    # Project Info
    project_name: str = Field(..., description="Project name")
    description: str = Field(..., description="Project description")
    
    # Backend Configuration
    backend_language: str = Field(
        default="python",
        description="Backend programming language"
    )
    backend_framework: str = Field(
        default="FastAPI",
        description="Backend framework"
    )
    api_type: str = Field(
        default="REST",
        description="API type (REST, GraphQL, gRPC)"
    )
    microservices: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Microservices configuration"
    )
    
    # Frontend Configuration
    frontend_framework: str = Field(
        default="react",
        description="Frontend framework"
    )
    ssr_required: bool = Field(
        default=False,
        description="Server-side rendering required"
    )
    
    # Database Configuration
    database: DatabaseRequirement = Field(
        default_factory=DatabaseRequirement,
        description="Database requirements"
    )
    
    # Message Queue
    queue: Optional[QueueRequirement] = Field(
        default=None,
        description="Message queue requirements"
    )
    
    # Infrastructure
    infrastructure: InfrastructureRequirement = Field(
        default_factory=InfrastructureRequirement,
        description="Infrastructure requirements"
    )
    
    # Security
    security: SecurityRequirement = Field(
        default_factory=SecurityRequirement,
        description="Security requirements"
    )
    
    # CI/CD
    cicd_platform: str = Field(
        default="github_actions",
        description="CI/CD platform"
    )
    deployment_strategy: str = Field(
        default="rolling",
        description="Deployment strategy (rolling, blue-green, canary)"
    )
    
    # Monitoring
    monitoring_stack: List[str] = Field(
        default=["prometheus", "grafana"],
        description="Monitoring tools"
    )
    
    # Additional Options
    session_management: Optional[str] = Field(
        default=None,
        description="Session management solution"
    )
    rate_limiting: bool = Field(
        default=True,
        description="Enable rate limiting"
    )
    api_gateway: Optional[str] = Field(
        default=None,
        description="API Gateway solution"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_name": "E-Commerce Platform",
                "description": "Modern e-commerce platform with microservices",
                "backend_language": "python",
                "backend_framework": "FastAPI",
                "frontend_framework": "react",
                "database": {
                    "primary_db": {"type": "postgresql", "version": "15"},
                    "cache_db": {"type": "redis"}
                },
                "infrastructure": {
                    "environment": "cloud",
                    "cloud_provider": "AWS"
                }
            }
        }
EOF

# ============================================================
# DOSYA 8: models/project.py
# ============================================================
echo -e "${BLUE}📄 Creating models/project.py...${NC}"
cat > models/project.py << 'EOF'
"""
Project and task models
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

from config.settings import TaskStatus, TaskPriority


class TaskDefinition(BaseModel):
    """Task definition for agent execution"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    assigned_to: str
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = Field(default_factory=list)
    estimated_hours: float = 1.0
    actual_hours: Optional[float] = None
    output: Optional[Any] = None
    error: Optional[str] = None
    callbacks: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class ServiceDefinition(BaseModel):
    """Microservice definition"""
    name: str
    description: str
    language: str
    framework: str
    port: int
    endpoints: List[Dict[str, Any]] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    database: Optional[str] = None
    cache: Optional[str] = None


class ProjectArchitecture(BaseModel):
    """Project architecture definition"""
    pattern: str = "monolith"  # monolith, microservices, modular_monolith
    services: List[ServiceDefinition] = Field(default_factory=list)
    api_gateway: Optional[str] = None
    service_mesh: Optional[str] = None
    event_bus: Optional[str] = None
    diagram: Optional[str] = None


class Project(BaseModel):
    """Complete project definition"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    status: str = "pending"
    architecture: Optional[ProjectArchitecture] = None
    tasks: List[TaskDefinition] = Field(default_factory=list)
    generated_files: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def add_task(self, task: TaskDefinition):
        """Add a task to the project"""
        self.tasks.append(task)
        self.updated_at = datetime.now()
    
    def get_task(self, task_id: str) -> Optional[TaskDefinition]:
        """Get task by ID"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def update_task_status(self, task_id: str, status: TaskStatus, output: Any = None):
        """Update task status"""
        task = self.get_task(task_id)
        if task:
            task.status = status
            if status == TaskStatus.IN_PROGRESS and not task.started_at:
                task.started_at = datetime.now()
            elif status == TaskStatus.COMPLETED:
                task.completed_at = datetime.now()
                task.output = output
            self.updated_at = datetime.now()
    
    def get_progress(self) -> Dict[str, Any]:
        """Calculate project progress"""
        total = len(self.tasks)
        if total == 0:
            return {"total": 0, "completed": 0, "percentage": 0}
        
        completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        in_progress = sum(1 for t in self.tasks if t.status == TaskStatus.IN_PROGRESS)
        failed = sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)
        blocked = sum(1 for t in self.tasks if t.status == TaskStatus.BLOCKED)
        
        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "failed": failed,
            "blocked": blocked,
            "pending": total - completed - in_progress - failed - blocked,
            "percentage": round((completed / total) * 100, 2)
        }
EOF

# ============================================================
# DOSYA 9: tools/__init__.py
# ============================================================
echo -e "${BLUE}📄 Creating tools/__init__.py...${NC}"
cat > tools/__init__.py << 'EOF'
from .code_tools import (
    CodeGenerationTool,
    CodeAnalysisTool,
    CodeRefactoringTool
)
from .file_tools import (
    FileWriterTool,
    FileReaderTool,
    DirectoryTool
)
from .infrastructure_tools import (
    TerraformTool,
    KubernetesTool,
    DockerTool,
    AnsibleTool
)
from .cicd_tools import (
    GitHubActionsTool,
    GitLabCITool,
    JenkinsTool
)
from .database_tools import (
    DatabaseSchemaTool,
    MigrationTool
)
from .testing_tools import (
    TestGeneratorTool,
    TestRunnerTool
)

__all__ = [
    "CodeGenerationTool",
    "CodeAnalysisTool",
    "CodeRefactoringTool",
    "FileWriterTool",
    "FileReaderTool",
    "DirectoryTool",
    "TerraformTool",
    "KubernetesTool",
    "DockerTool",
    "AnsibleTool",
    "GitHubActionsTool",
    "GitLabCITool",
    "JenkinsTool",
    "DatabaseSchemaTool",
    "MigrationTool",
    "TestGeneratorTool",
    "TestRunnerTool"
]
EOF

# ============================================================
# DOSYA 10: tools/code_tools.py
# ============================================================
echo -e "${BLUE}📄 Creating tools/code_tools.py...${NC}"
cat > tools/code_tools.py << 'EOF'
"""
Code generation and analysis tools for agents
"""
from typing import Type, Any, Optional
from pydantic import BaseModel, Field
from crewai_tools import BaseTool


class CodeGenerationInput(BaseModel):
    """Input schema for code generation"""
    language: str = Field(..., description="Programming language (python, go, nodejs, csharp)")
    framework: str = Field(..., description="Framework to use")
    component_type: str = Field(..., description="Type of component (model, service, controller, etc.)")
    component_name: str = Field(..., description="Name of the component")
    specifications: str = Field(..., description="Detailed specifications for the component")


class CodeGenerationTool(BaseTool):
    name: str = "Code Generation Tool"
    description: str = """
    Generates production-ready code based on specifications.
    Supports multiple languages and frameworks.
    Use this tool when you need to create new code files.
    """
    args_schema: Type[BaseModel] = CodeGenerationInput
    
    def _run(
        self,
        language: str,
        framework: str,
        component_type: str,
        component_name: str,
        specifications: str
    ) -> str:
        """Generate code based on specifications"""
        # This is a placeholder - actual implementation would use LLM
        template = self._get_template(language, framework, component_type)
        
        code_output = f"""
# Generated {component_type}: {component_name}
# Language: {language}
# Framework: {framework}

{template}

# Specifications implemented:
# {specifications}
"""
        return code_output
    
    def _get_template(self, language: str, framework: str, component_type: str) -> str:
        """Get appropriate code template"""
        templates = {
            ("python", "fastapi", "model"): '''
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class {name}Base(BaseModel):
    """Base schema for {name}"""
    pass

class {name}Create({name}Base):
    """Schema for creating {name}"""
    pass

class {name}Update({name}Base):
    """Schema for updating {name}"""
    pass

class {name}Response({name}Base):
    """Schema for {name} response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
''',
            ("python", "fastapi", "service"): '''
from typing import List, Optional
from sqlalchemy.orm import Session
from .models import {name}
from .schemas import {name}Create, {name}Update

class {name}Service:
    """Service layer for {name} operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[{name}]:
        """Get all {name} records"""
        return self.db.query({name}).offset(skip).limit(limit).all()
    
    async def get_by_id(self, id: int) -> Optional[{name}]:
        """Get {name} by ID"""
        return self.db.query({name}).filter({name}.id == id).first()
    
    async def create(self, data: {name}Create) -> {name}:
        """Create new {name}"""
        db_obj = {name}(**data.dict())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    async def update(self, id: int, data: {name}Update) -> Optional[{name}]:
        """Update {name}"""
        db_obj = await self.get_by_id(id)
        if db_obj:
            for key, value in data.dict(exclude_unset=True).items():
                setattr(db_obj, key, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj
    
    async def delete(self, id: int) -> bool:
        """Delete {name}"""
        db_obj = await self.get_by_id(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False
''',
            ("python", "fastapi", "controller"): '''
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from .database import get_db
from .services import {name}Service
from .schemas import {name}Create, {name}Update, {name}Response

router = APIRouter(prefix="/{name_lower}s", tags=["{name}s"])

@router.get("/", response_model=List[{name}Response])
async def get_all(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all {name}s"""
    service = {name}Service(db)
    return await service.get_all(skip=skip, limit=limit)

@router.get("/{id}", response_model={name}Response)
async def get_by_id(id: int, db: Session = Depends(get_db)):
    """Get {name} by ID"""
    service = {name}Service(db)
    result = await service.get_by_id(id)
    if not result:
        raise HTTPException(status_code=404, detail="{name} not found")
    return result

@router.post("/", response_model={name}Response, status_code=status.HTTP_201_CREATED)
async def create(data: {name}Create, db: Session = Depends(get_db)):
    """Create new {name}"""
    service = {name}Service(db)
    return await service.create(data)

@router.put("/{id}", response_model={name}Response)
async def update(id: int, data: {name}Update, db: Session = Depends(get_db)):
    """Update {name}"""
    service = {name}Service(db)
    result = await service.update(id, data)
    if not result:
        raise HTTPException(status_code=404, detail="{name} not found")
    return result

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, db: Session = Depends(get_db)):
    """Delete {name}"""
    service = {name}Service(db)
    if not await service.delete(id):
        raise HTTPException(status_code=404, detail="{name} not found")
'''
        }
        
        key = (language.lower(), framework.lower(), component_type.lower())
        return templates.get(key, f"// Template for {language}/{framework}/{component_type}")


class CodeAnalysisInput(BaseModel):
    """Input schema for code analysis"""
    code: str = Field(..., description="Code to analyze")
    analysis_type: str = Field(
        default="full",
        description="Type of analysis (full, security, performance, style)"
    )


class CodeAnalysisTool(BaseTool):
    name: str = "Code Analysis Tool"
    description: str = """
    Analyzes code for quality, security issues, and best practices.
    Use this tool to review and improve code quality.
    """
    args_schema: Type[BaseModel] = CodeAnalysisInput
    
    def _run(self, code: str, analysis_type: str = "full") -> str:
        """Analyze code and return findings"""
        findings = []
        
        # Basic analysis (placeholder for actual implementation)
        if "password" in code.lower() and "hardcoded" not in code.lower():
            findings.append("⚠️ Potential hardcoded password detected")
        
        if "TODO" in code or "FIXME" in code:
            findings.append("📝 Found TODO/FIXME comments that need attention")
        
        if "except:" in code or "except Exception:" in code:
            findings.append("⚠️ Broad exception handling detected - consider specific exceptions")
        
        if not findings:
            findings.append("✅ No major issues found")
        
        return "\n".join(findings)


class CodeRefactoringInput(BaseModel):
    """Input schema for code refactoring"""
    code: str = Field(..., description="Code to refactor")
    refactoring_type: str = Field(..., description="Type of refactoring to apply")
    target_pattern: Optional[str] = Field(None, description="Target design pattern")


class CodeRefactoringTool(BaseTool):
    name: str = "Code Refactoring Tool"
    description: str = """
    Refactors code to improve structure, apply design patterns, or optimize performance.
    Use this tool to improve existing code.
    """
    args_schema: Type[BaseModel] = CodeRefactoringInput
    
    def _run(
        self,
        code: str,
        refactoring_type: str,
        target_pattern: Optional[str] = None
    ) -> str:
        """Refactor code based on specifications"""
        # Placeholder implementation
        return f"""
# Refactored code
# Refactoring type: {refactoring_type}
# Target pattern: {target_pattern or 'N/A'}

{code}

# Refactoring applied successfully
"""
EOF

# ============================================================
# DOSYA 11: tools/file_tools.py
# ============================================================
echo -e "${BLUE}📄 Creating tools/file_tools.py...${NC}"
cat > tools/file_tools.py << 'EOF'
"""
File system operation tools for agents
"""
import os
from typing import Type, Optional, List
from pydantic import BaseModel, Field
from crewai_tools import BaseTool
from config.settings import settings


class FileWriterInput(BaseModel):
    """Input schema for file writing"""
    file_path: str = Field(..., description="Path to the file (relative to output directory)")
    content: str = Field(..., description="Content to write to the file")
    overwrite: bool = Field(default=True, description="Overwrite if file exists")


class FileWriterTool(BaseTool):
    name: str = "File Writer Tool"
    description: str = """
    Writes content to a file in the output directory.
    Creates directories if they don't exist.
    Use this tool to save generated code, configs, or documentation.
    """
    args_schema: Type[BaseModel] = FileWriterInput
    
    def _run(self, file_path: str, content: str, overwrite: bool = True) -> str:
        """Write content to file"""
        full_path = os.path.join(settings.output_dir, file_path)
        
        # Create directory if needed
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Check if file exists
        if os.path.exists(full_path) and not overwrite:
            return f"❌ File already exists: {file_path}"
        
        # Write file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"✅ File written successfully: {file_path}"


class FileReaderInput(BaseModel):
    """Input schema for file reading"""
    file_path: str = Field(..., description="Path to the file to read")


class FileReaderTool(BaseTool):
    name: str = "File Reader Tool"
    description: str = """
    Reads content from a file.
    Use this tool to read existing code or configuration files.
    """
    args_schema: Type[BaseModel] = FileReaderInput
    
    def _run(self, file_path: str) -> str:
        """Read content from file"""
        # Try output directory first, then absolute path
        paths_to_try = [
            os.path.join(settings.output_dir, file_path),
            file_path
        ]
        
        for path in paths_to_try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
        
        return f"❌ File not found: {file_path}"


class DirectoryInput(BaseModel):
    """Input schema for directory operations"""
    path: str = Field(..., description="Directory path")
    operation: str = Field(
        default="list",
        description="Operation to perform (list, create, delete)"
    )


class DirectoryTool(BaseTool):
    name: str = "Directory Tool"
    description: str = """
    Performs directory operations like listing, creating, or managing directories.
    Use this tool to organize project structure.
    """
    args_schema: Type[BaseModel] = DirectoryInput
    
    def _run(self, path: str, operation: str = "list") -> str:
        """Perform directory operation"""
        full_path = os.path.join(settings.output_dir, path)
        
        if operation == "list":
            if not os.path.exists(full_path):
                return f"❌ Directory not found: {path}"
            
            items = os.listdir(full_path)
            return "\n".join([f"📁 {item}" if os.path.isdir(os.path.join(full_path, item)) 
                            else f"📄 {item}" for item in items])
        
        elif operation == "create":
            os.makedirs(full_path, exist_ok=True)
            return f"✅ Directory created: {path}"
        
        elif operation == "delete":
            if os.path.exists(full_path):
                import shutil
                shutil.rmtree(full_path)
                return f"✅ Directory deleted: {path}"
            return f"❌ Directory not found: {path}"
        
        return f"❌ Unknown operation: {operation}"
EOF

# ============================================================
# DOSYA 12: tools/infrastructure_tools.py
# ============================================================
echo -e "${BLUE}📄 Creating tools/infrastructure_tools.py...${NC}"
cat > tools/infrastructure_tools.py << 'EOF'
"""
Infrastructure as Code tools for agents
"""
from typing import Type, Optional, Dict, Any, List
from pydantic import BaseModel, Field
from crewai_tools import BaseTool


class TerraformInput(BaseModel):
    """Input schema for Terraform generation"""
    provider: str = Field(..., description="Cloud provider (aws, azure, gcp)")
    resource_type: str = Field(..., description="Resource type to create")
    resource_name: str = Field(..., description="Resource name")
    configuration: Dict[str, Any] = Field(..., description="Resource configuration")


class TerraformTool(BaseTool):
    name: str = "Terraform Config Generator"
    description: str = """
    Generates Terraform configuration files for cloud infrastructure.
    Supports AWS, Azure, and GCP resources.
    Use this tool to create infrastructure as code.
    """
    args_schema: Type[BaseModel] = TerraformInput
    
    def _run(
        self,
        provider: str,
        resource_type: str,
        resource_name: str,
        configuration: Dict[str, Any]
    ) -> str:
        """Generate Terraform configuration"""
        
        provider_configs = {
            "aws": self._generate_aws_config,
            "azure": self._generate_azure_config,
            "gcp": self._generate_gcp_config
        }
        
        generator = provider_configs.get(provider.lower())
        if not generator:
            return f"❌ Unsupported provider: {provider}"
        
        return generator(resource_type, resource_name, configuration)
    
    def _generate_aws_config(
        self,
        resource_type: str,
        resource_name: str,
        config: Dict[str, Any]
    ) -> str:
        """Generate AWS Terraform config"""
        
        templates = {
            "vpc": '''
resource "aws_vpc" "{name}" {{
  cidr_block           = "{cidr}"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {{
    Name        = "{name}"
    Environment = "{environment}"
    ManagedBy   = "terraform"
  }}
}}

resource "aws_internet_gateway" "{name}_igw" {{
  vpc_id = aws_vpc.{name}.id

  tags = {{
    Name = "{name}-igw"
  }}
}}
''',
            "eks": '''
module "eks" {{
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "{name}"
  cluster_version = "{version}"

  vpc_id     = aws_vpc.main.id
  subnet_ids = aws_subnet.private[*].id

  eks_managed_node_groups = {{
    general = {{
      desired_size = {desired_size}
      min_size     = {min_size}
      max_size     = {max_size}

      instance_types = ["{instance_type}"]
      capacity_type  = "ON_DEMAND"
    }}
  }}

  tags = {{
    Environment = "{environment}"
    ManagedBy   = "terraform"
  }}
}}
''',
            "rds": '''
resource "aws_db_instance" "{name}" {{
  identifier     = "{name}"
  engine         = "{engine}"
  engine_version = "{engine_version}"
  instance_class = "{instance_class}"

  allocated_storage     = {allocated_storage}
  max_allocated_storage = {max_allocated_storage}

  db_name  = "{db_name}"
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  multi_az               = {multi_az}
  publicly_accessible    = false
  skip_final_snapshot    = true

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"

  tags = {{
    Name        = "{name}"
    Environment = "{environment}"
    ManagedBy   = "terraform"
  }}
}}
'''
        }
        
        template = templates.get(resource_type.lower(), "# Unknown resource type")
        
        # Apply configuration to template
        formatted = template.format(
            name=resource_name,
            **config
        )
        
        return formatted


    def _generate_azure_config(
        self,
        resource_type: str,
        resource_name: str,
        config: Dict[str, Any]
    ) -> str:
        """Generate Azure Terraform config"""
        return f'''
# Azure {resource_type}: {resource_name}
resource "azurerm_{resource_type}" "{resource_name}" {{
  name                = "{resource_name}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  # Configuration
  {self._dict_to_hcl(config)}

  tags = {{
    Environment = "production"
    ManagedBy   = "terraform"
  }}
}}
'''

    def _generate_gcp_config(
        self,
        resource_type: str,
        resource_name: str,
        config: Dict[str, Any]
    ) -> str:
        """Generate GCP Terraform config"""
        return f'''
# GCP {resource_type}: {resource_name}
resource "google_{resource_type}" "{resource_name}" {{
  name    = "{resource_name}"
  project = var.project_id

  # Configuration
  {self._dict_to_hcl(config)}

  labels = {{
    environment = "production"
    managed_by  = "terraform"
  }}
}}
'''

    def _dict_to_hcl(self, d: Dict[str, Any], indent: int = 2) -> str:
        """Convert dictionary to HCL format"""
        lines = []
        prefix = " " * indent
        for key, value in d.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key} = {{")
                lines.append(self._dict_to_hcl(value, indent + 2))
                lines.append(f"{prefix}}}")
            elif isinstance(value, bool):
                lines.append(f"{prefix}{key} = {str(value).lower()}")
            elif isinstance(value, (int, float)):
                lines.append(f"{prefix}{key} = {value}")
            else:
                lines.append(f'{prefix}{key} = "{value}"')
        return "\n".join(lines)


class KubernetesInput(BaseModel):
    """Input schema for Kubernetes manifest generation"""
    resource_type: str = Field(..., description="K8s resource type (deployment, service, configmap, etc.)")
    name: str = Field(..., description="Resource name")
    namespace: str = Field(default="default", description="Kubernetes namespace")
    spec: Dict[str, Any] = Field(..., description="Resource specification")


class KubernetesTool(BaseTool):
    name: str = "Kubernetes Manifest Generator"
    description: str = """
    Generates Kubernetes manifest files (YAML).
    Supports deployments, services, configmaps, secrets, and more.
    Use this tool to create Kubernetes resources.
    """
    args_schema: Type[BaseModel] = KubernetesInput
    
    def _run(
        self,
        resource_type: str,
        name: str,
        namespace: str,
        spec: Dict[str, Any]
    ) -> str:
        """Generate Kubernetes manifest"""
        import yaml
        
        generators = {
            "deployment": self._generate_deployment,
            "service": self._generate_service,
            "configmap": self._generate_configmap,
            "secret": self._generate_secret,
            "ingress": self._generate_ingress,
            "hpa": self._generate_hpa
        }
        
        generator = generators.get(resource_type.lower())
        if not generator:
            return f"❌ Unsupported resource type: {resource_type}"
        
        manifest = generator(name, namespace, spec)
        return yaml.dump(manifest, default_flow_style=False)
    
    def _generate_deployment(self, name: str, namespace: str, spec: Dict) -> Dict:
        """Generate Deployment manifest"""
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": name,
                "namespace": namespace,
                "labels": {"app": name}
            },
            "spec": {
                "replicas": spec.get("replicas", 3),
                "selector": {
                    "matchLabels": {"app": name}
                },
                "template": {
                    "metadata": {
                        "labels": {"app": name}
                    },
                    "spec": {
                        "containers": [{
                            "name": name,
                            "image": spec.get("image", f"{name}:latest"),
                            "ports": [{"containerPort": spec.get("port", 8080)}],
                            "resources": {
                                "requests": {
                                    "memory": spec.get("memory_request", "256Mi"),
                                    "cpu": spec.get("cpu_request", "250m")
                                },
                                "limits": {
                                    "memory": spec.get("memory_limit", "512Mi"),
                                    "cpu": spec.get("cpu_limit", "500m")
                                }
                            },
                            "livenessProbe": {
                                "httpGet": {
                                    "path": spec.get("health_path", "/health"),
                                    "port": spec.get("port", 8080)
                                },
                                "initialDelaySeconds": 30,
                                "periodSeconds": 10
                            },
                            "readinessProbe": {
                                "httpGet": {
                                    "path": spec.get("ready_path", "/ready"),
                                    "port": spec.get("port", 8080)
                                },
                                "initialDelaySeconds": 5,
                                "periodSeconds": 5
                            }
                        }]
                    }
                }
            }
        }
    
    def _generate_service(self, name: str, namespace: str, spec: Dict) -> Dict:
        """Generate Service manifest"""
        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": name,
                "namespace": namespace
            },
            "spec": {
                "type": spec.get("type", "ClusterIP"),
                "selector": {"app": name},
                "ports": [{
                    "port": spec.get("port", 80),
                    "targetPort": spec.get("target_port", 8080),
                    "protocol": "TCP"
                }]
            }
        }
    
    def _generate_configmap(self, name: str, namespace: str, spec: Dict) -> Dict:
        """Generate ConfigMap manifest"""
        return {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": name,
                "namespace": namespace
            },
            "data": spec.get("data", {})
        }
    
    def _generate_secret(self, name: str, namespace: str, spec: Dict) -> Dict:
        """Generate Secret manifest"""
        import base64
        
        encoded_data = {}
        for key, value in spec.get("data", {}).items():
            encoded_data[key] = base64.b64encode(value.encode()).decode()
        
        return {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": name,
                "namespace": namespace
            },
            "type": spec.get("type", "Opaque"),
            "data": encoded_data
        }
    
    def _generate_ingress(self, name: str, namespace: str, spec: Dict) -> Dict:
        """Generate Ingress manifest"""
        return {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": name,
                "namespace": namespace,
                "annotations": spec.get("annotations", {
                    "kubernetes.io/ingress.class": "nginx",
                    "cert-manager.io/cluster-issuer": "letsencrypt-prod"
                })
            },
            "spec": {
                "tls": [{
                    "hosts": [spec.get("host", f"{name}.example.com")],
                    "secretName": f"{name}-tls"
                }],
                "rules": [{
                    "host": spec.get("host", f"{name}.example.com"),
                    "http": {
                        "paths": [{
                            "path": "/",
                            "pathType": "Prefix",
                            "backend": {
                                "service": {
                                    "name": name,
                                    "port": {"number": spec.get("port", 80)}
                                }
                            }
                        }]
                    }
                }]
            }
        }
    
    def _generate_hpa(self, name: str, namespace: str, spec: Dict) -> Dict:
        """Generate HorizontalPodAutoscaler manifest"""
        return {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": name,
                "namespace": namespace
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": name
                },
                "minReplicas": spec.get("min_replicas", 2),
                "maxReplicas": spec.get("max_replicas", 10),
                "metrics": [{
                    "type": "Resource",
                    "resource": {
                        "name": "cpu",
                        "target": {
                            "type": "Utilization",
                            "averageUtilization": spec.get("cpu_threshold", 70)
                        }
                    }
                }]
            }
        }


class DockerInput(BaseModel):
    """Input schema for Docker file generation"""
    language: str = Field(..., description="Programming language")
    framework: str = Field(..., description="Framework used")
    app_name: str = Field(..., description="Application name")
    port: int = Field(default=8080, description="Application port")


class DockerTool(BaseTool):
    name: str = "Dockerfile Generator"
    description: str = """
    Generates optimized Dockerfiles for various languages and frameworks.
    Creates multi-stage builds for production-ready images.
    Use this tool to containerize applications.
    """
    args_schema: Type[BaseModel] = DockerInput
    
    def _run(
        self,
        language: str,
        framework: str,
        app_name: str,
        port: int = 8080
    ) -> str:
        """Generate Dockerfile"""
        
        templates = {
            "python": self._python_dockerfile,
            "go": self._go_dockerfile,
            "nodejs": self._nodejs_dockerfile,
            "csharp": self._csharp_dockerfile
        }
        
        generator = templates.get(language.lower())
        if not generator:
            return f"❌ Unsupported language: {language}"
        
        return generator(app_name, framework, port)
    
    def _python_dockerfile(self, app_name: str, framework: str, port: int) -> str:
        return f'''# Multi-stage build for Python {framework} application
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim as production

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE {port}

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:{port}/health')" || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{port}"]
'''
    
    def _go_dockerfile(self, app_name: str, framework: str, port: int) -> str:
        return f'''# Multi-stage build for Go application
# Stage 1: Builder
FROM golang:1.21-alpine as builder

WORKDIR /app

# Install dependencies
RUN apk add --no-cache git ca-certificates tzdata

# Download dependencies
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build binary
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -ldflags="-w -s" -o {app_name} .

# Stage 2: Production
FROM scratch

WORKDIR /app

# Copy CA certificates and timezone data
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo

# Copy binary
COPY --from=builder /app/{app_name} .

# Expose port
EXPOSE {port}

# Run application
ENTRYPOINT ["/{app_name}"]
'''
    
    def _nodejs_dockerfile(self, app_name: str, framework: str, port: int) -> str:
        return f'''# Multi-stage build for Node.js application
# Stage 1: Dependencies
FROM node:20-alpine as deps

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

# Stage 2: Builder
FROM node:20-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 3: Production
FROM node:20-alpine as production

WORKDIR /app

ENV NODE_ENV=production

# Create non-root user
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001

# Copy dependencies and build
COPY --from=deps /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./

USER nodejs

EXPOSE {port}

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD node -e "require('http').get('http://localhost:{port}/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1))" || exit 1

CMD ["node", "dist/main.js"]
'''
    
    def _csharp_dockerfile(self, app_name: str, framework: str, port: int) -> str:
        return f'''# Multi-stage build for .NET application
# Stage 1: Build
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build

WORKDIR /src

# Copy csproj and restore
COPY *.csproj ./
RUN dotnet restore

# Copy everything and build
COPY . .
RUN dotnet publish -c Release -o /app/publish

# Stage 2: Production
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS production

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY --from=build /app/publish .

# Change ownership
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE {port}

ENV ASPNETCORE_URLS=http://+:{port}

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{port}/health || exit 1

ENTRYPOINT ["dotnet", "{app_name}.dll"]
'''


class AnsibleInput(BaseModel):
    """Input schema for Ansible playbook generation"""
    playbook_type: str = Field(..., description="Type of playbook (setup, deploy, configure)")
    target: str = Field(..., description="Target system or service")
    tasks: List[str] = Field(..., description="List of tasks to include")


class AnsibleTool(BaseTool):
    name: str = "Ansible Playbook Generator"
    description: str = """
    Generates Ansible playbooks for configuration management and deployment.
    Use this tool to create automation scripts for server configuration.
    """
    args_schema: Type[BaseModel] = AnsibleInput
    
    def _run(
        self,
        playbook_type: str,
        target: str,
        tasks: List[str]
    ) -> str:
        """Generate Ansible playbook"""
        import yaml
        
        playbook = {
            "name": f"{playbook_type.title()} {target}",
            "hosts": target,
            "become": True,
            "vars": {
                "ansible_python_interpreter": "/usr/bin/python3"
            },
            "tasks": []
        }
        
        for task in tasks:
            playbook["tasks"].append(self._generate_task(task))
        
        return yaml.dump([playbook], default_flow_style=False)
    
    def _generate_task(self, task: str) -> Dict:
        """Generate individual task"""
        task_templates = {
            "install_docker": {
                "name": "Install Docker",
                "apt": {
                    "name": ["docker.io", "docker-compose"],
                    "state": "present",
                    "update_cache": True
                }
            },
            "configure_firewall": {
                "name": "Configure UFW firewall",
                "ufw": {
                    "rule": "allow",
                    "port": "{{ item }}",
                    "proto": "tcp"
                },
                "loop": ["22", "80", "443"]
            },
            "create_user": {
                "name": "Create application user",
                "user": {
                    "name": "appuser",
                    "shell": "/bin/bash",
                    "groups": "docker",
                    "append": True
                }
            }
        }
        
        return task_templates.get(task, {
            "name": task,
            "debug": {"msg": f"Task: {task}"}
        })
EOF

# ============================================================
# DOSYA 13: tools/cicd_tools.py
# ============================================================
echo -e "${BLUE}📄 Creating tools/cicd_tools.py...${NC}"
cat > tools/cicd_tools.py << 'EOF'
"""
CI/CD pipeline generation tools
"""
from typing import Type, Optional, Dict, Any, List
from pydantic import BaseModel, Field
from crewai_tools import BaseTool
import yaml


class GitHubActionsInput(BaseModel):
    """Input schema for GitHub Actions workflow"""
    workflow_name: str = Field(..., description="Name of the workflow")
    language: str = Field(..., description="Programming language")
    triggers: List[str] = Field(default=["push", "pull_request"], description="Workflow triggers")
    include_deploy: bool = Field(default=True, description="Include deployment step")
    deploy_target: Optional[str] = Field(default="kubernetes", description="Deployment target")


class GitHubActionsTool(BaseTool):
    name: str = "GitHub Actions Generator"
    description: str = """
    Generates GitHub Actions workflow files for CI/CD pipelines.
    Supports various languages, testing, and deployment strategies.
    Use this tool to create automated CI/CD pipelines.
    """
    args_schema: Type[BaseModel] = GitHubActionsInput
    
    def _run(
        self,
        workflow_name: str,
        language: str,
        triggers: List[str] = ["push", "pull_request"],
        include_deploy: bool = True,
        deploy_target: Optional[str] = "kubernetes"
    ) -> str:
        """Generate GitHub Actions workflow"""
        
        workflow = {
            "name": workflow_name,
            "on": self._build_triggers(triggers),
            "env": {
                "REGISTRY": "ghcr.io",
                "IMAGE_NAME": "${{ github.repository }}"
            },
            "jobs": {}
        }
        
        # Add test job
        workflow["jobs"]["test"] = self._build_test_job(language)
        
        # Add build job
        workflow["jobs"]["build"] = self._build_build_job(language)
        
        # Add deploy job if requested
        if include_deploy:
            workflow["jobs"]["deploy"] = self._build_deploy_job(deploy_target)
        
        return yaml.dump(workflow, default_flow_style=False, sort_keys=False)
    
    def _build_triggers(self, triggers: List[str]) -> Dict:
        """Build workflow triggers"""
        trigger_config = {}
        
        for trigger in triggers:
            if trigger == "push":
                trigger_config["push"] = {
                    "branches": ["main", "develop"],
                    "paths-ignore": ["**.md", "docs/**"]
                }
            elif trigger == "pull_request":
                trigger_config["pull_request"] = {
                    "branches": ["main", "develop"]
                }
            elif trigger == "schedule":
                trigger_config["schedule"] = [{"cron": "0 0 * * *"}]
            elif trigger == "workflow_dispatch":
                trigger_config["workflow_dispatch"] = {}
        
        return trigger_config
    
    def _build_test_job(self, language: str) -> Dict:
        """Build test job based on language"""
        
        language_configs = {
            "python": {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"uses": "actions/checkout@v4"},
                    {
                        "name": "Set up Python",
                        "uses": "actions/setup-python@v5",
                        "with": {"python-version": "3.11"}
                    },
                    {
                        "name": "Install dependencies",
                        "run": "pip install -r requirements.txt -r requirements-dev.txt"
                    },
                    {
                        "name": "Run linting",
                        "run": "ruff check . && black --check ."
                    },
                    {
                        "name": "Run tests",
                        "run": "pytest --cov=. --cov-report=xml"
                    },
                    {
                        "name": "Upload coverage",
                        "uses": "codecov/codecov-action@v3",
                        "with": {"files": "./coverage.xml"}
                    }
                ]
            },
            "go": {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"uses": "actions/checkout@v4"},
                    {
                        "name": "Set up Go",
                        "uses": "actions/setup-go@v5",
                        "with": {"go-version": "1.21"}
                    },
                    {
                        "name": "Run linting",
                        "uses": "golangci/golangci-lint-action@v3"
                    },
                    {
                        "name": "Run tests",
                        "run": "go test -v -race -coverprofile=coverage.out ./..."
                    }
                ]
            },
            "nodejs": {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"uses": "actions/checkout@v4"},
                    {
                        "name": "Set up Node.js",
                        "uses": "actions/setup-node@v4",
                        "with": {"node-version": "20", "cache": "npm"}
                    },
                    {"name": "Install dependencies", "run": "npm ci"},
                    {"name": "Run linting", "run": "npm run lint"},
                    {"name": "Run tests", "run": "npm test -- --coverage"}
                ]
            }
        }
        
        return language_configs.get(language.lower(), language_configs["python"])
    
    def _build_build_job(self, language: str) -> Dict:
        """Build Docker build job"""
        return {
            "runs-on": "ubuntu-latest",
            "needs": "test",
            "permissions": {
                "contents": "read",
                "packages": "write"
            },
            "steps": [
                {"uses": "actions/checkout@v4"},
                {
                    "name": "Set up Docker Buildx",
                    "uses": "docker/setup-buildx-action@v3"
                },
                {
                    "name": "Log in to Container Registry",
                    "uses": "docker/login-action@v3",
                    "with": {
                        "registry": "${{ env.REGISTRY }}",
                        "username": "${{ github.actor }}",
                        "password": "${{ secrets.GITHUB_TOKEN }}"
                    }
                },
                {
                    "name": "Extract metadata",
                    "id": "meta",
                    "uses": "docker/metadata-action@v5",
                    "with": {
                        "images": "${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}",
                        "tags": "type=sha,prefix=\ntype=ref,event=branch\ntype=semver,pattern={{version}}"
                    }
                },
                {
                    "name": "Build and push",
                    "uses": "docker/build-push-action@v5",
                    "with": {
                        "context": ".",
                        "push": True,
                        "tags": "${{ steps.meta.outputs.tags }}",
                        "labels": "${{ steps.meta.outputs.labels }}",
                        "cache-from": "type=gha",
                        "cache-to": "type=gha,mode=max"
                    }
                }
            ]
        }
    
    def _build_deploy_job(self, deploy_target: str) -> Dict:
        """Build deployment job"""
        
        base_job = {
            "runs-on": "ubuntu-latest",
            "needs": "build",
            "if": "github.ref == 'refs/heads/main'",
            "environment": {
                "name": "production",
                "url": "https://app.example.com"
            },
            "steps": [{"uses": "actions/checkout@v4"}]
        }
        
        if deploy_target == "kubernetes":
            base_job["steps"].extend([
                {
                    "name": "Configure kubectl",
                    "uses": "azure/setup-kubectl@v3"
                },
                {
                    "name": "Set Kubernetes context",
                    "uses": "azure/k8s-set-context@v3",
                    "with": {
                        "kubeconfig": "${{ secrets.KUBE_CONFIG }}"
                    }
                },
                {
                    "name": "Deploy to Kubernetes",
                    "run": """
                      kubectl set image deployment/app app=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
                      kubectl rollout status deployment/app
                    """
                }
            ])
        elif deploy_target == "ecs":
            base_job["steps"].extend([
                {
                    "name": "Configure AWS credentials",
                    "uses": "aws-actions/configure-aws-credentials@v4",
                    "with": {
                        "aws-access-key-id": "${{ secrets.AWS_ACCESS_KEY_ID }}",
                        "aws-secret-access-key": "${{ secrets.AWS_SECRET_ACCESS_KEY }}",
                        "aws-region": "us-east-1"
                    }
                },
                {
                    "name": "Deploy to ECS",
                    "run": """
                      aws ecs update-service --cluster production --service app --force-new-deployment
                    """
                }
            ])
        
        return base_job


class GitLabCIInput(BaseModel):
    """Input schema for GitLab CI configuration"""
    language: str = Field(..., description="Programming language")
    stages: List[str] = Field(
        default=["test", "build", "deploy"],
        description="Pipeline stages"
    )
    include_security_scan: bool = Field(default=True, description="Include security scanning")


class GitLabCITool(BaseTool):
    name: str = "GitLab CI Generator"
    description: str = """
    Generates GitLab CI/CD configuration files.
    Supports multi-stage pipelines with security scanning.
    Use this tool to create GitLab CI pipelines.
    """
    args_schema: Type[BaseModel] = GitLabCIInput
    
    def _run(
        self,
        language: str,
        stages: List[str] = ["test", "build", "deploy"],
        include_security_scan: bool = True
    ) -> str:
        """Generate GitLab CI configuration"""
        
        config = {
            "stages": stages,
            "variables": {
                "DOCKER_DRIVER": "overlay2",
                "DOCKER_TLS_CERTDIR": "/certs"
            },
            "default": {
                "image": self._get_default_image(language)
            }
        }
        
        # Add test job
        config["test"] = self._build_test_job_gitlab(language)
        
        # Add security scan if requested
        if include_security_scan:
            config["include"] = [
                {"template": "Security/SAST.gitlab-ci.yml"},
                {"template": "Security/Dependency-Scanning.gitlab-ci.yml"}
            ]
        
        # Add build job
        config["build"] = {
            "stage": "build",
            "image": "docker:24.0",
            "services": ["docker:24.0-dind"],
            "script": [
                "docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY",
                "docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .",
                "docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA"
            ],
            "only": ["main", "develop"]
        }
        
        # Add deploy job
        config["deploy"] = {
            "stage": "deploy",
            "image": "bitnami/kubectl:latest",
            "script": [
                "kubectl set image deployment/app app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA",
                "kubectl rollout status deployment/app"
            ],
            "only": ["main"],
            "environment": {
                "name": "production",
                "url": "https://app.example.com"
            }
        }
        
        return yaml.dump(config, default_flow_style=False, sort_keys=False)
    
    def _get_default_image(self, language: str) -> str:
        """Get default Docker image for language"""
        images = {
            "python": "python:3.11-slim",
            "go": "golang:1.21",
            "nodejs": "node:20-alpine",
            "csharp": "mcr.microsoft.com/dotnet/sdk:8.0"
        }
        return images.get(language.lower(), "ubuntu:22.04")
    
    def _build_test_job_gitlab(self, language: str) -> Dict:
        """Build test job for GitLab CI"""
        
        configs = {
            "python": {
                "stage": "test",
                "script": [
                    "pip install -r requirements.txt -r requirements-dev.txt",
                    "pytest --cov=. --cov-report=xml",
                    "ruff check ."
                ],
                "coverage": "/TOTAL.*\\s+(\\d+%)$/",
                "artifacts": {
                    "reports": {"coverage_report": {
                        "coverage_format": "cobertura",
                        "path": "coverage.xml"
                    }}
                }
            },
            "go": {
                "stage": "test",
                "script": [
                    "go test -v -race -coverprofile=coverage.out ./...",
                    "golangci-lint run"
                ]
            },
            "nodejs": {
                "stage": "test",
                "script": [
                    "npm ci",
                    "npm run lint",
                    "npm test -- --coverage"
                ]
            }
        }
        
        return configs.get(language.lower(), configs["python"])


class JenkinsInput(BaseModel):
    """Input schema for Jenkinsfile generation"""
    language: str = Field(..., description="Programming language")
    pipeline_type: str = Field(
        default="declarative",
        description="Pipeline type (declarative, scripted)"
    )
    deploy_environments: List[str] = Field(
        default=["staging", "production"],
        description="Deployment environments"
    )


class JenkinsTool(BaseTool):
    name: str = "Jenkinsfile Generator"
    description: str = """
    Generates Jenkinsfile for CI/CD pipelines.
    Supports declarative and scripted pipelines.
    Use this tool to create Jenkins pipelines.
    """
    args_schema: Type[BaseModel] = JenkinsInput
    
    def _run(
        self,
        language: str,
        pipeline_type: str = "declarative",
        deploy_environments: List[str] = ["staging", "production"]
    ) -> str:
        """Generate Jenkinsfile"""
        
        if pipeline_type == "declarative":
            return self._generate_declarative(language, deploy_environments)
        else:
            return self._generate_scripted(language, deploy_environments)
    
    def _generate_declarative(self, language: str, environments: List[str]) -> str:
        """Generate declarative pipeline"""
        
        test_commands = {
            "python": "pip install -r requirements.txt && pytest",
            "go": "go test -v ./...",
            "nodejs": "npm ci && npm test"
        }
        
        test_cmd = test_commands.get(language.lower(), "echo 'Running tests...'")
        
        env_stages = ""
        for env in environments:
            env_stages += f'''
        stage('Deploy to {env.title()}') {{
            when {{
                branch '{env if env != "production" else "main"}'
            }}
            steps {{
                script {{
                    kubernetesDeploy(
                        configs: 'k8s/{env}/*.yaml',
                        kubeconfigId: 'kubeconfig-{env}'
                    )
                }}
            }}
        }}
'''
        
        return f'''pipeline {{
    agent any
    
    environment {{
        DOCKER_REGISTRY = 'your-registry.com'
        IMAGE_NAME = 'your-app'
    }}
    
    options {{
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
    }}
    
    stages {{
        stage('Checkout') {{
            steps {{
                checkout scm
            }}
        }}
        
        stage('Test') {{
            steps {{
                sh '{test_cmd}'
            }}
        }}
        
        stage('Build') {{
            steps {{
                script {{
                    docker.build("${{DOCKER_REGISTRY}}/${{IMAGE_NAME}}:${{BUILD_NUMBER}}")
                }}
            }}
        }}
        
        stage('Push') {{
            steps {{
                script {{
                    docker.withRegistry("https://${{DOCKER_REGISTRY}}", 'docker-credentials') {{
                        docker.image("${{DOCKER_REGISTRY}}/${{IMAGE_NAME}}:${{BUILD_NUMBER}}").push()
                        docker.image("${{DOCKER_REGISTRY}}/${{IMAGE_NAME}}:${{BUILD_NUMBER}}").push('latest')
                    }}
                }}
            }}
        }}
{env_stages}
    }}
    
    post {{
        always {{
            cleanWs()
        }}
        success {{
            slackSend(color: 'good', message: "Build Successful: ${{env.JOB_NAME}} #${{env.BUILD_NUMBER}}")
        }}
        failure {{
            slackSend(color: 'danger', message: "Build Failed: ${{env.JOB_NAME}} #${{env.BUILD_NUMBER}}")
        }}
    }}
}}
'''
    
    def _generate_scripted(self, language: str, environments: List[str]) -> str:
        """Generate scripted pipeline"""
        return '''node {
    try {
        stage('Checkout') {
            checkout scm
        }
        
        stage('Test') {
            sh 'echo "Running tests..."'
        }
        
        stage('Build') {
            sh 'docker build -t app:${BUILD_NUMBER} .'
        }
        
        stage('Deploy') {
            sh 'kubectl apply -f k8s/'
        }
    } catch (e) {
        currentBuild.result = 'FAILED'
        throw e
    } finally {
        cleanWs()
    }
}
'''
EOF

# ============================================================
# DOSYA 14: tools/database_tools.py
# ============================================================
echo -e "${BLUE}📄 Creating tools/database_tools.py...${NC}"
cat > tools/database_tools.py << 'EOF'
"""
Database schema and migration tools
"""
from typing import Type, Optional, Dict, Any, List
from pydantic import BaseModel, Field
from crewai_tools import BaseTool


class DatabaseSchemaInput(BaseModel):
    """Input schema for database schema generation"""
    database_type: str = Field(..., description="Database type (postgresql, mysql, mongodb)")
    entities: List[Dict[str, Any]] = Field(..., description="Entity definitions")
    include_indexes: bool = Field(default=True, description="Generate index definitions")


class DatabaseSchemaTool(BaseTool):
    name: str = "Database Schema Generator"
    description: str = """
    Generates database schema definitions (SQL DDL or NoSQL schemas).
    Supports PostgreSQL, MySQL, and MongoDB.
    Use this tool to create database structure.
    """
    args_schema: Type[BaseModel] = DatabaseSchemaInput
    
    def _run(
        self,
        database_type: str,
        entities: List[Dict[str, Any]],
        include_indexes: bool = True
    ) -> str:
        """Generate database schema"""
        
        generators = {
            "postgresql": self._generate_postgresql,
            "mysql": self._generate_mysql,
            "mongodb": self._generate_mongodb
        }
        
        generator = generators.get(database_type.lower())
        if not generator:
            return f"❌ Unsupported database type: {database_type}"
        
        return generator(entities, include_indexes)
    
    def _generate_postgresql(self, entities: List[Dict], include_indexes: bool) -> str:
        """Generate PostgreSQL schema"""
        
        sql = "-- PostgreSQL Schema\n\n"
        sql += "-- Enable UUID extension\nCREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";\n\n"
        
        for entity in entities:
            name = entity.get("name", "entity")
            fields = entity.get("fields", [])
            
            sql += f"-- Table: {name}\n"
            sql += f"CREATE TABLE {name} (\n"
            
            field_lines = []
            for field in fields:
                field_name = field.get("name")
                field_type = self._map_type_postgresql(field.get("type"))
                nullable = "NULL" if field.get("nullable", True) else "NOT NULL"
                default = f"DEFAULT {field.get('default')}" if field.get("default") else ""
                
                if field.get("primary_key"):
                    field_lines.append(f"    {field_name} {field_type} PRIMARY KEY")
                else:
                    field_lines.append(f"    {field_name} {field_type} {nullable} {default}".strip())
            
            # Add audit columns
            field_lines.append("    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()")
            field_lines.append("    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()")
            
            sql += ",\n".join(field_lines)
            sql += "\n);\n\n"
            
            # Add indexes
            if include_indexes:
                for field in fields:
                    if field.get("index"):
                        idx_name = f"idx_{name}_{field.get('name')}"
                        sql += f"CREATE INDEX {idx_name} ON {name}({field.get('name')});\n"
                
                sql += "\n"
        
        # Add update trigger function
        sql += """
-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

"""
        
        for entity in entities:
            name = entity.get("name", "entity")
            sql += f"CREATE TRIGGER update_{name}_updated_at\n"
            sql += f"    BEFORE UPDATE ON {name}\n"
            sql += f"    FOR EACH ROW\n"
            sql += f"    EXECUTE FUNCTION update_updated_at_column();\n\n"
        
        return sql
    
    def _generate_mysql(self, entities: List[Dict], include_indexes: bool) -> str:
        """Generate MySQL schema"""
        
        sql = "-- MySQL Schema\n\n"
        
        for entity in entities:
            name = entity.get("name", "entity")
            fields = entity.get("fields", [])
            
            sql += f"-- Table: {name}\n"
            sql += f"CREATE TABLE `{name}` (\n"
            
            field_lines = []
            primary_keys = []
            
            for field in fields:
                field_name = field.get("name")
                field_type = self._map_type_mysql(field.get("type"))
                nullable = "NULL" if field.get("nullable", True) else "NOT NULL"
                default = f"DEFAULT {field.get('default')}" if field.get("default") else ""
                
                if field.get("primary_key"):
                    primary_keys.append(field_name)
                    if field.get("auto_increment"):
                        field_lines.append(f"    `{field_name}` {field_type} NOT NULL AUTO_INCREMENT")
                    else:
                        field_lines.append(f"    `{field_name}` {field_type} NOT NULL")
                else:
                    field_lines.append(f"    `{field_name}` {field_type} {nullable} {default}".strip())
            
            # Add audit columns
            field_lines.append("    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            field_lines.append("    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
            
            # Add primary key
            if primary_keys:
                field_lines.append(f"    PRIMARY KEY (`{', '.join(primary_keys)}`)")
            
            sql += ",\n".join(field_lines)
            sql += "\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n\n"
        
        return sql
    
    def _generate_mongodb(self, entities: List[Dict], include_indexes: bool) -> str:
        """Generate MongoDB schema validation and indexes"""
        import json
        
        output = "// MongoDB Schema Validation and Indexes\n\n"
        
        for entity in entities:
            name = entity.get("name", "entity")
            fields = entity.get("fields", [])
            
            # Create validation schema
            validation = {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": [],
                    "properties": {}
                }
            }
            
            for field in fields:
                field_name = field.get("name")
                bson_type = self._map_type_mongodb(field.get("type"))
                
                validation["$jsonSchema"]["properties"][field_name] = {
                    "bsonType": bson_type,
                    "description": field.get("description", f"The {field_name} field")
                }
                
                if not field.get("nullable", True):
                    validation["$jsonSchema"]["required"].append(field_name)
            
            # Add timestamps
            validation["$jsonSchema"]["properties"]["createdAt"] = {"bsonType": "date"}
            validation["$jsonSchema"]["properties"]["updatedAt"] = {"bsonType": "date"}
            
            output += f"// Collection: {name}\n"
            output += f"db.createCollection('{name}', {{\n"
            output += f"  validator: {json.dumps(validation, indent=4)}\n"
            output += "});\n\n"
            
            # Add indexes
            if include_indexes:
                for field in fields:
                    if field.get("index"):
                        output += f"db.{name}.createIndex({{ {field.get('name')}: 1 }});\n"
                    if field.get("unique"):
                        output += f"db.{name}.createIndex({{ {field.get('name')}: 1 }}, {{ unique: true }});\n"
                
                output += "\n"
        
        return output
    
    def _map_type_postgresql(self, field_type: str) -> str:
        """Map field type to PostgreSQL type"""
        type_map = {
            "string": "VARCHAR(255)",
            "text": "TEXT",
            "integer": "INTEGER",
            "bigint": "BIGINT",
            "float": "DECIMAL(10,2)",
            "boolean": "BOOLEAN",
            "date": "DATE",
            "datetime": "TIMESTAMP WITH TIME ZONE",
            "uuid": "UUID DEFAULT uuid_generate_v4()",
            "json": "JSONB"
        }
        return type_map.get(field_type.lower(), "VARCHAR(255)")
    
    def _map_type_mysql(self, field_type: str) -> str:
        """Map field type to MySQL type"""
        type_map = {
            "string": "VARCHAR(255)",
            "text": "TEXT",
            "integer": "INT",
            "bigint": "BIGINT",
            "float": "DECIMAL(10,2)",
            "boolean": "TINYINT(1)",
            "date": "DATE",
            "datetime": "DATETIME",
            "uuid": "CHAR(36)",
            "json": "JSON"
        }
        return type_map.get(field_type.lower(), "VARCHAR(255)")
    
    def _map_type_mongodb(self, field_type: str) -> str:
        """Map field type to MongoDB BSON type"""
        type_map = {
            "string": "string",
            "text": "string",
            "integer": "int",
            "bigint": "long",
            "float": "double",
            "boolean": "bool",
            "date": "date",
            "datetime": "date",
            "uuid": "string",
            "json": "object"
        }
        return type_map.get(field_type.lower(), "string")


class MigrationInput(BaseModel):
    """Input schema for migration generation"""
    database_type: str = Field(..., description="Database type")
    migration_name: str = Field(..., description="Migration name")
    operations: List[Dict[str, Any]] = Field(..., description="Migration operations")


class MigrationTool(BaseTool):
    name: str = "Migration Generator"
    description: str = """
    Generates database migration scripts.
    Supports Alembic (Python), Flyway, and raw SQL migrations.
    Use this tool to create version-controlled database changes.
    """
    args_schema: Type[BaseModel] = MigrationInput
    
    def _run(
        self,
        database_type: str,
        migration_name: str,
        operations: List[Dict[str, Any]]
    ) -> str:
        """Generate migration script"""
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        migration = f"""\"\"\"
{migration_name}

Revision ID: {timestamp}
Create Date: {datetime.now().isoformat()}
\"\"\"
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '{timestamp}'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
"""
        
        for operation in operations:
            op_type = operation.get("type")
            if op_type == "create_table":
                migration += self._generate_create_table(operation)
            elif op_type == "add_column":
                migration += self._generate_add_column(operation)
            elif op_type == "drop_table":
                migration += self._generate_drop_table(operation)
        
        migration += """

def downgrade():
    pass  # TODO: Implement downgrade
"""
        
        return migration
    
    def _generate_create_table(self, operation: Dict) -> str:
        """Generate create table operation"""
        table_name = operation.get("table")
        columns = operation.get("columns", [])
        
        code = f"    op.create_table('{table_name}',\n"
        
        for col in columns:
            col_type = col.get("type", "String")
            code += f"        sa.Column('{col.get('name')}', sa.{col_type}()"
            if col.get("primary_key"):
                code += ", primary_key=True"
            if col.get("nullable") is False:
                code += ", nullable=False"
            code += "),\n"
        
        code += "    )\n"
        return code
    
    def _generate_add_column(self, operation: Dict) -> str:
        """Generate add column operation"""
        table_name = operation.get("table")
        column = operation.get("column", {})
        col_type = column.get("type", "String")
        
        return f"    op.add_column('{table_name}', sa.Column('{column.get('name')}', sa.{col_type}()))\n"
    
    def _generate_drop_table(self, operation: Dict) -> str:
        """Generate drop table operation"""
        return f"    op.drop_table('{operation.get('table')}')\n"
EOF

# ============================================================
# DOSYA 15: tools/testing_tools.py
# ============================================================
echo -e "${BLUE}📄 Creating tools/testing_tools.py...${NC}"
cat > tools/testing_tools.py << 'EOF'
"""
Test generation and execution tools
"""
from typing import Type, Optional, Dict, Any, List
from pydantic import BaseModel, Field
from crewai_tools import BaseTool


class TestGeneratorInput(BaseModel):
    """Input schema for test generation"""
    language: str = Field(..., description="Programming language")
    test_type: str = Field(..., description="Test type (unit, integration, e2e)")
    target_code: str = Field(..., description="Code to test")
    target_name: str = Field(..., description="Name of function/class to test")


class TestGeneratorTool(BaseTool):
    name: str = "Test Generator Tool"
    description: str = """
    Generates test code for various testing frameworks.
    Supports unit tests, integration tests, and e2e tests.
    Use this tool to create comprehensive test suites.
    """
    args_schema: Type[BaseModel] = TestGeneratorInput
    
    def _run(
        self,
        language: str,
        test_type: str,
        target_code: str,
        target_name: str
    ) -> str:
        """Generate test code"""
        
        generators = {
            ("python", "unit"): self._generate_python_unit,
            ("python", "integration"): self._generate_python_integration,
            ("go", "unit"): self._generate_go_unit,
            ("nodejs", "unit"): self._generate_nodejs_unit,
            ("nodejs", "e2e"): self._generate_nodejs_e2e
        }
        
        generator = generators.get((language.lower(), test_type.lower()))
        if not generator:
            return f"❌ Unsupported combination: {language}/{test_type}"
        
        return generator(target_name, target_code)
    
    def _generate_python_unit(self, target_name: str, target_code: str) -> str:
        """Generate Python unit tests"""
        return f'''"""
Unit tests for {target_name}
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from {target_name.lower()} import {target_name}


class Test{target_name}:
    """Test cases for {target_name}"""
    
    @pytest.fixture
    def instance(self):
        """Create test instance"""
        return {target_name}()
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock external dependencies"""
        return {{
            "db": Mock(),
            "cache": Mock()
        }}
    
    def test_initialization(self, instance):
        """Test proper initialization"""
        assert instance is not None
    
    def test_basic_functionality(self, instance):
        """Test basic functionality"""
        # Arrange
        expected = "expected_result"
        
        # Act
        result = instance.some_method()
        
        # Assert
        assert result == expected
    
    def test_edge_cases(self, instance):
        """Test edge cases"""
        # Test with empty input
        with pytest.raises(ValueError):
            instance.some_method(None)
        
        # Test with invalid input
        with pytest.raises(TypeError):
            instance.some_method(123)
    
    @pytest.mark.parametrize("input_val,expected", [
        ("valid_input", "valid_output"),
        ("another_input", "another_output"),
    ])
    def test_parameterized(self, instance, input_val, expected):
        """Test with multiple input combinations"""
        result = instance.some_method(input_val)
        assert result == expected
    
    @patch("{target_name.lower()}.external_service")
    def test_with_mock(self, mock_service, instance):
        """Test with mocked external service"""
        mock_service.return_value = "mocked_result"
        
        result = instance.method_using_service()
        
        mock_service.assert_called_once()
        assert result == "mocked_result"
    
    @pytest.mark.asyncio
    async def test_async_method(self, instance):
        """Test async method"""
        result = await instance.async_method()
        assert result is not None


class Test{target_name}Integration:
    """Integration tests for {target_name}"""
    
    @pytest.fixture
    def real_dependencies(self):
        """Setup real dependencies for integration tests"""
        # Setup
        yield {{}}
        # Teardown
    
    @pytest.mark.integration
    def test_with_database(self, real_dependencies):
        """Test with real database connection"""
        pass
'''
    
    def _generate_python_integration(self, target_name: str, target_code: str) -> str:
        """Generate Python integration tests"""
        return f'''"""
Integration tests for {target_name} API
"""
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


class TestAPI{target_name}:
    """API integration tests for {target_name}"""
    
    def test_create_{target_name.lower()}(self, client):
        """Test create endpoint"""
        response = client.post(
            "/{target_name.lower()}s",
            json={{"name": "Test", "description": "Test description"}}
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
    
    def test_get_{target_name.lower()}_list(self, client):
        """Test list endpoint"""
        response = client.get("/{target_name.lower()}s")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_{target_name.lower()}_by_id(self, client):
        """Test get by ID endpoint"""
        # Create first
        create_response = client.post(
            "/{target_name.lower()}s",
            json={{"name": "Test"}}
        )
        item_id = create_response.json()["id"]
        
        # Get by ID
        response = client.get(f"/{target_name.lower()}s/{{item_id}}")
        assert response.status_code == 200
    
    def test_update_{target_name.lower()}(self, client):
        """Test update endpoint"""
        # Create first
        create_response = client.post(
            "/{target_name.lower()}s",
            json={{"name": "Test"}}
        )
        item_id = create_response.json()["id"]
        
        # Update
        response = client.put(
            f"/{target_name.lower()}s/{{item_id}}",
            json={{"name": "Updated"}}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"
    
    def test_delete_{target_name.lower()}(self, client):
        """Test delete endpoint"""
        # Create first
        create_response = client.post(
            "/{target_name.lower()}s",
            json={{"name": "Test"}}
        )
        item_id = create_response.json()["id"]
        
        # Delete
        response = client.delete(f"/{target_name.lower()}s/{{item_id}}")
        assert response.status_code == 204
        
        # Verify deleted
        get_response = client.get(f"/{target_name.lower()}s/{{item_id}}")
        assert get_response.status_code == 404
    
    def test_not_found(self, client):
        """Test 404 response"""
        response = client.get("/{target_name.lower()}s/99999")
        assert response.status_code == 404
    
    def test_validation_error(self, client):
        """Test validation error"""
        response = client.post(
            "/{target_name.lower()}s",
            json={{}}  # Missing required fields
        )
        assert response.status_code == 422
'''
    
    def _generate_go_unit(self, target_name: str, target_code: str) -> str:
        """Generate Go unit tests"""
        return f'''package main

import (
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
)

// Mock dependencies
type Mock{target_name}Repository struct {{
    mock.Mock
}}

func (m *Mock{target_name}Repository) Get(id string) (*{target_name}, error) {{
    args := m.Called(id)
    if args.Get(0) == nil {{
        return nil, args.Error(1)
    }}
    return args.Get(0).(*{target_name}), args.Error(1)
}}

func Test{target_name}_Create(t *testing.T) {{
    // Arrange
    mockRepo := new(Mock{target_name}Repository)
    service := New{target_name}Service(mockRepo)
    
    // Act
    result, err := service.Create(&{target_name}{{Name: "Test"}})
    
    // Assert
    assert.NoError(t, err)
    assert.NotNil(t, result)
}}

func Test{target_name}_Get(t *testing.T) {{
    // Arrange
    mockRepo := new(Mock{target_name}Repository)
    mockRepo.On("Get", "123").Return(&{target_name}{{ID: "123", Name: "Test"}}, nil)
    
    service := New{target_name}Service(mockRepo)
    
    // Act
    result, err := service.Get("123")
    
    // Assert
    assert.NoError(t, err)
    assert.Equal(t, "123", result.ID)
    mockRepo.AssertExpectations(t)
}}

func Test{target_name}_Get_NotFound(t *testing.T) {{
    // Arrange
    mockRepo := new(Mock{target_name}Repository)
    mockRepo.On("Get", "999").Return(nil, ErrNotFound)
    
    service := New{target_name}Service(mockRepo)
    
    // Act
    result, err := service.Get("999")
    
    // Assert
    assert.Error(t, err)
    assert.Nil(t, result)
}}

// Table-driven tests
func Test{target_name}_Validation(t *testing.T) {{
    tests := []struct {{
        name    string
        input   *{target_name}
        wantErr bool
    }}{{
        {{"valid input", &{target_name}{{Name: "Test"}}, false}},
        {{"empty name", &{target_name}{{Name: ""}}, true}},
        {{"nil input", nil, true}},
    }}
    
    for _, tt := range tests {{
        t.Run(tt.name, func(t *testing.T) {{
            err := Validate{target_name}(tt.input)
            if tt.wantErr {{
                assert.Error(t, err)
            }} else {{
                assert.NoError(t, err)
            }}
        }})
    }}
}}
'''
    
    def _generate_nodejs_unit(self, target_name: str, target_code: str) -> str:
        """Generate Node.js unit tests with Jest"""
        return f'''/**
 * Unit tests for {target_name}
 */
import {{ describe, it, expect, beforeEach, jest }} from '@jest/globals';
import {{ {target_name} }} from './{target_name.lower()}';

describe('{target_name}', () => {{
    let instance: {target_name};
    
    beforeEach(() => {{
        instance = new {target_name}();
    }});
    
    describe('initialization', () => {{
        it('should create instance', () => {{
            expect(instance).toBeDefined();
        }});
    }});
    
    describe('basic functionality', () => {{
        it('should perform basic operation', () => {{
            const result = instance.someMethod();
            expect(result).toBeDefined();
        }});
        
        it('should handle valid input', () => {{
            const result = instance.process('valid');
            expect(result).toBe('expected');
        }});
    }});
    
    describe('error handling', () => {{
        it('should throw on invalid input', () => {{
            expect(() => instance.process(null)).toThrow();
        }});
        
        it('should handle empty input', () => {{
            expect(() => instance.process('')).toThrow('Input cannot be empty');
        }});
    }});
    
    describe('with mocks', () => {{
        it('should call external service', async () => {{
            const mockService = jest.fn().mockResolvedValue('mocked');
            instance.setService(mockService);
            
            const result = await instance.callService();
            
            expect(mockService).toHaveBeenCalled();
            expect(result).toBe('mocked');
        }});
    }});
    
    describe.each([
        ['input1', 'output1'],
        ['input2', 'output2'],
    ])('parameterized tests', (input, expected) => {{
        it(`should return ${{expected}} for ${{input}}`, () => {{
            const result = instance.transform(input);
            expect(result).toBe(expected);
        }});
    }});
}});
'''
    
    def _generate_nodejs_e2e(self, target_name: str, target_code: str) -> str:
        """Generate Node.js E2E tests with Playwright"""
        return f'''/**
 * E2E tests for {target_name}
 */
import {{ test, expect }} from '@playwright/test';

test.describe('{target_name} E2E Tests', () => {{
    test.beforeEach(async ({{ page }}) => {{
        await page.goto('/');
    }});
    
    test('should load main page', async ({{ page }}) => {{
        await expect(page).toHaveTitle(/{target_name}/);
    }});
    
    test('should create new {target_name.lower()}', async ({{ page }}) => {{
        // Click create button
        await page.click('[data-testid="create-button"]');
        
        // Fill form
        await page.fill('[name="name"]', 'Test {target_name}');
        await page.fill('[name="description"]', 'Test description');
        
        // Submit
        await page.click('[type="submit"]');
        
        // Verify created
        await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    }});
    
    test('should display {target_name.lower()} list', async ({{ page }}) => {{
        await page.goto('/{target_name.lower()}s');
        
        const items = page.locator('[data-testid="{target_name.lower()}-item"]');
        await expect(items).toHaveCount(await items.count());
    }});
    
    test('should navigate to detail page', async ({{ page }}) => {{
        await page.goto('/{target_name.lower()}s');
        
        // Click first item
        await page.click('[data-testid="{target_name.lower()}-item"]:first-child');
        
        // Verify navigation
        await expect(page).toHaveURL(/{target_name.lower()}s\\/\\d+/);
    }});
    
    test('should handle errors gracefully', async ({{ page }}) => {{
        await page.goto('/{target_name.lower()}s/invalid-id');
        
        await expect(page.locator('[data-testid="error-message"]')).toContainText('Not found');
    }});
}});
'''


class TestRunnerInput(BaseModel):
    """Input schema for test runner"""
    language: str = Field(..., description="Programming language")
    test_directory: str = Field(default="tests", description="Test directory")
    coverage: bool = Field(default=True, description="Generate coverage report")


class TestRunnerTool(BaseTool):
    name: str = "Test Runner Tool"
    description: str = """
    Runs test suites and generates coverage reports.
    Supports pytest, go test, jest, and more.
    Use this tool to execute tests.
    """
    args_schema: Type[BaseModel] = TestRunnerInput
    
    def _run(
        self,
        language: str,
        test_directory: str = "tests",
        coverage: bool = True
    ) -> str:
        """Generate test run command"""
        
        commands = {
            "python": f"pytest {test_directory} {'--cov=. --cov-report=html' if coverage else ''} -v",
            "go": f"go test {'--cover' if coverage else ''} -v ./...",
            "nodejs": f"npm test {'-- --coverage' if coverage else ''}",
            "csharp": f"dotnet test {'--collect:\"XPlat Code Coverage\"' if coverage else ''}"
        }
        
        cmd = commands.get(language.lower())
        if not cmd:
            return f"❌ Unsupported language: {language}"
        
        return f"""
# Test Runner Command
# Language: {language}
# Coverage: {'Enabled' if coverage else 'Disabled'}

{cmd}

# For CI/CD, use:
# {cmd} --ci
"""
EOF

# ============================================================
# DOSYA 16: agents/__init__.py
# ============================================================
echo -e "${BLUE}📄 Creating agents/__init__.py...${NC}"
cat > agents/__init__.py << 'EOF'
from .base_agent import BaseAgent
from .team_manager import TeamManagerAgent
from .analyst import AnalystAgent
from .backend_engineers import (
    BackendEngineerFactory,
    PythonBackendEngineer,
    GoBackendEngineer,
    NodeJSBackendEngineer,
    CSharpBackendEngineer
)
from .frontend_engineers import (
    FrontendEngineerFactory,
    ReactEngineer,
    AngularEngineer,
    NextJSEngineer
)
from .devops_engineer import DevOpsEngineer
from .system_engineer import SystemEngineer
from .db_engineer import DatabaseEngineer
from .qa_engineer import QAEngineer

__all__ = [
    "BaseAgent",
    "TeamManagerAgent",
    "AnalystAgent",
    "BackendEngineerFactory",
    "PythonBackendEngineer",
    "GoBackendEngineer",
    "NodeJSBackendEngineer",
    "CSharpBackendEngineer",
    "FrontendEngineerFactory",
    "ReactEngineer",
    "AngularEngineer",
    "NextJSEngineer",
    "DevOpsEngineer",
    "SystemEngineer",
    "DatabaseEngineer",
    "QAEngineer"
]
EOF

# ============================================================
# DOSYA 17: agents/base_agent.py
# ============================================================
echo -e "${BLUE}📄 Creating agents/base_agent.py...${NC}"
cat > agents/base_agent.py << 'EOF'
"""
Base agent class with common functionality
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Any
from crewai import Agent
from config.llm_config import get_llm_for_role


class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self):
        self._agent: Optional[Agent] = None
        self._tools: List[Any] = []
        self._setup_tools()
    
    @property
    @abstractmethod
    def role(self) -> str:
        """Agent's role"""
        pass
    
    @property
    @abstractmethod
    def goal(self) -> str:
        """Agent's goal"""
        pass
    
    @property
    @abstractmethod
    def backstory(self) -> str:
        """Agent's backstory"""
        pass
    
    @property
    def llm_type(self) -> str:
        """LLM type for this agent"""
        return "coder"
    
    @property
    def tools(self) -> List[Any]:
        """Agent's tools"""
        return self._tools
    
    @abstractmethod
    def _setup_tools(self) -> None:
        """Setup agent-specific tools"""
        pass
    
    def get_agent(self) -> Agent:
        """Get or create the CrewAI agent"""
        if self._agent is None:
            self._agent = Agent(
                role=self.role,
                goal=self.goal,
                backstory=self.backstory,
                tools=self.tools,
                llm=get_llm_for_role(self.llm_type),
                verbose=True,
                allow_delegation=self._allow_delegation(),
                max_iter=15,
                memory=True
            )
        return self._agent
    
    def _allow_delegation(self) -> bool:
        """Whether this agent can delegate tasks"""
        return False
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(role='{self.role}')"
EOF

# ============================================================
# DOSYA 18: agents/team_manager.py
# ============================================================
echo -e "${BLUE}📄 Creating agents/team_manager.py...${NC}"
cat > agents/team_manager.py << 'EOF'
"""
Team Manager Agent - Orchestrates all other agents
"""
from typing import List, Dict, Any
from crewai import Agent
from .base_agent import BaseAgent
from config.llm_config import get_llm_for_role


class TeamManagerAgent(BaseAgent):
    """Team Manager that orchestrates the development team"""
    
    @property
    def role(self) -> str:
        return "Technical Team Manager"
    
    @property
    def goal(self) -> str:
        return """
        Lead the development team to successfully deliver high-quality software projects.
        Analyze requirements, design architecture, decompose work into tasks,
        assign tasks to appropriate team members, and ensure successful delivery.
        """
    
    @property
    def backstory(self) -> str:
        return """
        You are a seasoned Technical Team Manager with 15+ years of experience in software development.
        You have led multiple successful projects across various domains including e-commerce,
        fintech, healthcare, and enterprise systems.
        
        Your expertise includes:
        - Analyzing complex requirements and translating them into technical specifications
        - Designing scalable and maintainable software architectures
        - Breaking down large projects into manageable tasks
        - Matching tasks to team members based on their expertise
        - Managing project timelines and identifying risks
        - Ensuring code quality and best practices
        
        You have deep knowledge of:
        - Multiple programming languages (Python, Go, Node.js, C#, Ruby)
        - Frontend frameworks (React, Angular, Next.js)
        - Cloud platforms (AWS, Azure, GCP)
        - DevOps practices and CI/CD pipelines
        - Database design and optimization
        - Security best practices
        
        You are known for your ability to see the big picture while also understanding
        technical details, making you an effective bridge between business requirements
        and technical implementation.
        """
    
    @property
    def llm_type(self) -> str:
        return "manager"
    
    def _setup_tools(self) -> None:
        """Team Manager doesn't need specific tools - uses LLM capabilities"""
        self._tools = []
    
    def _allow_delegation(self) -> bool:
        """Team Manager can delegate tasks"""
        return True
    
    def get_agent(self) -> Agent:
        """Get Team Manager agent with manager role enabled"""
        if self._agent is None:
            self._agent = Agent(
                role=self.role,
                goal=self.goal,
                backstory=self.backstory,
                tools=self.tools,
                llm=get_llm_for_role(self.llm_type),
                verbose=True,
                allow_delegation=True,
                max_iter=25,
                memory=True
            )
        return self._agent
EOF

# ============================================================
# DOSYA 19: agents/analyst.py
# ============================================================
echo -e "${BLUE}📄 Creating agents/analyst.py...${NC}"
cat > agents/analyst.py << 'EOF'
"""
Analyst Agent - Tracks progress and provides insights
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from crewai import Agent
from .base_agent import BaseAgent
from models.project import TaskDefinition
from config.settings import TaskStatus


class AnalystAgent(BaseAgent):
    """Analyst that tracks project progress and provides insights"""
    
    def __init__(self):
        super().__init__()
        self.tracked_tasks: Dict[str, TaskDefinition] = {}
        self.metrics: Dict[str, Any] = {}
    
    @property
    def role(self) -> str:
        return "Project Analyst"
    
    @property
    def goal(self) -> str:
        return """
        Track project progress, identify bottlenecks, generate reports,
        and provide actionable insights to improve team performance.
        """
    
    @property
    def backstory(self) -> str:
        return """
        You are an experienced Project Analyst with expertise in software development metrics
        and project management. You excel at:
        
        - Tracking task progress and team velocity
        - Identifying blockers and bottlenecks
        - Generating comprehensive progress reports
        - Providing data-driven recommendations
        - Forecasting project completion dates
        - Analyzing team performance patterns
        
        You use metrics and data to help the team continuously improve their processes
        and deliver high-quality software on time.
        """
    
    @property
    def llm_type(self) -> str:
        return "analyst"
    
    def _setup_tools(self) -> None:
        """Analyst uses custom tracking methods"""
        self._tools = []
    
    def track_task(self, task: TaskDefinition) -> None:
        """Add a task to tracking"""
        self.tracked_tasks[task.id] = task
    
    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        output: Any = None
    ) -> Optional[TaskDefinition]:
        """Update tracked task status"""
        if task_id not in self.tracked_tasks:
            return None
        
        task = self.tracked_tasks[task_id]
        task.status = status
        
        if status == TaskStatus.IN_PROGRESS and not task.started_at:
            task.started_at = datetime.now()
        elif status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now()
            task.output = output
            if task.started_at:
                task.actual_hours = (task.completed_at - task.started_at).total_seconds() / 3600
        
        return task
    
    def get_progress_report(self) -> Dict[str, Any]:
        """Generate progress report"""
        total = len(self.tracked_tasks)
        if total == 0:
            return {
                "total_tasks": 0,
                "completed": 0,
                "in_progress": 0,
                "pending": 0,
                "failed": 0,
                "blocked": 0,
                "completion_percentage": 0.0
            }
        
        status_counts = {status: 0 for status in TaskStatus}
        for task in self.tracked_tasks.values():
            status_counts[task.status] += 1
        
        completed = status_counts[TaskStatus.COMPLETED]
        
        return {
            "total_tasks": total,
            "completed": completed,
            "in_progress": status_counts[TaskStatus.IN_PROGRESS],
            "pending": status_counts[TaskStatus.PENDING],
            "failed": status_counts[TaskStatus.FAILED],
            "blocked": status_counts[TaskStatus.BLOCKED],
            "completion_percentage": (completed / total) * 100
        }
    
    def identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify bottlenecks in the project"""
        bottlenecks = []
        
        for task in self.tracked_tasks.values():
            # Check for overdue tasks
            if task.status == TaskStatus.IN_PROGRESS and task.started_at:
                elapsed = (datetime.now() - task.started_at).total_seconds() / 3600
                if elapsed > task.estimated_hours * 1.5:
                    bottlenecks.append({
                        "task_id": task.id,
                        "task_name": task.name,
                        "type": "overdue",
                        "estimated_hours": task.estimated_hours,
                        "elapsed_hours": elapsed,
                        "delay_percentage": ((elapsed - task.estimated_hours) / task.estimated_hours) * 100
                    })
            
            # Check for blocked tasks
            if task.status == TaskStatus.BLOCKED:
                bottlenecks.append({
                "task_id": task.id,
                    "task_name": task.name,
                    "type": "blocked",
                    "dependencies": task.dependencies,
                    "blocked_since": task.started_at.isoformat() if task.started_at else None
                })
        
        return bottlenecks
    
    def get_team_performance(self) -> Dict[str, Any]:
        """Analyze team performance by assignee"""
        performance = {}
        
        for task in self.tracked_tasks.values():
            assignee = task.assigned_to
            if assignee not in performance:
                performance[assignee] = {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "total_estimated_hours": 0,
                    "total_actual_hours": 0,
                    "on_time_completions": 0
                }
            
            performance[assignee]["total_tasks"] += 1
            performance[assignee]["total_estimated_hours"] += task.estimated_hours
            
            if task.status == TaskStatus.COMPLETED:
                performance[assignee]["completed_tasks"] += 1
                if task.actual_hours:
                    performance[assignee]["total_actual_hours"] += task.actual_hours
                    if task.actual_hours <= task.estimated_hours:
                        performance[assignee]["on_time_completions"] += 1
        
        # Calculate efficiency for each assignee
        for assignee, data in performance.items():
            if data["completed_tasks"] > 0:
                data["completion_rate"] = (data["completed_tasks"] / data["total_tasks"]) * 100
                data["on_time_rate"] = (data["on_time_completions"] / data["completed_tasks"]) * 100
                if data["total_actual_hours"] > 0:
                    data["efficiency"] = (data["total_estimated_hours"] / data["total_actual_hours"]) * 100
        
        return performance
    
    def generate_summary_report(self) -> str:
        """Generate a comprehensive summary report"""
        progress = self.get_progress_report()
        bottlenecks = self.identify_bottlenecks()
        performance = self.get_team_performance()
        
        report = f"""
================================================================================
                         PROJECT PROGRESS REPORT
                         Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================================

📊 OVERALL PROGRESS
-------------------
Total Tasks: {progress['total_tasks']}
Completed: {progress['completed']} ({progress['completion_percentage']:.1f}%)
In Progress: {progress['in_progress']}
Pending: {progress['pending']}
Blocked: {progress['blocked']}
Failed: {progress['failed']}

"""
        
        if bottlenecks:
            report += "⚠️  BOTTLENECKS IDENTIFIED\n"
            report += "-" * 25 + "\n"
            for bottleneck in bottlenecks:
                report += f"  - {bottleneck['task_name']} ({bottleneck['type']})\n"
            report += "\n"
        
        if performance:
            report += "👥 TEAM PERFORMANCE\n"
            report += "-" * 25 + "\n"
            for assignee, data in performance.items():
                report += f"  {assignee}:\n"
                report += f"    Tasks: {data['completed_tasks']}/{data['total_tasks']} completed\n"
                if 'completion_rate' in data:
                    report += f"    Completion Rate: {data['completion_rate']:.1f}%\n"
                if 'on_time_rate' in data:
                    report += f"    On-Time Rate: {data['on_time_rate']:.1f}%\n"
            report += "\n"
        
        report += "=" * 80 + "\n"
        
        return report
EOF

# ============================================================
# DOSYA 20: agents/backend_engineers.py
# ============================================================
echo -e "${BLUE}📄 Creating agents/backend_engineers.py...${NC}"
cat > agents/backend_engineers.py << 'EOF'
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
EOF

# ============================================================
# DOSYA 21: agents/frontend_engineers.py
# ============================================================
echo -e "${BLUE}📄 Creating agents/frontend_engineers.py...${NC}"
cat > agents/frontend_engineers.py << 'EOF'
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
EOF

# ============================================================
# DOSYA 22: agents/devops_engineer.py
# ============================================================
echo -e "${BLUE}📄 Creating agents/devops_engineer.py...${NC}"
cat > agents/devops_engineer.py << 'EOF'
"""
DevOps Engineer Agent
"""
from typing import List
from .base_agent import BaseAgent
from tools.infrastructure_tools import TerraformTool, KubernetesTool, DockerTool, AnsibleTool
from tools.cicd_tools import GitHubActionsTool, GitLabCITool, JenkinsTool
from tools.file_tools import FileWriterTool


class DevOpsEngineer(BaseAgent):
    """DevOps Engineer for CI/CD, containerization, and automation"""
    
    @property
    def role(self) -> str:
        return "Senior DevOps Engineer"
    
    @property
    def goal(self) -> str:
        return """
        Design and implement CI/CD pipelines, containerization strategies,
        and infrastructure automation. Ensure reliable, secure, and efficient
        software delivery processes.
        """
    
    @property
    def backstory(self) -> str:
        return """
        You are a Senior DevOps Engineer with 10+ years of experience in
        software delivery and infrastructure automation. Your expertise includes:
        
        - CI/CD pipeline design and implementation
        - GitHub Actions, GitLab CI, Jenkins, ArgoCD
        - Docker containerization and multi-stage builds
        - Kubernetes deployments and Helm charts
        - Infrastructure as Code with Terraform and Pulumi
        - Configuration management with Ansible
        - GitOps practices and workflows
        - Security scanning and compliance (SAST, DAST, SCA)
        - Monitoring and observability setup
        
        You design pipelines that are fast, reliable, and secure.
        You follow GitOps principles and infrastructure as code best practices.
        """
    
    def _setup_tools(self) -> None:
        """Setup DevOps engineer tools"""
        self._tools = [
            DockerTool(),
            KubernetesTool(),
            TerraformTool(),
            AnsibleTool(),
            GitHubActionsTool(),
            GitLabCITool(),
            JenkinsTool(),
            FileWriterTool()
        ]
EOF

# ============================================================
# DOSYA 23: agents/system_engineer.py
# ============================================================
echo -e "${BLUE}📄 Creating agents/system_engineer.py...${NC}"
cat > agents/system_engineer.py << 'EOF'
"""
System/Cloud Engineer Agent
"""
from typing import List
from .base_agent import BaseAgent
from tools.infrastructure_tools import TerraformTool, KubernetesTool, AnsibleTool
from tools.file_tools import FileWriterTool


class SystemEngineer(BaseAgent):
    """System/Cloud Engineer for infrastructure and cloud architecture"""
    
    @property
    def role(self) -> str:
        return "Senior Cloud/System Engineer"
    
    @property
    def goal(self) -> str:
        return """
        Design and implement scalable, secure, and cost-effective cloud
        infrastructure. Ensure high availability, disaster recovery,
        and optimal performance of all systems.
        """
    
    @property
    def backstory(self) -> str:
        return """
        You are a Senior Cloud/System Engineer with 12+ years of experience
        designing and managing cloud infrastructure. Your expertise includes:
        
        AWS:
        - VPC, EC2, EKS, ECS, Lambda
        - RDS, DynamoDB, ElastiCache
        - S3, CloudFront, Route53
        - IAM, KMS, Secrets Manager
        
        Azure:
        - Virtual Networks, VMs, AKS
        - Azure SQL, Cosmos DB, Redis
        - Blob Storage, CDN
        - Active Directory, Key Vault
        
        GCP:
        - VPC, GCE, GKE
        - Cloud SQL, Firestore, Memorystore
        - Cloud Storage, Cloud CDN
        - IAM, Secret Manager
        
        General:
        - Multi-cloud and hybrid architectures
        - High availability and disaster recovery
        - Cost optimization strategies
        - Security best practices and compliance
        - Performance tuning and optimization
        - Infrastructure as Code (Terraform, Pulumi)
        
        You design infrastructure that is scalable, secure, and cost-effective.
        You follow cloud-native best practices and Well-Architected Framework.
        """
    
    def _setup_tools(self) -> None:
        """Setup system engineer tools"""
        self._tools = [
            TerraformTool(),
            KubernetesTool(),
            AnsibleTool(),
            FileWriterTool()
        ]
EOF

# ============================================================
# DOSYA 24: agents/db_engineer.py
# ============================================================
echo -e "${BLUE}📄 Creating agents/db_engineer.py...${NC}"
cat > agents/db_engineer.py << 'EOF'
"""
Database Engineer Agent
"""
from typing import List
from .base_agent import BaseAgent
from tools.database_tools import DatabaseSchemaTool, MigrationTool
from tools.file_tools import FileWriterTool


class DatabaseEngineer(BaseAgent):
    """Database Engineer for schema design and optimization"""
    
    @property
    def role(self) -> str:
        return "Senior Database Engineer"
    
    @property
    def goal(self) -> str:
        return """
        Design optimal database schemas, implement efficient queries,
        ensure data integrity, and maintain high performance at scale.
        """
    
    @property
    def backstory(self) -> str:
        return """
        You are a Senior Database Engineer with 12+ years of experience
        in database design and administration. Your expertise includes:
        
        Relational Databases:
        - PostgreSQL: Advanced features, partitioning, replication
        - MySQL: InnoDB optimization, clustering
        - SQL Server: Always On, columnstore indexes
        
        NoSQL Databases:
        - MongoDB: Sharding, aggregation pipelines
        - Redis: Clustering, data structures, Lua scripting
        - Elasticsearch: Indexing, search optimization
        - Cassandra: Wide-column design, consistency tuning
        
        Database Design:
        - Normalization and denormalization strategies
        - Index design and optimization
        - Query performance tuning
        - Data modeling for different use cases
        
        Operations:
        - Backup and recovery strategies
        - Replication and high availability
        - Migration planning and execution
        - Monitoring and alerting
        
        You design databases that are performant, scalable, and maintainable.
        You always consider data integrity, consistency, and access patterns.
        """
    
    def _setup_tools(self) -> None:
        """Setup database engineer tools"""
        self._tools = [
            DatabaseSchemaTool(),
            MigrationTool(),
            FileWriterTool()
        ]
EOF

# ============================================================
# DOSYA 25: agents/qa_engineer.py
# ============================================================
echo -e "${BLUE}📄 Creating agents/qa_engineer.py...${NC}"
cat > agents/qa_engineer.py << 'EOF'
"""
QA Engineer Agent
"""
from typing import List
from .base_agent import BaseAgent
from tools.testing_tools import TestGeneratorTool, TestRunnerTool
from tools.code_tools import CodeAnalysisTool
from tools.file_tools import FileWriterTool


class QAEngineer(BaseAgent):
    """QA Engineer for testing and quality assurance"""
    
    @property
    def role(self) -> str:
        return "Senior QA Engineer"
    
    @property
    def goal(self) -> str:
        return """
        Ensure software quality through comprehensive testing strategies.
        Design and implement test suites that catch bugs early and
        prevent regressions.
        """
    
    @property
    def backstory(self) -> str:
        return """
        You are a Senior QA Engineer with 10+ years of experience in
        software testing and quality assurance. Your expertise includes:
        
        Testing Types:
        - Unit testing with high coverage
        - Integration testing for APIs and services
        - End-to-end testing for user flows
        - Performance and load testing
        - Security testing and penetration testing
        - Accessibility testing (WCAG compliance)
        
        Testing Frameworks:
        - Python: pytest, unittest, behave
        - JavaScript: Jest, Mocha, Cypress, Playwright
        - Go: testing, testify
        - C#: xUnit, NUnit, SpecFlow
        
        Tools:
        - Selenium, Playwright, Cypress for E2E
        - JMeter, k6, Locust for load testing
        - OWASP ZAP, Burp Suite for security
        - SonarQube for code quality
        
        Practices:
        - Test-Driven Development (TDD)
        - Behavior-Driven Development (BDD)
        - Continuous testing in CI/CD
        - Test data management
        - Defect tracking and analysis
        
        You create comprehensive test suites that ensure software quality.
        You identify edge cases and potential failure modes.
        """
    
    def _setup_tools(self) -> None:
        """Setup QA engineer tools"""
        self._tools = [
            TestGeneratorTool(),
            TestRunnerTool(),
            CodeAnalysisTool(),
            FileWriterTool()
        ]
EOF

# ============================================================
# DOSYA 26: tasks/__init__.py
# ============================================================
echo -e "${BLUE}📄 Creating tasks/__init__.py...${NC}"
cat > tasks/__init__.py << 'EOF'
from .task_factory import TaskFactory
from .analysis_tasks import AnalysisTasks
from .backend_tasks import BackendTasks
from .frontend_tasks import FrontendTasks
from .infrastructure_tasks import InfrastructureTasks
from .testing_tasks import TestingTasks

__all__ = [
    "TaskFactory",
    "AnalysisTasks",
    "BackendTasks",
    "FrontendTasks",
    "InfrastructureTasks",
    "TestingTasks"
]
EOF

# ============================================================
# DOSYA 27: tasks/task_factory.py
# ============================================================
echo -e "${BLUE}📄 Creating tasks/task_factory.py...${NC}"
cat > tasks/task_factory.py << 'EOF'
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
EOF

# ============================================================
# DOSYA 28: tasks/analysis_tasks.py
# ============================================================
echo -e "${BLUE}📄 Creating tasks/analysis_tasks.py...${NC}"
cat > tasks/analysis_tasks.py << 'EOF'
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
EOF

# ============================================================
# DOSYA 29: tasks/backend_tasks.py
# ============================================================
echo -e "${BLUE}📄 Creating tasks/backend_tasks.py...${NC}"
cat > tasks/backend_tasks.py << 'EOF'
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
EOF

# ============================================================
# DOSYA 30: tasks/frontend_tasks.py
# ============================================================
echo -e "${BLUE}📄 Creating tasks/frontend_tasks.py...${NC}"
cat > tasks/frontend_tasks.py << 'EOF'
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
EOF

# ============================================================
# DOSYA 31: tasks/infrastructure_tasks.py
# ============================================================
echo -e "${BLUE}📄 Creating tasks/infrastructure_tasks.py...${NC}"
cat > tasks/infrastructure_tasks.py << 'EOF'
"""
Infrastructure and DevOps tasks
"""
from typing import Optional, List, Dict, Any
from crewai import Task, Agent


class InfrastructureTasks:
    """Tasks for infrastructure and DevOps"""
    
    @staticmethod
    def design_infrastructure(
        agent: Agent,
        infra_config: Dict[str, Any]
    ) -> Task:
        """Design cloud infrastructure"""
        return Task(
            description=f"""
            Design cloud infrastructure for:
            
            Configuration:
            {infra_config}
            
            Design:
            1. VPC/Network architecture
            2. Compute resources (EKS/GKE/AKS or EC2/VMs)
            3. Database infrastructure
            4. Load balancing and CDN
            5. Security groups and IAM
            6. Monitoring and logging
            7. Backup and DR strategy
            """,
            expected_output="""
            Infrastructure design document:
            - Architecture diagram description
            - Resource specifications
            - Network topology
            - Security configuration
            - Cost estimates
            """,
            agent=agent
        )
    
    @staticmethod
    def implement_terraform(
        agent: Agent,
        resources: List[Dict[str, Any]],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Implement Terraform configurations"""
        return Task(
            description=f"""
            Implement Terraform configurations for:
            
            Resources:
            {resources}
            
            Requirements:
            1. Modular structure
            2. Environment separation (dev/staging/prod)
            3. State management (remote backend)
            4. Variable definitions
            5. Output definitions
            6. Security best practices
            """,
            expected_output="""
            Complete Terraform configuration:
            - Module definitions
            - Environment configurations
            - Variables and outputs
            - Backend configuration
            - README with usage
            """,
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def implement_kubernetes(
        agent: Agent,
        services: List[Dict[str, Any]],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Implement Kubernetes manifests"""
        return Task(
            description=f"""
            Implement Kubernetes manifests for:
            
            Services:
            {services}
            
            Requirements:
            1. Deployments with proper resource limits
            2. Services and Ingress
            3. ConfigMaps and Secrets
            4. HPA for auto-scaling
            5. Network policies
            6. RBAC configuration
            """,
            expected_output="""
            Complete Kubernetes manifests:
            - Deployment manifests
            - Service definitions
            - Ingress configuration
            - ConfigMaps and Secrets
            - HPA configurations
            - Helm chart (optional)
            """,
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def implement_cicd(
        agent: Agent,
        cicd_config: Dict[str, Any],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Implement CI/CD pipelines"""
        return Task(
            description=f"""
            Implement CI/CD pipelines for:
            
            Configuration:
            {cicd_config}
            
            Requirements:
            1. Build stage with testing
            2. Security scanning (SAST/DAST)
            3. Container image building
            4. Artifact management
            5. Deployment automation
            6. Environment promotion
            7. Rollback procedures
            """,
            expected_output="""
            Complete CI/CD implementation:
            - Pipeline configuration files
            - Build scripts
            - Deployment scripts
            - Environment configs
            - Documentation
            """,
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def implement_monitoring(
        agent: Agent,
        monitoring_config: Dict[str, Any],
        context: Optional[List[Task]] = None
    ) -> Task:
        """Implement monitoring and observability"""
        return Task(
            description=f"""
            Implement monitoring and observability:
            
            Configuration:
            {monitoring_config}
            
            Requirements:
            1. Metrics collection (Prometheus)
            2. Log aggregation (Loki/ELK)
            3. Tracing (Jaeger/Zipkin)
            4. Dashboards (Grafana)
            5. Alerting rules
            6. SLO/SLI definitions
            """,
            expected_output="""
            Complete monitoring implementation:
            - Prometheus configuration
            - Grafana dashboards
            - Alert rules
            - Log collection setup
            - Tracing configuration
            """,
            agent=agent,
            context=context or []
        )
EOF

# ============================================================
# DOSYA 32: tasks/testing_tasks.py
# ============================================================
echo -e "${BLUE}📄 Creating tasks/testing_tasks.py...${NC}"
cat > tasks/testing_tasks.py << 'EOF'
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
EOF

# ============================================================
# DOSYA 33: crews/__init__.py
# ============================================================
echo -e "${BLUE}📄 Creating crews/__init__.py...${NC}"
cat > crews/__init__.py << 'EOF'
from .development_crew import DevelopmentCrew
from .analysis_crew import AnalysisCrew

__all__ = ["DevelopmentCrew", "AnalysisCrew"]
EOF

# ============================================================
# DOSYA 34: crews/development_crew.py
# ============================================================
echo -e "${BLUE}📄 Creating crews/development_crew.py...${NC}"
cat > crews/development_crew.py << 'EOF'
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
EOF

# ============================================================
# DOSYA 35: crews/analysis_crew.py
# ============================================================
echo -e "${BLUE}📄 Creating crews/analysis_crew.py...${NC}"
cat > crews/analysis_crew.py << 'EOF'
"""
Analysis Crew - For requirement analysis and architecture design only
"""
from typing import Dict, Any, Optional
from crewai import Crew, Process
from loguru import logger

from agents import TeamManagerAgent, AnalystAgent
from tasks import AnalysisTasks
from models.requirements import ComplexStackRequest
from config.settings import settings


class AnalysisCrew:
    """
    Lighter crew for analysis phase only
    """
    
    def __init__(self, request: ComplexStackRequest):
        self.request = request
        self.manager = TeamManagerAgent()
        self.analyst = AnalystAgent()
        self.crew: Optional[Crew] = None
        
        logger.info(f"Initialized AnalysisCrew for: {request.project_name}")
    
    def build_crew(self) -> Crew:
        """Build analysis crew"""
        
        # Create analysis tasks
        requirement_task = AnalysisTasks.requirement_analysis(
            agent=self.manager.get_agent(),
            request=self.request
        )
        
        architecture_task = AnalysisTasks.architecture_design(
            agent=self.manager.get_agent(),
            request=self.request,
            context=[requirement_task]
        )
        
        decomposition_task = AnalysisTasks.task_decomposition(
            agent=self.manager.get_agent(),
            request=self.request,
            context=[requirement_task, architecture_task]
        )
        
        self.crew = Crew(
            agents=[
                self.manager.get_agent(),
                self.analyst.get_agent()
            ],
            tasks=[
                requirement_task,
                architecture_task,
                decomposition_task
            ],
            process=Process.sequential,
            verbose=settings.crewai_verbose
        )
        
        return self.crew
    
    def run(self) -> Dict[str, Any]:
        """Run analysis"""
        if not self.crew:
            self.build_crew()
        
        logger.info("Running analysis...")
        
        try:
            result = self.crew.kickoff()
            return {
                "status": "success",
                "analysis": result
            }
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
EOF

# ============================================================
# DOSYA 36: workflows/__init__.py
# ============================================================
echo -e "${BLUE}📄 Creating workflows/__init__.py...${NC}"
cat > workflows/__init__.py << 'EOF'
from .project_workflow import ProjectWorkflow

__all__ = ["ProjectWorkflow"]
EOF

# ============================================================
# DOSYA 37: workflows/project_workflow.py
# ============================================================
echo -e "${BLUE}📄 Creating workflows/project_workflow.py...${NC}"
cat > workflows/project_workflow.py << 'EOF'
"""
Project Workflow - Orchestrates the complete project lifecycle
"""
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from loguru import logger
import json
import os

from models.requirements import ComplexStackRequest
from models.project import Project
from crews import DevelopmentCrew, AnalysisCrew
from config.settings import settings


class ProjectWorkflow:
    """
    Manages the complete project development workflow
    """
    
    def __init__(
        self,
        request: ComplexStackRequest,
        output_dir: Optional[str] = None,
        on_progress: Optional[Callable[[Dict], None]] = None
    ):
        self.request = request
        self.output_dir = output_dir or os.path.join(settings.output_dir, request.project_name)
        self.on_progress = on_progress
        
        self.project = Project(
            name=request.project_name,
            description=request.description
        )
        
        self.phases = {
            "analysis": {"status": "pending", "result": None},
            "development": {"status": "pending", "result": None},
            "review": {"status": "pending", "result": None}
        }
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"Initialized ProjectWorkflow: {request.project_name}")
    
    def _emit_progress(self, phase: str, status: str, data: Any = None):
        """Emit progress update"""
        progress = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "status": status,
            "data": data,
            "overall_progress": self._calculate_progress()
        }
        
        if self.on_progress:
            self.on_progress(progress)
        
        logger.info(f"Progress: {phase} - {status}")
    
    def _calculate_progress(self) -> float:
        """Calculate overall progress percentage"""
        completed = sum(1 for p in self.phases.values() if p["status"] == "completed")
        return (completed / len(self.phases)) * 100
    
    def run_analysis_only(self) -> Dict[str, Any]:
        """Run only the analysis phase"""
        logger.info("Running analysis phase only...")
        
        self._emit_progress("analysis", "started")
        
        try:
            analysis_crew = AnalysisCrew(self.request)
            result = analysis_crew.run()
            
            self.phases["analysis"]["status"] = "completed"
            self.phases["analysis"]["result"] = result
            
            # Save analysis results
            self._save_output("analysis", result)
            
            self._emit_progress("analysis", "completed", result)
            
            return result
            
        except Exception as e:
            logger.error(f"Analysis phase failed: {e}")
            self.phases["analysis"]["status"] = "failed"
            self._emit_progress("analysis", "failed", str(e))
            raise
    
    def run_full_development(self) -> Dict[str, Any]:
        """Run the complete development workflow"""
        logger.info("Starting full development workflow...")
        
        results = {}
        
        # Phase 1: Analysis
        self._emit_progress("analysis", "started")
        try:
            analysis_crew = AnalysisCrew(self.request)
            analysis_result = analysis_crew.run()
            
            self.phases["analysis"]["status"] = "completed"
            self.phases["analysis"]["result"] = analysis_result
            results["analysis"] = analysis_result
            
            self._save_output("analysis", analysis_result)
            self._emit_progress("analysis", "completed", analysis_result)
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.phases["analysis"]["status"] = "failed"
            self._emit_progress("analysis", "failed", str(e))
            raise
        
        # Phase 2: Development
        self._emit_progress("development", "started")
        try:
            dev_crew = DevelopmentCrew(self.request)
            dev_result = dev_crew.run()
            
            self.phases["development"]["status"] = "completed"
            self.phases["development"]["result"] = dev_result
            results["development"] = dev_result
            
            self._save_output("development", dev_result)
            self._emit_progress("development", "completed", dev_result)
            
        except Exception as e:
            logger.error(f"Development failed: {e}")
            self.phases["development"]["status"] = "failed"
            self._emit_progress("development", "failed", str(e))
            raise
        
        # Phase 3: Review
        self._emit_progress("review", "started")
        try:
            review_result = self._run_review(results)
            
            self.phases["review"]["status"] = "completed"
            self.phases["review"]["result"] = review_result
            results["review"] = review_result
            
            self._save_output("review", review_result)
            self._emit_progress("review", "completed", review_result)
            
        except Exception as e:
            logger.error(f"Review failed: {e}")
            self.phases["review"]["status"] = "failed"
            self._emit_progress("review", "failed", str(e))
            raise
        
        # Final summary
        results["summary"] = self._generate_summary(results)
        self._save_output("summary", results["summary"])
        
        logger.info("Full development workflow completed")
        
        return results
    
    def _run_review(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Run review phase (placeholder for actual review logic)"""
        return {
            "status": "completed",
            "findings": [],
            "recommendations": [],
            "approval": True
        }
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate project summary"""
        return {
            "project_name": self.request.project_name,
            "completed_at": datetime.now().isoformat(),
            "phases_completed": len([p for p in self.phases.values() if p["status"] == "completed"]),
            "total_phases": len(self.phases),
            "output_directory": self.output_dir
        }
    
    def _save_output(self, phase: str, data: Any):
        """Save phase output to file"""
        output_file = os.path.join(self.output_dir, f"{phase}_output.json")
        
        try:
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Saved {phase} output to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save {phase} output: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        return {
            "project": self.project.model_dump(),
            "phases": self.phases,
            "progress": self._calculate_progress()
        }
EOF

# ============================================================
# DOSYA 38: main.py
# ============================================================
echo -e "${BLUE}📄 Creating main.py...${NC}"
cat > main.py << 'EOF'
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
EOF

# ============================================================
# DOSYA 39: tests/test_agents.py
# ============================================================
echo -e "${BLUE}📄 Creating tests/test_agents.py...${NC}"
cat > tests/test_agents.py << 'EOF'
"""
Tests for agent classes
"""
import pytest
from unittest.mock import patch, MagicMock

from agents import (
    TeamManagerAgent,
    AnalystAgent,
    BackendEngineerFactory,
    FrontendEngineerFactory,
    DevOpsEngineer,
    DatabaseEngineer,
    QAEngineer
)


class TestTeamManagerAgent:
    """Tests for TeamManagerAgent"""
    
    def test_initialization(self):
        """Test agent initialization"""
        agent = TeamManagerAgent()
        assert agent.role == "Technical Team Manager"
        assert agent._allow_delegation() == True
    
    def test_goal_and_backstory(self):
        """Test goal and backstory are set"""
        agent = TeamManagerAgent()
        assert len(agent.goal) > 0
        assert len(agent.backstory) > 0


class TestBackendEngineerFactory:
    """Tests for BackendEngineerFactory"""
    
    def test_create_python_engineer(self):
        """Test creating Python backend engineer"""
        engineer = BackendEngineerFactory.create("python")
        assert engineer.language == "Python"
        assert "FastAPI" in engineer.frameworks
    
    def test_create_go_engineer(self):
        """Test creating Go backend engineer"""
        engineer = BackendEngineerFactory.create("go")
        assert engineer.language == "Go"
        assert "Gin" in engineer.frameworks
    
    def test_create_nodejs_engineer(self):
        """Test creating Node.js backend engineer"""
        engineer = BackendEngineerFactory.create("nodejs")
        assert engineer.language == "Node.js"
        assert "NestJS" in engineer.frameworks
    
    def test_unsupported_language(self):
        """Test error for unsupported language"""
        with pytest.raises(ValueError):
            BackendEngineerFactory.create("unsupported")


class TestFrontendEngineerFactory:
    """Tests for FrontendEngineerFactory"""
    
    def test_create_react_engineer(self):
        """Test creating React engineer"""
        engineer = FrontendEngineerFactory.create("react")
        assert engineer.framework == "React"
    
    def test_create_angular_engineer(self):
        """Test creating Angular engineer"""
        engineer = FrontendEngineerFactory.create("angular")
        assert engineer.framework == "Angular"
    
    def test_create_nextjs_engineer(self):
        """Test creating Next.js engineer"""
        engineer = FrontendEngineerFactory.create("nextjs")
        assert engineer.framework == "Next.js"


class TestAnalystAgent:
    """Tests for AnalystAgent"""
    
    def test_initialization(self):
        """Test analyst initialization"""
        analyst = AnalystAgent()
        assert analyst.role == "Project Analyst"
        assert len(analyst.tracked_tasks) == 0
    
    def test_progress_report_empty(self):
        """Test progress report with no tasks"""
        analyst = AnalystAgent()
        report = analyst.get_progress_report()
        assert report["total_tasks"] == 0
        assert report["completion_percentage"] == 0.0
EOF

# ============================================================
# DOSYA 40: tests/test_tools.py
# ============================================================
echo -e "${BLUE}📄 Creating tests/test_tools.py...${NC}"
cat > tests/test_tools.py << 'EOF'
"""
Tests for tools
"""
import pytest
from tools.code_tools import CodeGenerationTool, CodeAnalysisTool
from tools.infrastructure_tools import DockerTool, KubernetesTool
from tools.cicd_tools import GitHubActionsTool


class TestCodeGenerationTool:
    """Tests for CodeGenerationTool"""
    
    def test_initialization(self):
        """Test tool initialization"""
        tool = CodeGenerationTool()
        assert tool.name == "Code Generation Tool"
    
    def test_run_python_model(self):
        """Test generating Python model"""
        tool = CodeGenerationTool()
        result = tool._run(
            language="python",
            framework="fastapi",
            component_type="model",
            component_name="User",
            specifications="User model with email and name"
        )
        assert "class" in result or "Generated" in result


class TestDockerTool:
    """Tests for DockerTool"""
    
    def test_python_dockerfile(self):
        """Test generating Python Dockerfile"""
        tool = DockerTool()
        result = tool._run(
            language="python",
            framework="fastapi",
            app_name="myapp",
            port=8080
        )
        assert "FROM python" in result
        assert "EXPOSE 8080" in result
    
    def test_go_dockerfile(self):
        """Test generating Go Dockerfile"""
        tool = DockerTool()
        result = tool._run(
            language="go",
            framework="gin",
            app_name="myapp",
            port=8080
        )
        assert "FROM golang" in result


class TestKubernetesTool:
    """Tests for KubernetesTool"""
    
    def test_deployment_generation(self):
        """Test generating Kubernetes deployment"""
        tool = KubernetesTool()
        result = tool._run(
            resource_type="deployment",
            name="myapp",
            namespace="default",
            spec={"replicas": 3, "image": "myapp:latest", "port": 8080}
        )
        assert "kind: Deployment" in result
        assert "replicas: 3" in result


class TestGitHubActionsTool:
    """Tests for GitHubActionsTool"""
    
    def test_workflow_generation(self):
        """Test generating GitHub Actions workflow"""
        tool = GitHubActionsTool()
        result = tool._run(
            workflow_name="CI/CD Pipeline",
            language="python",
            triggers=["push", "pull_request"],
            include_deploy=True,
            deploy_target="kubernetes"
        )
        assert "name: CI/CD Pipeline" in result
        assert "push:" in result
EOF

# ============================================================
# DOSYA 41: tests/conftest.py
# ============================================================
echo -e "${BLUE}📄 Creating tests/conftest.py...${NC}"
cat > tests/conftest.py << 'EOF'
"""
Pytest configuration and fixtures
"""
import pytest
import os
from unittest.mock import MagicMock, patch

# Set test environment
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture
def mock_llm():
    """Mock LLM for testing"""
    with patch("config.llm_config.get_llm") as mock:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Test response")
        mock.return_value = mock_llm
        yield mock_llm


@pytest.fixture
def sample_request():
    """Sample project request for testing"""
    from models.requirements import ComplexStackRequest
    
    return ComplexStackRequest(
        project_name="Test Project",
        description="A test project",
        backend_language="python",
        backend_framework="FastAPI",
        frontend_framework="react"
    )


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return str(output_dir)
EOF

# ============================================================
# DOSYA 42: examples/simple_project.py
# ============================================================
echo -e "${BLUE}📄 Creating examples/simple_project.py...${NC}"
cat > examples/simple_project.py << 'EOF'
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
EOF

# ============================================================
# DOSYA 43: examples/full_stack_project.py
# ============================================================
echo -e "${BLUE}📄 Creating examples/full_stack_project.py...${NC}"
cat > examples/full_stack_project.py << 'EOF'
"""
Example: Full-stack project generation
"""
from models.requirements import (
    ComplexStackRequest,
    DatabaseRequirement,
    InfrastructureRequirement,
    SecurityRequirement,
    QueueRequirement
)
from workflows import ProjectWorkflow


def main():
    """Run full-stack project development"""
    
    # Define comprehensive project requirements
    request = ComplexStackRequest(
        project_name="E-Commerce Platform",
        description="""
        A modern e-commerce platform with:
        - User authentication and authorization
        - Product catalog with search
        - Shopping cart and checkout
        - Order management
        - Payment integration
        - Admin dashboard
        """,
        backend_language="python",
        backend_framework="FastAPI",
        api_type="REST",
        microservices=[
            {"name": "auth-service", "description": "Authentication service"},
            {"name": "product-service", "description": "Product catalog service"},
            {"name": "order-service", "description": "Order management service"},
            {"name": "payment-service", "description": "Payment processing service"}
        ],
        frontend_framework="nextjs",
        ssr_required=True,
        database=DatabaseRequirement(
            primary_db={"type": "postgresql", "version": "15"},
            cache_db={"type": "redis", "version": "7"},
            search_db={"type": "elasticsearch", "version": "8"}
        ),
        queue=QueueRequirement(
            type="RabbitMQ",
            use_cases=["order_processing", "email_notifications", "inventory_updates"]
        ),
        infrastructure=InfrastructureRequirement(
            environment="cloud",
            cloud_provider="AWS",
            regions=["us-east-1", "eu-west-1"],
            high_availability=True,
            disaster_recovery=True,
            kubernetes_config={
                "cluster_name": "ecommerce-cluster",
                "node_count": 3,
                "instance_type": "t3.large"
            }
        ),
        security=SecurityRequirement(
            authentication="JWT",
            authorization="RBAC",
            encryption=True,
            waf=True,
            ddos_protection=True,
            compliance=["PCI-DSS", "GDPR"]
        ),
        cicd_platform="github_actions",
        deployment_strategy="blue-green",
        monitoring_stack=["prometheus", "grafana", "loki", "jaeger"],
        rate_limiting=True,
        api_gateway="Kong"
    )
    
    # Progress callback
    def on_progress(progress):
        print(f"[{progress['phase']}] {progress['status']} - {progress['overall_progress']:.1f}%")
    
    # Create and run workflow
    workflow = ProjectWorkflow(
        request=request,
        on_progress=on_progress
    )
    
    print("Starting full-stack project development...")
    print("=" * 60)
    
    # Run analysis only for this example
    result = workflow.run_analysis_only()
    
    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print(result)


if __name__ == "__main__":
    main()


EOF
# ============================================================