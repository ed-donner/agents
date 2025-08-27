#!/bin/bash

echo "🐳 Finance Copilot Docker Setup"
echo "================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create one with your API keys."
    echo "💡 You can copy from env_example.txt"
    exit 1
fi

echo "✅ Docker is running"
echo "✅ .env file found"

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t finance-copilot .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

echo "✅ Docker image built successfully"

# Run the container
echo "🚀 Starting Finance Copilot container..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Failed to start container"
    exit 1
fi

echo "✅ Container started successfully"
echo ""
echo "🌐 Finance Copilot is now running at: http://localhost:7860"
echo "🔑 Login: admin / finance123"
echo ""
echo "📊 Container logs: docker-compose logs -f"
echo "🛑 Stop container: docker-compose down"
echo "🔍 Check status: docker-compose ps"
