# 🎯 Interview Prep Agent

An AI-powered interview preparation assistant that helps you prepare for job interviews with personalized guides, company research, and YouTube video recommendations.


## ✨ Features

- **🏢 Company Research**: Uses AI-powered web search to find and summarize company information
- **📝 Custom Prep Guides**: Generates tailored interview questions and answer tips
- **📺 YouTube Integration**: Finds relevant interview preparation videos
- **🔄 Iterative Refinement**: Refine your guide up to 3 times with custom requests
- **💬 Conversational Interface**: Natural chat-based interaction via Gradio

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Groq API key (for LLM)
- Tavily API key (for web search)
- YouTube API key (optional, for video search)

### Installation

1. **Clone the repository**
   ```bash
   cd interview_prep_agent
   ```

2. **Install dependencies**
   ```bash
   uv sync
   # or: pip install -e .
   ```

3. **Set up environment variables**
   
   Create a `.env` file or export environment variables:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   YOUTUBE_API_KEY=your_youtube_api_key_here  # Optional
   ```
   
   **Get API Keys:**
   - **Groq**: Sign up at [console.groq.com](https://console.groq.com)
   - **Tavily**: Sign up at [tavily.com](https://tavily.com) (free tier available)
   - **YouTube**: Get from [Google Cloud Console](https://console.cloud.google.com)

### Running the Application

**New modular structure:**
```bash
python main.py
```

**Original monolithic file:**
```bash
python interview_prep.py
```

The web interface will open at `http://localhost:7860`

## 💡 Usage

1. **Start the conversation**: Type "hi" or "hello"
2. **Provide company name**: e.g., "Google"
3. **Specify role**: e.g., "Software Engineer"
4. **Review the guide**: The agent will research and generate a comprehensive prep guide
5. **Refine as needed**:
   - Request more questions
   - Ask for YouTube videos
   - Adjust specific details
6. **Finish**: Say "looks good" when satisfied

### Example Conversation

```
User: hi
Agent: Hi! What company are you interviewing with?

User: Google
Agent: Great! What role are you applying for?

User: Software Engineer
Agent: Perfect! Let me research Google and create your interview prep guide...

[Guide appears]

User: Can you add more behavioral questions?
Agent: ✅ Updated!

User: Show me YouTube videos
Agent: 📺 Here are helpful YouTube videos for Google Software Engineer interviews...

User: looks good
Agent: ✅ You're all set! Good luck with your interview! 🚀
```

## 🔧 Configuration

Edit `src/config.py` to customize:

- **LLM settings**: Model, temperature
- **Scraping**: Timeout, max characters
- **YouTube**: Max results
- **Refinements**: Maximum iterations (default: 3)
- **UI**: Title, placeholder text, height

## 📦 Key Dependencies

- **LangGraph**: Graph-based workflow orchestration
- **LangChain**: LLM framework
- **Groq**: Fast LLM inference (Llama 3.3 70B)
- **Gradio**: Web UI
- **Tavily**: AI-powered web search and scraping
- **YouTube Data API v3**: Video search

## 🏛️ Architecture

The application uses a **state machine** built with LangGraph:

```
START → Planner (gather info) → Research → Generate Guide → 
        Ask Refinement ⟲ Handle Refinement → END
                      ↓
                YouTube Search
```

### State Flow

1. **Gather Info**: Collect company name and role
2. **Research**: Search web for company information and summarize
3. **Generate**: Create interview prep guide with LLM
4. **Refinement Loop**: Allow user to refine (max 3 times)
5. **Completion**: Finalize and encourage user

### Node Functions

- `planner`: Conversational info gathering
- `research`: Web search and company information gathering
- `generate_guide`: LLM-powered guide creation
- `ask_refinement`: Present guide with options
- `handle_refinement`: Process user feedback
- `youtube_search_node`: Fetch relevant videos

## 🛠️ Development

### Adding New Features

1. **New node**: Add function to `src/nodes.py`
2. **Update graph**: Modify `src/graph.py` routing
3. **Configuration**: Add constants to `src/config.py`
4. **External service**: Extend `src/external_services.py`

## 📝 License

This project is for educational purposes.

## 🙏 Acknowledgments

- **Groq** for fast LLM inference
- **LangGraph** for workflow orchestration
- **Tavily** for AI-powered web search
- **Gradio** for the UI framework

---

**Built with ❤️ using LangGraph and Groq**

