# Quickstart Guide

This guide will help you quickly set up and test the Transcript Summarizer application.

## Prerequisites

Before starting, make sure you have:
- Python 3.8 or higher
- Docker and Docker Compose (optional, for containerized setup)
- Git (optional, for cloning)

## Option 1: Quick Development Setup (Recommended for Testing)

### Step 1: Set Up Ollama

1. **Install Ollama** (if not already installed):
   - Windows: Download from https://ollama.ai/download/windows
   - macOS: `brew install ollama`
   - Linux: `curl -fsSL https://ollama.ai/install.sh | sh`

2. **Start Ollama and pull LLaMA3**:
   ```bash
   # Start Ollama service
   ollama serve
   
   # In a new terminal, pull the model
   ollama pull llama3.1:8b
   ```

### Step 2: Set Up the Application

1. **Navigate to the project directory**:
   ```bash
   cd c:\Workspace\Personal\transcripter
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file** (optional):
   ```bash
   copy .env.example .env
   # Edit .env if you need to change any settings
   ```

### Step 3: Test the Application

1. **Run the application**:
   ```bash
   python main.py
   ```

2. **Access the web interface**:
   - Open your browser and go to: http://localhost:7860
   - You should see the Transcript Summarizer interface

3. **Test with sample data**:
   - Create a test VTT file or use the sample below
   - Upload it through the web interface
   - Click "Generate Summary"

## Option 2: Docker Setup (Production-Ready)

### Step 1: Using Docker Compose

1. **Start all services**:
   ```bash
   cd c:\Workspace\Personal\transcripter
   docker-compose -f docker/docker-compose.yml up --build
   ```

2. **Wait for initialization**:
   - The first run will take 5-10 minutes to download the LLaMA3 model
   - Watch the logs for "Model initialization complete!"

3. **Access the application**:
   - Web interface: http://localhost:7860
   - Ollama API: http://localhost:11434

### Step 2: Stop the Services

```bash
docker-compose -f docker/docker-compose.yml down
```

## Sample VTT File for Testing

Create a file called `sample.vtt` with this content:

```vtt
WEBVTT

00:00:00.000 --> 00:00:05.000
Welcome everyone to today's presentation on artificial intelligence and machine learning.

00:00:05.000 --> 00:00:12.000
We'll be covering the latest developments in natural language processing and how they're transforming various industries.

00:00:12.000 --> 00:00:18.000
First, let's discuss the evolution of large language models over the past few years.

00:00:18.000 --> 00:00:25.000
These models have grown significantly in size and capability, from GPT-1 with 117 million parameters to models with hundreds of billions.

00:00:25.000 --> 00:00:32.000
The key breakthrough was the transformer architecture, which enabled better handling of long-range dependencies in text.

00:00:32.000 --> 00:00:38.000
Now, let's look at some practical applications in business and education.

00:00:38.000 --> 00:00:45.000
Companies are using these models for customer service, content generation, and automated report writing.

00:00:45.000 --> 00:00:52.000
In education, they're being used for personalized tutoring and automatic essay grading.

00:00:52.000 --> 00:00:58.000
However, we must also consider the challenges and limitations of these technologies.

00:00:58.000 --> 00:01:05.000
Issues include bias in training data, hallucination of facts, and the environmental cost of training large models.

00:01:05.000 --> 00:01:10.000
Thank you for your attention. Let's now open the floor for questions.
```

## Testing Steps

1. **Health Check**:
   - Click "Check System Health" in the web interface
   - Verify that both Ollama connection and model availability show ✅

2. **Upload and Summarize**:
   - Upload the sample VTT file
   - Adjust settings if desired (chunk size, temperature)
   - Click "Generate Summary"

3. **Review Results**:
   - Check the generated summary in the "Summary" tab
   - Review processing statistics in the "Statistics" tab


