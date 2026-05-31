# Multi-Model Evaluator (2_lab2.py)

A Python script that evaluates and compares the performance of multiple AI language models by generating a challenging question, collecting responses from various providers, and ranking them using a judge model.

## Overview

This script performs the following steps:
1. **Question Generation**: Uses an OpenAI model to generate a challenging, real-world question
2. **Multi-Model Evaluation**: Sends the question to multiple AI models from different providers
3. **Response Collection**: Gathers and displays all responses with timing information
4. **Judging**: Uses a judge model to rank the responses based on correctness, depth, clarity, and helpfulness

## Prerequisites

- Python 3.7 or higher
- API keys for the AI providers you want to test (at minimum, OpenAI API key is required)

## Installation

1. **Install required Python packages:**

```bash
pip install openai anthropic python-dotenv
```

Or if you have a requirements file:

```bash
pip install -r requirements.txt
```

Required packages:
- `openai` - For OpenAI API calls and OpenAI-compatible APIs
- `anthropic` - For Anthropic/Claude API calls
- `python-dotenv` - For loading environment variables from `.env` file

## Environment Setup

1. **Create a `.env` file** in the same directory as `2_lab2.py` (or in the project root)

2. **Add your API keys** to the `.env` file:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional (add only if you want to test these providers)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
GROQ_API_KEY=your_groq_api_key_here
OLLAMA_BASE_URL=http://localhost:11434
```

**Note:** Only `OPENAI_API_KEY` is strictly required. The script will skip providers for which API keys are missing.

## Supported Models

The script is configured to test the following models (you can modify the `COMPETITORS` list in the script):

- **Claude Sonnet 4.5** (Anthropic) - Requires `ANTHROPIC_API_KEY`
- **GPT-5 Nano** (OpenAI) - Requires `OPENAI_API_KEY`
- **Gemini 2.0 Flash** (Google) - Requires `GOOGLE_API_KEY`
- **Llama 3.2** (via Ollama) - Requires `OLLAMA_BASE_URL` pointing to local Ollama instance
- **DeepSeek Chat** (DeepSeek) - Requires `DEEPSEEK_API_KEY`
- **GPT-OSS-120B** (via Groq) - Requires `GROQ_API_KEY`

## Usage

1. **Ensure your `.env` file is set up** with at least the `OPENAI_API_KEY`

2. **Run the script:**

```bash
python 2_lab2.py
```

The script will:
- Generate a challenging question
- Display the question
- Query each configured model (skipping those without API keys)
- Display each response with timing information
- Use a judge model to rank all responses
- Display the final rankings with scores and justifications

## Customization

You can customize the script by modifying:

- **`QUESTION_GENERATOR_MODEL`** (line 167): The model used to generate questions (default: `"gpt-4.1-mini"`)
- **`JUDGE_MODEL`** (line 319): The model used to judge responses (default: `"o3-mini"`)
- **`COMPETITORS`** list (lines 196-227): Add, remove, or modify the models to test

## Notes

- Models without corresponding API keys will be skipped gracefully
- The script uses OpenAI's Responses API for some models and standard Chat Completions API for others
- Ollama requires a local instance running and accessible at the `OLLAMA_BASE_URL`
- Response times are measured and displayed for each model
- The judge model outputs JSON-formatted rankings with scores (0-10) and justifications

## Troubleshooting

- **"OPENAI_API_KEY is required"**: Make sure your `.env` file contains a valid OpenAI API key
- **"ANTHROPIC_API_KEY missing"**: This is expected if you don't have an Anthropic key. The script will skip Anthropic models
- **Ollama connection errors**: Ensure Ollama is running locally and accessible at the configured `OLLAMA_BASE_URL`
- **Import errors**: Make sure all required packages are installed: `pip install openai anthropic python-dotenv`

