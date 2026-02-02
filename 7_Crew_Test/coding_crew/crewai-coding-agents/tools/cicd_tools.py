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
