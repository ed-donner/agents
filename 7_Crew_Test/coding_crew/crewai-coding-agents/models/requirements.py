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
