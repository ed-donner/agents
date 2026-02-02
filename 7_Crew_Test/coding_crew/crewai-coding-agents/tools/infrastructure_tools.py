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
