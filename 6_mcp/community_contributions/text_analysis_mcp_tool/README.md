This is a simple example of:
- Creating basic tools (text reader, basic stats on text, and readability score): document.py
- Creating an MCP server for these tools: document_server.py
- Using in a basic gradio chat interface (user uploads file, analysis is provided and further questions can be asked): app.py

Important to have the latest openai-agents package (included in the requirements) for this to work as it uses sessions for the memory (import SQLiteSession).