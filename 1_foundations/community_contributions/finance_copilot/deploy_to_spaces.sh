#!/bin/bash

# 🚀 Finance Copilot - Hugging Face Spaces Deployment Script
# This script automates the deployment process to Hugging Face Spaces

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SPACE_NAME="finance-copilot"
HF_USERNAME=""
REPO_URL=""

echo -e "${BLUE}🚀 Finance Copilot - Hugging Face Spaces Deployment${NC}"
echo "=================================================="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git is not installed. Please install git first.${NC}"
    exit 1
fi

# Check if user is logged into Hugging Face
if ! git config --global user.name &> /dev/null; then
    echo -e "${YELLOW}⚠️  Git user not configured. Please run:${NC}"
    echo "   git config --global user.name 'Your Name'"
    echo "   git config --global user.email 'your.email@example.com'"
    exit 1
fi

# Get Hugging Face username
echo -e "${BLUE}📝 Enter your Hugging Face username:${NC}"
read -p "Username: " HF_USERNAME

if [ -z "$HF_USERNAME" ]; then
    echo -e "${RED}❌ Username cannot be empty${NC}"
    exit 1
fi

# Set repository URL
REPO_URL="https://huggingface.co/spaces/${HF_USERNAME}/${SPACE_NAME}"

echo -e "${BLUE}🔍 Checking if space already exists...${NC}"

# Check if space exists
if curl -s -f "https://huggingface.co/spaces/${HF_USERNAME}/${SPACE_NAME}" > /dev/null; then
    echo -e "${YELLOW}⚠️  Space already exists. Updating existing space...${NC}"
    
    # Clone existing space
    if [ -d "$SPACE_NAME" ]; then
        echo -e "${YELLOW}⚠️  Directory $SPACE_NAME already exists. Removing...${NC}"
        rm -rf "$SPACE_NAME"
    fi
    
    echo -e "${BLUE}📥 Cloning existing space...${NC}"
    git clone "$REPO_URL" "$SPACE_NAME"
    cd "$SPACE_NAME"
    
else
    echo -e "${GREEN}✅ Creating new space...${NC}"
    
    # Create directory
    mkdir -p "$SPACE_NAME"
    cd "$SPACE_NAME"
    
    # Initialize git repository
    git init
    git remote add origin "$REPO_URL"
    
    echo -e "${BLUE}📝 Creating README.md for new space...${NC}"
    cat > README.md << 'EOF'
# Finance Copilot

AI-powered financial analysis platform with real-time market data, portfolio management, and Monte Carlo simulations.

## Features

- 🤖 AI-powered financial assistant
- 📊 Real-time market data
- 💼 Portfolio management
- 🔮 Monte Carlo simulations
- 📈 Technical analysis
- 🔔 Price alerts

## Usage

1. Enter your credentials (admin/finance123)
2. Ask questions about stocks, crypto, or portfolios
3. Get AI-powered insights and analysis

## Example Queries

- "What's the current price of AAPL?"
- "What's the outlook for Bitcoin in 2025?"
- "Show me MSFT fundamentals"
- "Run a Monte Carlo simulation for my portfolio"

---

*Powered by OpenAI GPT-4 and real-time financial data*
EOF
fi

# Copy project files
echo -e "${BLUE}📁 Copying project files...${NC}"

# Copy essential files from parent directory
cp ../app.py .
cp ../ai_agent.py .
cp ../market_data.py .
cp ../analysis_tool.py .
cp ../database.py .
cp ../notification_system.py .
cp ../config.py .
cp ../requirements.txt .

# Copy documentation
cp ../README.md ./README_MAIN.md
cp ../README_Spaces.md ./README.md

# Create .gitignore
echo -e "${BLUE}📝 Creating .gitignore...${NC}"
cat > .gitignore << 'EOF'
# Environment variables
.env
.env.local

# Database files
*.db
*.sqlite
*.sqlite3

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp
EOF

# Check if files were copied successfully
if [ ! -f "app.py" ]; then
    echo -e "${RED}❌ Failed to copy app.py. Make sure you're running this script from the finance_copilot directory.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Files copied successfully${NC}"

# Add files to git
echo -e "${BLUE}📝 Adding files to git...${NC}"
git add .

# Commit changes
echo -e "${BLUE}💾 Committing changes...${NC}"
if git diff --cached --quiet; then
    echo -e "${YELLOW}⚠️  No changes to commit${NC}"
else
    git commit -m "Deploy Finance Copilot to Hugging Face Spaces"
fi

# Push to Hugging Face
echo -e "${BLUE}🚀 Pushing to Hugging Face Spaces...${NC}"
if git push -u origin main 2>/dev/null || git push -u origin master 2>/dev/null; then
    echo -e "${GREEN}✅ Successfully pushed to Hugging Face Spaces!${NC}"
else
    echo -e "${YELLOW}⚠️  Push failed. This might be expected for new spaces.${NC}"
    echo -e "${BLUE}💡 You may need to create the space manually first:${NC}"
    echo "   1. Go to https://huggingface.co/spaces"
    echo "   2. Click 'Create new Space'"
    echo "   3. Choose 'Gradio' as SDK"
    echo "   4. Name it: $SPACE_NAME"
    echo "   5. Then run this script again"
fi

echo ""
echo -e "${GREEN}🎉 Deployment script completed!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Go to: https://huggingface.co/spaces/${HF_USERNAME}/${SPACE_NAME}"
echo "2. Wait for the build to complete"
echo "3. Add your API keys in Space Settings > Repository secrets:"
echo "   - OPENAI_API_KEY"
echo "   - ALPHA_VANTAGE_API_KEY"
echo "4. Test your app!"
echo ""
echo -e "${BLUE}🔗 Your app will be available at:${NC}"
echo "   https://huggingface.co/spaces/${HF_USERNAME}/${SPACE_NAME}"
echo ""
echo -e "${GREEN}🚀 Happy deploying!${NC}"


