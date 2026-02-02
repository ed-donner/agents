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


