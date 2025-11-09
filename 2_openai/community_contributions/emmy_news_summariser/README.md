# Multimodal Agent News Summarizer

An AI-powered news summarization system that aggregates news from multiple RSS feeds, creates concise summaries using Gemini 2.5 Flash, and generates audio briefings using MiniMax TTS. Built with a modular agent-based architecture following OpenAI Agents SDK patterns.

## 🚀 Features

- **Multi-Source News Aggregation**: Concurrently fetches news from multiple RSS feeds across different topics (tech, world, business, politics, sports)
- **AI-Powered Summarization**: Uses Google's Gemini 2.5 Flash to create engaging 300-word summaries optimized for audio consumption
- **Text-to-Speech**: Converts summaries into high-quality audio files using MiniMax TTS API
- **Modern Web Interface**: Beautiful Gradio-based UI with blue theme for easy interaction
- **Agent-Based Architecture**: Modular design with separate agents for each task, following OpenAI Agents SDK patterns
- **Async/Await Support**: Fully asynchronous implementation for optimal performance

### (The Solution)

- Agents use Google Gemini's function calling API
- LLM decides when and how to use tools
- Agents reason about tasks and autonomously choose tools
- Proper agent loop: LLM → decides → calls tool → processes result → responds

```python
# NEW: Agent decides autonomously what to do
articles_response = await self.aggregator.run(
    f"Fetch the latest news articles about {topic}"
)
# ↑ The agent analyzes this request and decides to call aggregate_news
```

## Technical Implementation

### 1. Agent Class with Real LLM Behavior

**File:** `agents/base.py`

The `Agent` class:

1. Initializes Gemini with function declarations
2. Runs an agent loop that handles function calling
3. Executes tools when LLM requests them
4. Returns final responses

```python
class Agent:
    def __post_init__(self):
        # Convert Python functions to Gemini function declarations
        self.function_declarations = [
            _convert_tool_to_function_declaration(tool)
            for tool in self.tools
        ]

        # Initialize Gemini with tools
        self.model_instance = genai.GenerativeModel(
            model_name=self.model,
            tools=self.function_declarations,
            system_instruction=self.instructions
        )

    async def run(self, user_message: str) -> Any:
        # Start chat and send user message
        response = chat.send_message(user_message)

        # Agent loop: LLM decides to call tools
        while has_function_calls(response):
            # Execute requested tools
            tool_results = await execute_tools(response.function_calls)

            # Send results back to LLM
            response = chat.send_message(tool_results)

        return final_response
```

### 2. Tool Schema Conversion

**Function:** `_convert_tool_to_function_declaration()`

Automatically converts Python functions to Gemini function declarations:

```python
@function_tool
async def aggregate_news(topic: str, num_sources: int = 5) -> Dict[str, Any]:
    """Aggregate news from RSS feeds concurrently."""
    # ...

# Gets converted to:
{
    "name": "aggregate_news",
    "description": "Aggregate news from RSS feeds concurrently.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "topic": {"type": "STRING", "description": "Parameter topic"},
            "num_sources": {"type": "INTEGER", "description": "Parameter num_sources"}
        },
        "required": ["topic"]
    }
}
```

### 3. Autonomous Orchestration

**File:** `orchestrator.py`

Instead of calling functions directly, the orchestrator now **delegates to agents**:

```python
# Step 1: Aggregator agent autonomously fetches news
articles_response = await self.aggregator.run(
    f"Fetch the latest news articles about {topic}",
    return_raw_tool_result=True
)
# The LLM sees this request, decides aggregate_news is needed, calls it

# Step 2: Summarizer agent autonomously creates summary
summary = await self.summarizer.run(
    f"Summarize these news articles: {json.dumps(articles)}"
)
# The LLM sees articles, decides summarize_articles is needed, calls it

# Step 3: Audio generator agent autonomously creates audio
audio_path = await self.audio_generator.run(
    f"Convert this text to speech: {summary}"
)
# The LLM sees text, decides synthesize_speech is needed, calls it
```

