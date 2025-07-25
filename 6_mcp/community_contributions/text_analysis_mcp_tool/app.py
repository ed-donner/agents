from dotenv import load_dotenv
from agents import Agent, Runner, SQLiteSession, trace, gen_trace_id
from agents.mcp import MCPServerStdio
import gradio as gr

load_dotenv(override=True)

# Configuration
INSTRUCTIONS = """You are a document analysis assistant. The user has provided a document file path that you should analyze. 
You can extract text from docx, doc, pdf, and txt files. You can also provide basic statistics on the text and do readability assessments.
When the user first provides a file path, acknowledge it, provide some basic statistics and a one line reference to what the document contains.
For follow-up questions, continue to use the appropriate tools to answer their specific requests about the document.
You should extract the file type from the file path provided."""

MODEL = "gpt-4.1-mini"
MCP_PARAMS = {"command": "uv", "args": ["run", "document_server.py"]}

# Create agent - add MCP servers at run
document_agent = Agent(
    name="text_analyser",
    instructions=INSTRUCTIONS,
    model=MODEL
)

# Session store
session_store = {}

async def respond(message, history):
    """Main response function for ChatInterface"""
    # Extract text and files from message
    text_content = message.get("text", "").strip()
    files = message.get("files", [])
    
    # Create session ID
    session_id = "document_chat_session"
    if session_id not in session_store:
        session_store[session_id] = SQLiteSession(session_id)
    session = session_store[session_id]
  
    if hasattr(session, 'trace_id') and session.trace_id:
        trace_id = session.trace_id
    else:
        trace_id = gen_trace_id()
        session.trace_id = trace_id
    
    with trace("Document chat", trace_id=trace_id):
        print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
    
        # Build the message for the agent  
        if files:
            # New document uploaded
            full_message = f"Please analyze this document and provide some basic details based on the tools available: {files[0]}"
            # If text with document
            if text_content:
                full_message = f"{text_content}\n\n{full_message}"
        else:
            # Follow up questions
            if not text_content:
                return "Please upload a document or ask a question about your uploaded document."
            full_message = text_content

        try:
            # Create MCP server and run with session       
            async with MCPServerStdio(params=MCP_PARAMS, client_session_timeout_seconds=30) as mcp_server:
                # Add MCP server to agent for this run
                document_agent.mcp_servers = [mcp_server]
                
                result = await Runner.run(
                    document_agent,
                    full_message,
                    session=session
                )
                return result.final_output
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"

# Create the ChatInterface
demo = gr.ChatInterface(
    fn=respond,
    type="messages",
    multimodal=True,
    title="AI Document Chat Assistant",
    description="**Upload a document and chat about it!**",
    textbox=gr.MultimodalTextbox(
        file_types=[".pdf", ".docx", ".doc", ".txt"],
        placeholder="Upload a document above, then ask questions about it, e.g. ask about document readability!",
        file_count="single"
    )
)

if __name__ == "__main__":
    demo.launch()