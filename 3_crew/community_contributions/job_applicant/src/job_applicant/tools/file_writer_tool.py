import os
import re
from crewai.tools import BaseTool


class FileWriterTool(BaseTool):
    """Writes generated content (tailored resumes, cover letters) to the output directory."""

    name: str = "file_writer"
    description: str = (
        "Writes text content to a file in the output directory. "
        "Input format: 'filename|||content' where filename is the desired filename "
        "(e.g., 'Google_SWE_resume.md') and content is the text to write. "
        "Returns the full path of the written file."
    )

    def _run(self, input_data: str) -> str:
        if "|||" not in input_data:
            return (
                "Error: Input must be in format 'filename|||content'. "
                "Example: 'Google_SWE_resume.md|||Your resume content here...'"
            )

        parts = input_data.split("|||", 1)
        filename = parts[0].strip()
        content = parts[1].strip()

        if not filename:
            return "Error: Filename cannot be empty."
        if not content:
            return "Error: Content cannot be empty."

        # Sanitize filename
        filename = re.sub(r'[^\w\-_. ]', '_', filename)
        filename = filename.replace(' ', '_')

        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        ))), "output")
        os.makedirs(output_dir, exist_ok=True)

        file_path = os.path.join(output_dir, filename)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully written to: {file_path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"
