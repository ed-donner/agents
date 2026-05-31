# 🧰 Skills Toolbox - AI Research & Coding Assistant

Skills Toolbox is an intelligent assistant application that leverages LangGraph to provide research and coding capabilities through AI-powered agents. The system intelligently routes user requests based on intent classification and provides comprehensive research reports or code implementations.

## 🚀 Key Features

### 🔍 Research Assistant
- **Intelligent Search Query Generation**: Automatically generates relevant search queries based on the user's topic
- **Query Evaluation**: Evaluates generated queries based on relevance, actionability, and specificity
- **Human Approval Workflow**: Includes user approval step for search queries before execution
- **Comprehensive Report Generation**: Creates detailed research reports in both Markdown and HTML formats
- **Source Integration**: Aggregates and extracts content from multiple sources

### 💻 Coding Assistant
- **Task Planning**: Breaks down coding tasks into structured plans
- **Implementation Assistance**: Helps with code generation and implementation
- **Structured Approach**: Plans and executes coding tasks systematically

### 🧠 AI-Powered Architecture
- **LangGraph Integration**: Built with LangGraph for stateful AI workflows
- **Intent Classification**: Smart routing between research and coding tasks
- **Multi-Modal Output**: Supports various output formats and content types
- **State Management**: Maintains conversation and research state throughout the session

## 🛠️ Technologies Used

- **LangGraph**: For building stateful AI agent workflows
- **LangChain**: For LLM integration and management
- **Gradio**: For the web UI interface
- **Tavily**: For search and content extraction
- **Pydantic**: For data validation and structured outputs
- **OpenAI API**: For LLM interactions (with support for various providers)
- **WeasyPrint**: For HTML report generation

## 📋 Requirements

- Python 3.8+
- Tavily API key for search functionality
- LLM API key (Cerebras, Ollama, or compatible provider)

## 🚀 Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd apps/Skills Toolbox
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Open your browser** to `http://localhost:7860` to access the interface

## 🎯 Usage

1. **Enter a topic** in the text box (e.g., "AI in Healthcare", "Blockchain Development")
2. **The system will classify** the intent as research or coding
3. **For research**: The system will generate search queries, seek approval (if needed), and produce a comprehensive report
4. **For coding**: The system will plan and implement the requested task

## 🏗️ Architecture

The application follows a multi-agent architecture:

- **Main Workflow**: Orchestrates between research and coding agents based on intent classification
- **Research Agent**: Handles the research workflow with query generation, evaluation, and report creation
- **Coding Agent**: Plans and implements coding tasks
- **State Management**: Maintains context throughout the conversation using LangGraph's state management

## 📊 Workflow Details

### Research Workflow
1. Topic classification and intent detection
2. Generate multiple search queries
3. Evaluate queries for relevance, actionability, and specificity
4. User approval of selected queries
5. Perform searches and aggregate results
6. Extract content from relevant sources
7. Generate comprehensive research report

### Coding Workflow
1. Task analysis and understanding
2. Plan the implementation in structured steps
3. Execute the implementation plan

## 🔐 Environment Variables

Create a `.env` file with the following variables:

```env
TAVILY_API_KEY=your_tavily_api_key
CEREBRAS_API_KEY=your_cerebras_api_key  # or other provider
OLLAMA_API_KEY=your_ollama_api_key      # optional, for local models
```

## 🤖 Supported LLM Providers

The system supports multiple LLM providers:
- Cerebras (default)
- Ollama (for local models)
- OpenAI-compatible APIs

## 📈 Features Highlight

- **Interactive UI**: Gradio-based interface with workflow visualization
- **Visual Workflow**: Shows the current workflow graph in real-time
- **Interrupt Mechanism**: Allows human interaction at key decision points
- **Flexible Architecture**: Easy to extend with additional agents and capabilities
- **Multiple Output Formats**: Supports markdown, HTML, and planned PDF exports
- **Smart Query Selection**: Uses scoring to select the best search queries

## 🧪 Development

To extend the functionality:

1. Add new agent implementations in the `agents/` directory
2. Define new state schemas in `schemas.py`
3. Update the main workflow in `app.py` to incorporate new capabilities

## 📚 Examples

The system includes several example topics for quick testing:
- "Write a Go backend program that calculates simple and compound interests"
- "FinTech Startups In Ghana"
- "Blockchain in Healthcare"
- "AI Replacing The Workforce"

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

[Add your license information here]