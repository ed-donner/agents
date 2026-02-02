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
