# AWS Lambda + API Gateway deployment for the enterprise agent.
# Requires: terraform >= 1.5, aws provider ~> 5.0
# Usage:
#   terraform init
#   terraform apply -var="openai_api_key=sk-..."

terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region"     { default = "us-east-1" }
variable "openai_api_key" { sensitive = true }
variable "global_budget"  { default = "50.0" }
variable "per_user_budget" { default = "2.0" }


# --- ECR repository for the Docker image ---
resource "aws_ecr_repository" "agent" {
  name                 = "enterprise-agent"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration { scan_on_push = true }
}


# --- Secrets Manager for API key ---
resource "aws_secretsmanager_secret" "openai_key" {
  name = "enterprise-agent/openai-api-key"
}

resource "aws_secretsmanager_secret_version" "openai_key" {
  secret_id     = aws_secretsmanager_secret.openai_key.id
  secret_string = var.openai_api_key
}


# --- IAM Role for Lambda ---
resource "aws_iam_role" "lambda_role" {
  name = "enterprise-agent-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "secrets_access" {
  role = aws_iam_role.lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = aws_secretsmanager_secret.openai_key.arn
    }]
  })
}


# --- Lambda function (container image) ---
resource "aws_lambda_function" "agent" {
  function_name = "enterprise-agent"
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.agent.repository_url}:latest"
  timeout       = 60
  memory_size   = 512

  environment {
    variables = {
      OPENAI_API_KEY_SECRET = aws_secretsmanager_secret.openai_key.name
      GLOBAL_BUDGET_USD     = var.global_budget
      PER_USER_BUDGET_USD   = var.per_user_budget
      AUDIT_LOG_FILE        = "/tmp/audit.jsonl"
    }
  }
}


# --- API Gateway (HTTP API — cheaper than REST API) ---
resource "aws_apigatewayv2_api" "agent_api" {
  name          = "enterprise-agent-api"
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["POST", "GET"]
    allow_headers = ["*"]
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id             = aws_apigatewayv2_api.agent_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.agent.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "chat" {
  api_id    = aws_apigatewayv2_api.agent_api.id
  route_key = "POST /chat"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.agent_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.agent.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.agent_api.execution_arn}/*/*"
}


# --- Outputs ---
output "api_url" {
  value       = aws_apigatewayv2_stage.default.invoke_url
  description = "POST /chat to this URL"
}

output "ecr_repo" {
  value = aws_ecr_repository.agent.repository_url
}