## Key Features

### 1. Autonomous Tool Selection

The LLM analyzes the user's request and decides which tool(s) to use:

```
User: "Fetch the latest news articles about tech"
                     ↓
    LLM analyzes: "I need to get tech news"
                     ↓
    LLM decides: "I should call aggregate_news with topic='tech'"
                     ↓
    Agent executes: aggregate_news(topic="tech")
                     ↓
    LLM processes result and responds
```

### 2. Multi-Step Reasoning

Agents can chain multiple tool calls:

```python
# Agent could decide to:
# 1. Call aggregate_news for "tech"
# 2. See the results aren't enough
# 3. Call aggregate_news again for "business"
# 4. Combine and respond
```

### 3. Error Handling

Agents handle tool errors gracefully:

```python
try:
    result = await tool_func(**function_args)
except Exception as e:
    # Agent receives error message
    # LLM can reason about the error and try alternative approaches
    function_response = f"Error: {str(e)}"
```

### 4. Flexible Output Modes

```python
# Get LLM's natural language response
result = await agent.run("Get tech news")
# → "I've fetched 15 tech articles from 5 sources..."

# Get raw tool result (for structured data)
result = await agent.run("Get tech news", return_raw_tool_result=True)
# → {"articles": [...]}
```

### Real Agent Pattern

This follows the proper agent pattern used by frameworks like:

- OpenAI Agents SDK
- Anthropic Claude Agents

Where agents:

1. Receive high-level instructions
2. Reason about how to accomplish tasks
3. Decide which tools to use
4. Execute tools autonomously
5. Return results

### Benefits

1. **Flexibility**: Change agent behavior by updating instructions, not code
2. **Extensibility**: Add new tools, agents automatically learn to use them
3. **Robustness**: Agents can handle unexpected situations
4. **Maintainability**: Less hardcoded logic, more declarative instructions

## Testing

To test the implementation:

```bash
# Ensure environment variables are set
# GEMINI_API_KEY=your_key
# GEMINI_BASE_URL=your_base_url
# MINIMAX_API_KEY=your_key

# Run the test suite
python test_agents.py
```

The test will:

1. Test each agent individually
2. Verify autonomous tool calling
3. Run the complete orchestrator workflow
4. Show agent decision-making in action

## Example Output

```
[News Aggregator] Calling tool: aggregate_news with args: {'topic': 'tech'}
✓ Fetched 15 articles

[News Summarizer] Calling tool: summarize_articles with args: {'articles_json': '[...]'}
✓ Summary created (287 words)

[Audio Generator] Calling tool: synthesize_speech with args: {'text': '...'}
✓ Audio generated: news_summary_20251107_095453.mp3
```

## Architecture Diagram

```
User Request
     ↓
Orchestrator (Delegates to agents)
     ↓
┌────────────────────────────────────┐
│  Agent (with LLM reasoning)        │
│  ┌──────────────────────────────┐  │
│  │ 1. Analyze user request      │  │
│  │ 2. Decide which tool to use  │  │
│  │ 3. Call tool with parameters │  │
│  │ 4. Process tool result       │  │
│  │ 5. Return final response     │  │
│  └──────────────────────────────┘  │
│                                    │
│  Available Tools:                  │
│  • aggregate_news                  │
│  • summarize_articles              │
│  • synthesize_speech               │
└────────────────────────────────────┘
```

## Conclusion

This implementation uses "autonomous agents with LLM-powered decision making". The agents reason about tasks and decide how to accomplish them, following industry-standard agent patterns.

## Response to Code Review

**Flow:**

- ✅ Agents use Gemini's native function calling
- ✅ `@function_tool` decorator enables tool schema generation
- ✅ LLM autonomously decides which tools to call
- ✅ Follows real agent patterns from OpenAI/LangChain/Anthropic
- ✅ Agents are actually used in the workflow (not just their tools)
