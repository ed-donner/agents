# Lab2 Multi-Model Comparison - Complete Guide

This guide provides everything you need to run the entire **Lab2** from the 1_foundations directory end-to-end.

## What is Lab2?

Lab2 demonstrates the **Multi-Model Comparison** pattern, a powerful agentic AI technique where:
1. **Multiple AI models** are tested with the same challenging question
2. **Responses are collected** from different providers (OpenAI, Anthropic, Google, etc.)
3. **A judge model** evaluates and ranks all responses
4. **Results are compared** to find the best-performing model

This pattern is widely used in production systems where accuracy and quality are critical.

## 🚀 Quick Start (Automated Setup)

The easiest way to run Lab2 is using our automated setup script:

```bash
# Navigate to your agents directory
cd /path/to/your/agents/repository

# Run the automated setup and execution script
./setup_and_run_lab2.sh
```

This script will:
- ✅ Create a Python virtual environment
- ✅ Install all required dependencies
- ✅ Create a `.env` template for API keys
- ✅ Check for Ollama (local models)
- ✅ Run the complete Lab2 workflow

## 📋 Manual Setup (Step by Step)

If you prefer manual setup or want to understand each step:

### 1. Environment Setup

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install python-dotenv openai anthropic ipython
```

### 2. API Keys Configuration

Create a `.env` file in the root directory:

```bash
# Required for best experience
OPENAI_API_KEY=your_actual_openai_api_key

# Optional - add any or all of these
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
GROQ_API_KEY=your_groq_api_key
```

**Where to get API keys:**
- 🔑 **OpenAI**: https://platform.openai.com/api-keys
- 🔑 **Anthropic**: https://console.anthropic.com/
- 🔑 **Google**: https://aistudio.google.com/
- 🔑 **DeepSeek**: https://platform.deepseek.com/
- 🔑 **Groq**: https://console.groq.com/

### 3. Optional: Local Models with Ollama

For free local models (no API keys needed):

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Install a model (in another terminal)
ollama pull llama3.2
```

### 4. Run Lab2

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Run the complete lab
python run_lab2.py
```

## 🎯 What You'll See

When you run Lab2, you'll see:

1. **🔍 API Key Check**: Which services are available
2. **❓ Question Generation**: AI generates a challenging question
3. **🤖 Model Testing**: Each available model answers the question
4. **⚖️ Response Judging**: A judge model ranks all responses
5. **🏆 Final Rankings**: See which model performed best
6. **📊 Complete Results**: Full responses and analysis

## 💡 Understanding the Output

### Successful Run Example:
```
============================================================
 LAB2: MULTI-MODEL COMPARISON
============================================================

============================================================
 CHECKING API KEYS
============================================================
✓ OpenAI API Key exists and begins sk-proj-A...
✓ Anthropic API Key exists and begins sk-ant-...
✗ Google API Key not set (optional)

============================================================
 GENERATING CHALLENGING QUESTION
============================================================
🤖 Asking GPT-4o-mini to generate a challenging question...
✓ Generated question: How would you design a system that balances...

============================================================
 TESTING MODELS
============================================================
--- Testing GPT-4o-mini ---
✓ GPT-4o-mini responded successfully
--- Testing Claude-3.5-Sonnet ---
✓ Claude-3.5-Sonnet responded successfully

============================================================
 JUDGING RESPONSES
============================================================
⚖️ Asking o3-mini to judge the responses...

🏆 Rank 1: Claude-3.5-Sonnet
🏆 Rank 2: GPT-4o-mini
```

### No API Keys Example:
```
⚠️ OpenAI API key required for question generation. Using fallback question.
✗ All models failed due to missing API keys

💡 To get started:
   1. Edit the .env file with your actual API keys
   2. Or install and run Ollama with: ollama serve && ollama pull llama3.2
```

## 🔧 Troubleshooting

### Common Issues:

**"No models were able to respond"**
- Check your `.env` file has valid API keys
- Ensure API keys don't have typos
- Verify you have credits/quota remaining

**"Ollama connection error"**
- Start Ollama: `ollama serve`
- Install a model: `ollama pull llama3.2`
- Check if running on port 11434

**"Module not found" errors**
- Activate virtual environment: `source .venv/bin/activate`
- Install dependencies: `pip install python-dotenv openai anthropic`

**API rate limits or quota exceeded**
- Check your API provider's dashboard
- Use fewer models or smaller models
- Consider free alternatives like Ollama

## 🎓 Learning Objectives

After running Lab2, you'll understand:

1. **Multi-Model Comparison Pattern**: How to orchestrate multiple AI models
2. **API Integration**: Working with different AI provider APIs
3. **Response Evaluation**: Using AI judges to compare outputs
4. **Error Handling**: Graceful degradation when services are unavailable
5. **Production Patterns**: Techniques used in real-world AI systems

## 📁 Files Created

Running Lab2 creates these files:
- `.env` - Your API key configuration
- `.venv/` - Python virtual environment
- `run_lab2.py` - The executable Lab2 script

## 🚀 Next Steps

1. **Experiment**: Try different API keys and models
2. **Customize**: Modify the question generation prompt
3. **Extend**: Add new model providers or local models
4. **Compare**: Run multiple times to see consistency
5. **Apply**: Use this pattern in your own projects

## 💰 Cost Considerations

- **OpenAI**: ~$0.01-0.05 per run (depending on models and response length)
- **Anthropic**: ~$0.01-0.03 per run
- **Google/DeepSeek/Groq**: Usually cheaper or free tiers available
- **Ollama**: Completely free (uses local compute)

**Cost-Saving Tips:**
- Start with just one API key (OpenAI)
- Use Ollama for free local testing
- Monitor your API usage dashboards
- Use smaller/cheaper models for development

---

**🎉 Enjoy exploring the fascinating world of Multi-Model AI Comparison!**

For questions or issues, refer to the original course materials or reach out to the course community.