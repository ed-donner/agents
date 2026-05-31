import os
from pathlib import Path
from dotenv import load_dotenv

def find_env_file():
    """Search upward for .env file starting from current file location"""
    current_path = Path(__file__).resolve().parent
    
    # Search up to 10 levels up
    for _ in range(10):
        env_path = current_path / ".env"
        if env_path.exists():
            return env_path
        
        # Move up one directory
        parent = current_path.parent
        if parent == current_path:  # Reached filesystem root
            break
        current_path = parent
    
    return None

# Load environment variables from project root
env_path = find_env_file()
if env_path:
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✓ Loaded .env from: {env_path}")
else:
    print("⚠️  No .env file found, using system environment variables")
    load_dotenv()  # Load from default locations

# Disable tracing to prevent non-fatal errors
os.environ['LANGCHAIN_TRACING_V2'] = "false"
os.environ['LANGSMITH_TRACING'] = "false"
os.environ['LANGCHAIN_API_KEY'] = ""

# Set OpenAI configuration
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    os.environ['OPENAI_API_KEY'] = api_key

# Set OpenAI base URL (configurable via .env, defaults to standard OpenAI)
base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
os.environ['OPENAI_BASE_URL'] = base_url
if base_url != 'https://api.openai.com/v1':
    print(f"✓ Using custom OpenAI gateway: {base_url}")

# Suppress tracing error messages
import sys
import warnings
warnings.filterwarnings("ignore", message=".*Tracing client error.*")

class SuppressTracingErrors:
    def __init__(self, stream):
        self.stream = stream
    def write(self, text):
        if "[non-fatal] Tracing client error" not in text:
            self.stream.write(text)
    def flush(self):
        self.stream.flush()

sys.stderr = SuppressTracingErrors(sys.stderr)

import gradio as gr
from learning_manager import LearningManager


