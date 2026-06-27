"""
PDF Writer Node - Converts markdown content to a styled PDF file.
"""

from typing import Dict, Any
from state import State
from tools import generate_pdf_from_markdown, SANDBOX_DIR


class PDFWriterNode:
    """
    Convert the markdown content to a styled PDF document.
    Saves the file to the sandbox directory.
    """
    
    def __init__(self):
        # No initialization needed - uses tools directly
        pass

    def execute(self, state: State) -> Dict[str, Any]:
        """Execute the PDF writer node."""
        topic = state["topic"]
        markdown_content = state.get("markdown_content")
        if not markdown_content:
            return {
                "pdf_path": None,
                "messages": [{"role": "assistant", "content": "Error: No markdown content to convert."}]
            }
        safe_topic = topic.lower().replace(" ", "_").replace("/", "_")
        filename = f"learning_path_{safe_topic}"
        generate_pdf_from_markdown(markdown_content, filename)
        filepath = str(SANDBOX_DIR / f"{filename}.pdf")
        return {
            "pdf_path": filepath,
            "messages": [{"role": "assistant", "content": f"PDF generated: {filepath}"}]
        }
