#!/usr/bin/env python
import sys
import warnings
import os
from datetime import datetime
import asyncio

from advanced_engineering_team.crew import (
    build_breakdown_crew,
    build_feature_engineering_crew,
    build_integration_crew,
)

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

requirements = """
A motor insurance claims platform that manages products, policies, customers, and claims. 

The system should include the following modules:

1. Products & Claim Computation:
   - Allow admin users to create, update, and manage insurance products.
   - Define claim computation rates, coverage options, and premium calculation logic.
   - Allow querying of products and associated rates.

2. Customers & Policy Management:
   - Register new customers with personal details.
   - Create, update, and manage customer insurance policies.
   - Associate customers with one or more insurance products.
   - Track policy start and end dates, coverage details, and premiums.

3. Claims Management:
   - Receive new claim submissions, including customer, policy, and incident details.
   - Automatically compute claim amounts based on the associated product rates.
   - Allow approvals, rejections, and comments by claims adjusters.
   - Process payments for approved claims.
   - Maintain a complete audit trail of claims and actions.

Additional requirements:
- Validate all inputs and enforce business rules (e.g., prevent claim submission for inactive policies).
- Provide reporting functions for claims status, customer policy summary, and product performance.
- Integrate with external functions such as `get_customer_credit_score(customer_id)` or `get_claim_history(customer_id)` if needed.
- Ensure modularity: each module should be implementable as a separate Python class and module but ready to integrate into a unified system.
- Include simple test hooks so that unit tests can be written for all classes and methods.
- The frontend should provide a minimal Gradio interface for demonstration, allowing:
  - Admin to add/update products and rates.
  - Admin to register customers and assign policies.
  - Customers to submit claims and see claim status.
"""


def run():
    """
    Run the advanced engineering team crew.
    """
    breakdown_result = build_breakdown_crew().kickoff(inputs={"requirements": requirements})
    print("breakdown_result:", breakdown_result)
    parsed = breakdown_result.pydantic
    modules_list = [feature.dict() for feature in parsed.features]

    feature_crew = build_feature_engineering_crew()
    feature_results = feature_crew.kickoff_for_each(inputs=modules_list)
    print("Features", feature_results)

    module_names = [feature["module_name"] for feature in modules_list]
    integration_result = build_integration_crew().kickoff(inputs={"modules": module_names})
    print("Integration complete:", integration_result)

if __name__ == "__main__":
    run()