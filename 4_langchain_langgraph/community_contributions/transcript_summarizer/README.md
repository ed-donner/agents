# Transcript Summarizer using Langgraph and Llama3

A scalable transcript summarizer application built with Python, Ollama API, LLaMA3, LangChain, and Gradio. This application can handle long transcriptions that exceed the context window by chunking and processing them efficiently.

## Features

- 📄 Upload .vtt transcript files
- 🤖 AI-powered summarization using LLaMA3 via Ollama
- 🔄 Handles long transcripts with intelligent chunking
- 🎯 Multi-level summarization (chunk-level and final summary)
- 🐳 Fully containerized with Docker
- 🎨 Modern Gradio web interface
- 🔧 Modular and extensible architecture
- ⚙️ Configurable via environment variables
- 📝 Configurable logging levels for debugging

## Architecture

```
transcripter/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── summarizer.py      # Main summarization logic
│   │   ├── chunker.py         # Text chunking strategies
│   │   └── vtt_parser.py      # VTT file parsing
│   ├── services/
│   │   ├── __init__.py
│   │   └── ollama_service.py  # Ollama API integration
│   ├   └── gemini_service.py  # Gemini API integration (if needed)
│   ├── tests/
│   │   ├── __init__.py
|   |   
│   ├── ui/
│   │   ├── __init__.py
│   │   └── gradio_app.py      # Gradio interface
│   └── utils/
│       ├── __init__.py
│       └── config.py          # Configuration management
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── requirements.txt
├── main.py
└── setup.py
```

## Quick Start

### Prerequisites

- Python 3.8+ (tested with Python 3.13)
- Docker & Docker Compose (for containerized deployment)
- Ollama running locally with LLaMA3 model

### Setup Development Environment

#### Option 1: Automated Setup (Recommended)

1. **Clone and navigate to the project:**
   ```bash
   cd c:\Workspace\Personal\transcripter
   ```

2. **Run the automated setup script:**
   ```bash
   setup.bat
   ```
   
   This script will:
   - Create a virtual environment
   - Install all dependencies
   - Check Ollama connectivity
   - Provide setup status

#### Option 2: Manual Setup

1. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

2. **Upgrade pip:**
   ```bash
   python -m pip install --upgrade pip
   ```

3. **Install dependencies (choose one):**
   
   **Full Installation (Recommended):**
   ```bash
   pip install -r requirements.txt
   ```
   
   **Minimal Installation (if you face dependency issues):**
   ```bash
   pip install -r requirements-minimal.txt
   ```

4. **Ensure Ollama is running with LLaMA3:**
   ```bash
   ollama serve
   ollama pull llama3.1:8b
   ```

5. **Run the application:**
   ```bash
   python main.py
   ```

6. **Access the web interface:**
   Open http://localhost:7860 in your browser

### Using Docker

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose -f docker/docker-compose.yml up --build
   ```

2. **Access the application:**
   Open http://localhost:7860 in your browser

## Usage

1. **Upload VTT File:** Click on the file upload area and select your .vtt transcript file
2. **Configure Settings:** Adjust chunk size and overlap settings if needed
3. **Generate Summary:** Click "Generate Summary" to process the transcript
4. **Review Results:** View the generated summary and processing statistics

## Configuration

The application can be configured through environment variables or by creating a `.env` file in the project root:

- `OLLAMA_BASE_URL`: Ollama API base URL (default: http://localhost:11434)
- `MODEL_NAME`: LLaMA model name (default: llama3.1:8b)
- `CHUNK_SIZE`: Maximum tokens per chunk (default: 2000)
- `CHUNK_OVERLAP`: Token overlap between chunks (default: 200)
- `GRADIO_PORT`: Gradio server port (default: 7860)
- `MAX_CONCURRENT_REQUESTS`: Maximum concurrent API requests (default: 3)
- `REQUEST_TIMEOUT`: Request timeout in seconds (default: 300)
- `TEMPERATURE`: Temperature for text generation (default: 0.3)
- `LOG_LEVEL`: Logging level - DEBUG, INFO, WARNING, ERROR, or CRITICAL (default: INFO)

### Environment File Setup

Copy the example environment file and modify as needed:
```bash
cp .env.example .env
```

Then edit `.env` with your preferred settings:
```env
# Example .env configuration
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=llama3.1:8b
CHUNK_SIZE=2000
CHUNK_OVERLAP=200
TEMPERATURE=0.3
GRADIO_PORT=7860
MAX_CONCURRENT_REQUESTS=3
REQUEST_TIMEOUT=300
LOG_LEVEL=INFO
```

## Development

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Test specific modules
python -m pytest tests/test_config.py -v        # Test configuration loading
python -m pytest tests/test_chunker.py -v       # Test text chunking
python -m pytest tests/test_vtt_parser.py -v    # Test VTT parsing
python -m pytest tests/test_ollama_service.py -v # Test Ollama integration
```

### Testing Configuration
To verify your environment configuration is working correctly:
```bash
python -c "from src.utils.config import Config; c = Config(); print(f'Loaded config: {c.dict()}')"
```

### Code Formatting
```bash
black src/
isort src/
```

### Type Checking
```bash
mypy src/
```

## Troubleshooting

### Common Issues

#### 1. Package Installation Failures
**Problem:** NumPy or other packages fail to compile on Windows
**Solution:** 
- Use the automated setup script (`setup.bat`) which handles this automatically
- Or try the minimal requirements: `pip install -r requirements-minimal.txt`
- Ensure you have the latest pip: `python -m pip install --upgrade pip`

#### 2. Ollama Connection Issues
**Problem:** "❌ Ollama connection: FAILED"
**Solution:**
- Ensure Ollama is running: `ollama serve`
- Check if the model is available: `ollama list`
- Pull the model if missing: `ollama pull llama3.1:8b`
- Verify the URL in your .env file: `OLLAMA_BASE_URL=http://localhost:11434`

#### 3. LangGraph Import Errors
**Problem:** ImportError related to LangGraph
**Solution:**
- Use the exact versions in requirements.txt
- Reinstall: `pip uninstall langgraph langchain -y && pip install -r requirements.txt`

#### 4. Gradio Interface Not Loading
**Problem:** Web interface doesn't load
**Solution:**
- Check if port 7860 is available
- Try a different port: set `GRADIO_PORT=7861` in your .env file
- Check firewall settings

#### 5. VTT File Processing Errors
**Problem:** VTT files not parsing correctly
**Solution:**
- Ensure your VTT file follows the WebVTT standard
- Check the sample file in `examples/sample_transcript.vtt`
- Verify file encoding is UTF-8

#### 6. Debugging and Logging Issues
**Problem:** Need more detailed logs for troubleshooting
**Solution:**
- Set `LOG_LEVEL=DEBUG` in your .env file for detailed logging
- Available log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Check application logs for specific error messages
- Use `LOG_LEVEL=ERROR` to reduce log verbosity in production

### Getting Help
- Check the system health in the web interface
- Review logs for detailed error messages (set LOG_LEVEL=DEBUG for more details)
- Ensure all dependencies are correctly installed
- Verify Ollama is running and accessible
- Test your configuration: `python tests/test_config.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License
