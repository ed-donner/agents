from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from markdown_pdf import MarkdownPdf, Section
from pathlib import Path
from contextlib import contextmanager
import os

# Context manager for safe pushd/popd behavior
@contextmanager
def pushd(directory: Path):
    prev_dir = Path.cwd()
    os.chdir(directory)
    print(f"Changed directory to: {directory}") 
    try:
        yield
    finally:
        os.chdir(prev_dir)
        print(f"Returned to directory: {prev_dir}")

class MarkdownToPDFInput(BaseModel):
    markdown_path: str = Field(..., description="Path to the input Markdown file.")
    output_pdf_path: str = Field(..., description="Path where the output PDF will be saved.")

class MarkdownToPDFTool(BaseTool):
    name: str = "Markdown to PDF Converter"
    description: str = "Converts a Markdown file into a PDF document."
    args_schema: Type[BaseModel] = MarkdownToPDFInput

    def _run(self, markdown_path: str, output_pdf_path: str) -> str:
        md_path = Path(markdown_path).resolve()
        out_path = Path(output_pdf_path).resolve()

        if not md_path.exists():
            return f"Markdown file not found: {md_path}"

        # Read the markdown content
        md_content = md_path.read_text(encoding="utf-8")

        # Safely switch working directory for image resolution
        with pushd(md_path.parent):
            pdf = MarkdownPdf(toc_level=0)
            pdf.add_section(Section(md_content))
            pdf.meta["title"] = md_path.stem

            # Create output directory if needed
            out_path.parent.mkdir(parents=True, exist_ok=True)
            
            pdf.save(str(out_path))

        return f"PDF successfully created at: {out_path}"
