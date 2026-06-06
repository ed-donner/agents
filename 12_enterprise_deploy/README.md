# Week 12: Enterprise Deployment

## What you'll build
A production-ready agent deployment: Docker container, cost budget middleware, PII scrubber, audit logger, and IaC templates for AWS Lambda, GCP Cloud Run, and Azure Container Apps.

## Learning objectives
- Containerise an agent with Docker for cloud deployment
- Implement a BudgetMiddleware that hard-stops spending above a threshold
- Scrub PII from inputs/outputs before they reach the LLM
- Write an immutable audit log suitable for compliance review
- Deploy to AWS Lambda (serverless), GCP Cloud Run, and Azure Container Apps
- Implement a circuit breaker so a failing downstream model doesn't take your service down

## Labs

| Lab | Topic | Key pattern |
|-----|-------|-------------|
| `1_lab1.ipynb` | Docker + FastAPI | Containerise an agent, expose via REST API |
| `2_lab2.ipynb` | Cost controls | BudgetMiddleware, per-user quotas, model routing |
| `3_lab3.ipynb` | Compliance (PII + audit) | Scrubber, structured audit log, retention policy |
| `4_lab4.ipynb` | Cloud IaC | Terraform snippets for AWS/GCP/Azure deployments |

## Files
- `agent_server.py` — FastAPI-wrapped agent (the deployable)
- `middleware.py` — BudgetMiddleware, PII scrubber, audit logger
- `circuit_breaker.py` — Fault tolerance pattern for LLM API calls
- `Dockerfile` — Multi-stage production Docker build
- `deploy/` — IaC templates for each cloud

## Cost estimate
Cloud deployment costs (beyond API costs):
- AWS Lambda: ~$0.00 for < 1M requests/month (free tier)
- GCP Cloud Run: ~$0.00 for < 2M requests/month (free tier)
- Azure Container Apps: ~$0.00 for < 180K vCPU-seconds/month (free tier)
