#!/bin/bash

# Lab2 Setup and Run Script
# ========================
# This script sets up and runs the complete Lab2 workflow from the agents repository

set -e  # Exit on error

echo "🚀 Setting up Lab2 Multi-Model Comparison Environment"
echo "====================================================="

# Navigate to the agents directory
cd "$(dirname "$0")"

echo "📁 Working directory: $(pwd)"

# Check if .env file exists, if not, explain setup
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating template..."
    cat > .env << 'EOF'
# AI API Keys for Lab2
# Replace the placeholder values with your actual API keys

# Required for OpenAI models (GPT-4o-mini, o3-mini)
OPENAI_API_KEY=your_openai_api_key_here

# Optional API keys - lab2 will skip these models if keys are not provided
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here  
GROQ_API_KEY=your_groq_api_key_here

# For testing purposes, you can set these to dummy values to see error handling
# OPENAI_API_KEY=sk-test-dummy-key
# ANTHROPIC_API_KEY=sk-ant-dummy-key
EOF
    echo "✅ Created .env template"
fi

# Check Python version
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python version: $python_version"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install core dependencies for lab2
echo "📦 Installing core dependencies..."
pip install python-dotenv openai anthropic ipython > /dev/null 2>&1
echo "✅ Core dependencies installed"

# Check for Ollama
echo "🤖 Checking for Ollama..."
if command -v ollama >/dev/null 2>&1; then
    echo "✅ Ollama found"
    if pgrep -x ollama >/dev/null; then
        echo "✅ Ollama is running"
    else
        echo "⚠️  Ollama is installed but not running"
        echo "   To start Ollama: ollama serve"
        echo "   To install llama3.2: ollama pull llama3.2"
    fi
else
    echo "ℹ️  Ollama not found (optional for local models)"
    echo "   Install from: https://ollama.com"
fi

# Make run script executable
chmod +x run_lab2.py

echo ""
echo "🎯 SETUP COMPLETE!"
echo "=================="
echo ""
echo "📋 Next steps:"
echo "1. 📝 Edit .env file with your actual API keys (optional but recommended)"
echo "2. 🚀 Run lab2: python run_lab2.py"
echo ""
echo "💡 API Key Setup:"
echo "   • OpenAI: https://platform.openai.com/api-keys"
echo "   • Anthropic: https://console.anthropic.com/"
echo "   • Google: https://aistudio.google.com/"
echo "   • DeepSeek: https://platform.deepseek.com/"
echo "   • Groq: https://console.groq.com/"
echo ""
echo "🆓 Free Alternative:"
echo "   Install Ollama for local models (no API keys needed)"
echo "   1. Install: curl -fsSL https://ollama.com/install.sh | sh"
echo "   2. Start: ollama serve"
echo "   3. Install model: ollama pull llama3.2"
echo ""

# Ask if user wants to run immediately
read -p "🚀 Run Lab2 now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🏃 Running Lab2..."
    python run_lab2.py
else
    echo "👋 Setup complete. Run 'python run_lab2.py' when ready!"
fi