async def analyze_code(file_path: str, task_description: str, include_git_diff: bool, include_commit_history: bool):
    """Analyze code and generate learning documentation"""
    if not file_path:
        yield "⚠️ Please provide a file path", "", "", None
        return
    
    manager = LearningManager()
    status_message = ""
    saved_file_path = None
    
    try:
        async for chunk in manager.analyze_code(
            file_path=file_path,
            task_description=task_description,
            include_git_diff=include_git_diff,
            include_commit_history=include_commit_history
        ):
            # Check if this is a status update or final result
            if chunk and not chunk.startswith("#") and len(chunk) < 500:
                status_message += f"✓ {chunk}\n\n"
                # Yield status, empty output, empty link, no file
                yield status_message, "*Generating documentation...*", "", None
            else:
                # This is the final documentation
                # Try to extract the saved file path from the documentation
                import re
                # Look for file path in various formats
                patterns = [
                    r'learning_docs/[^\s\)"\'\]]+\.md',
                    r'saved_to["\']?:\s*["\']?([^"\'\s\)]+\.md)',
                    r'Documentation saved to:?\s*([^\s\)]+\.md)'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, chunk, re.IGNORECASE)
                    if match:
                        if match.groups():
                            saved_file_path = match.group(1)
                        else:
                            saved_file_path = match.group(0)
                        break
                
                # Also check for files created in the learning_docs directory recently
                if not saved_file_path:
                    import glob
                    from datetime import datetime, timedelta
                    recent_files = glob.glob("learning_docs/*.md")
                    if recent_files:
                        # Get the most recent file
                        recent_files.sort(key=os.path.getmtime, reverse=True)
                        saved_file_path = recent_files[0]
                
                # Provide download file and ALWAYS show content on screen
                if saved_file_path and os.path.exists(saved_file_path):
                    abs_path = os.path.abspath(saved_file_path)
                    
                    # Read the saved file to display it
                    try:
                        with open(saved_file_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                    except:
                        file_content = chunk  # Fallback to original chunk
                    
                    # Create clean markdown success message
                    success_message = f'''
> ✅ **Document Saved Successfully!**
> 
> 📁 **Saved to:** `{saved_file_path}`
> 
> 💾 **Use the download button below to save a copy**
'''
                    
                    # Show the actual markdown content ON SCREEN + provide download
                    display_output = f"**✅ Analysis Complete!**\n\n{success_message}\n\n---\n\n{file_content}"
                    
                    yield status_message + "✓ Documentation complete!\n", display_output, "", abs_path
                else:
                    # No file found but still display the content on screen
                    display_output = f"**✅ Analysis Complete!**\n\n---\n\n{chunk}"
                    yield status_message + "✓ Documentation complete!\n", display_output, "", None
                    
    except Exception as e:
        error_msg = f"❌ **Error during analysis:**\n\n```\n{str(e)}\n```"
        if "403" in str(e):
            error_msg += "\n\n💡 **Tip:** The OpenAI gateway might be temporarily unavailable. Please try again in a moment."
        elif "404" in str(e):
            error_msg += "\n\n💡 **Tip:** Make sure the file path is correct and the file exists."
        yield status_message + "❌ Analysis failed\n", error_msg, "", None


# Build the Gradio interface with professional styling
custom_theme = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="blue",
    neutral_hue="slate",
    font=["Inter", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Arial", "sans-serif"],
    font_mono=["Fira Code", "Consolas", "Monaco", "monospace"]
)

with gr.Blocks(theme=custom_theme, css="""
    .gradio-container {
        max-width: 1400px !important;
    }
    h1 {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        margin-bottom: 1rem !important;
    }
    h3 {
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.75rem !important;
    }
    .markdown-text {
        font-size: 1rem !important;
        line-height: 1.7 !important;
    }
    .status-box {
        background-color: #f8fafc !important;
        border-left: 4px solid #6366f1 !important;
        padding: 1rem !important;
        border-radius: 6px !important;
        margin-bottom: 1rem !important;
        min-height: 80px !important;
    }
    code {
        background-color: #f6f8fa !important;
        padding: 0.2em 0.4em !important;
        border-radius: 3px !important;
        font-size: 0.9em !important;
    }
    pre {
        background-color: #f6f8fa !important;
        padding: 1rem !important;
        border-radius: 6px !important;
        overflow-x: auto !important;
    }
""") as ui:
    gr.Markdown(
        """
        # 📚 Code Learning Assistant
        
        <p style="font-size: 1.15rem; color: #64748b; margin-top: 0.5rem; margin-bottom: 1.5rem;">
        AI-powered system to help you <strong>learn</strong> and <strong>document</strong> code in any programming language
        </p>
        """,
        elem_classes="header-section"
    )
    
    with gr.Row():
        gr.Markdown("🎓 **Learn** new languages")
        gr.Markdown("📝 **Document** for PRs")
        gr.Markdown("🔍 **Understand** codebases")
        gr.Markdown("✍️ **Generate** learning notes")
    
    gr.Markdown("---")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📂 Configuration")
            
            file_path_input = gr.Textbox(
                label="File Path",
                placeholder="/path/to/your/code/file.go",
                lines=1,
                info="Relative or absolute path to the code file you want to analyze"
            )
            
            task_description = gr.Textbox(
                label="Task Description (Optional)",
                placeholder="Added authentication middleware to API endpoints...",
                lines=3,
                info="Describe what you implemented or what you want to learn"
            )
            
            with gr.Row():
                include_git_diff = gr.Checkbox(
                    label="📊 Git Diff",
                    value=False,
                    info="Show what changed"
                )
                include_commit_history = gr.Checkbox(
                    label="📜 Commit History",
                    value=False,
                    info="Show file evolution"
                )
            
            with gr.Row():
                run_button = gr.Button("🚀 Analyze Code", variant="primary", size="lg")
                clear_button = gr.Button("🗑️ Clear", size="lg")
            
            with gr.Accordion("📖 Examples & Tips", open=False):
                gr.Markdown(
                    """
                    **Local file:**
                    ```
                    code_assistant.py
                    ```
                    
                    **Absolute path:**
                    ```
                    /Users/you/projects/myapp/src/main.py
                    ```
                    
                    **With task context:**
                    ```
                    File: backend/auth.go
                    Task: Implemented JWT authentication
                    ```
                    """
                )
        
        with gr.Column(scale=2):
            gr.Markdown("### 🔄 Status")
            
            status_box = gr.Markdown(
                value="<p style='color: #94a3b8; font-style: italic;'>Ready to analyze...</p>",
                elem_classes="status-box"
            )
            
            gr.Markdown("### 📄 Generated Documentation")
            
            output_markdown = gr.Markdown(
                value="<p style='color: #94a3b8; font-style: italic;'>Your learning documentation will appear here...</p>",
                elem_classes="output-area"
            )
            
            download_info = gr.HTML(
                value="",
                label="Status"
            )
            
            download_file = gr.File(
                label="📥 Download Documentation",
                visible=True,
                interactive=False
            )
    
    gr.Markdown("---")
    
    with gr.Accordion("🎯 What You'll Get", open=False):
        gr.Markdown(
            """
            - **Language Concepts**: Understand the programming patterns and features used
            - **Code Explanation**: Step-by-step breakdown of what the code does
            - **Change Documentation**: Professional PR-ready documentation
            - **Git Analysis**: What specifically changed (if enabled)
            - **Learning Notes**: Saved to `learning_docs/` folder for future reference
            """
        )
    
    with gr.Accordion("💡 Tips for Best Results", open=False):
        gr.Markdown(
            """
            - Start with simple files to get familiar with the output
            - Add task context for better, more focused documentation
            - Use git diff analysis to understand your changes
            - Generated docs are saved automatically with timestamps
            """
        )
    
    # Event handlers
    run_button.click(
        fn=analyze_code,
        inputs=[file_path_input, task_description, include_git_diff, include_commit_history],
        outputs=[status_box, output_markdown, download_info, download_file]
    )
    
    file_path_input.submit(
        fn=analyze_code,
        inputs=[file_path_input, task_description, include_git_diff, include_commit_history],
        outputs=[status_box, output_markdown, download_info, download_file]
    )
    
    clear_button.click(
        fn=lambda: (
            "", 
            "", 
            False,
            False,
            "<p style='color: #94a3b8; font-style: italic;'>Ready to analyze...</p>",
            "<p style='color: #94a3b8; font-style: italic;'>Your learning documentation will appear here...</p>",
            "",
            None
        ),
        outputs=[file_path_input, task_description, include_git_diff, include_commit_history, status_box, output_markdown, download_info, download_file]
    )


if __name__ == "__main__":
    print("🚀 Starting Code Learning Assistant...")
    print("📍 Access the UI at: http://127.0.0.1:7860")
    ui.launch(inbrowser=True)

