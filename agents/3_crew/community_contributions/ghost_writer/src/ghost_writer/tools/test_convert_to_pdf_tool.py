import pytest
from pathlib import Path
from PIL import Image
from ghost_writer.tools.convert_to_pdf_tool import MarkdownToPDFTool, MarkdownToPDFInput

def create_test_image(path: Path):
    """Creates a simple black 100x100 PNG image at the specified path."""
    image = Image.new('RGB', (100, 100), color='black')
    image.save(path)

def test_markdown_to_pdf_tool_with_image(tmp_path):
    # Arrange
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    image_path = images_dir / "cover.png"
    create_test_image(image_path)

    # Markdown file with a reference to the image
    md_path = tmp_path / "book.md"
    md_content = f"""
# Test Book Title

![Cover](images/cover.png)

## Chapter 1

This is a test chapter.
"""
    md_path.write_text(md_content, encoding="utf-8")

    # Output PDF path
    pdf_path = tmp_path / "book.pdf"

    # Act
    tool = MarkdownToPDFTool()
    input_data = MarkdownToPDFInput(
        markdown_path=str(md_path),
        output_pdf_path=str(pdf_path)
    )
    result = tool.run(**input_data.dict())

    # Assert
    assert pdf_path.exists(), f"Expected PDF at {pdf_path}, but it wasn't created"
    assert "successfully" in result.lower()
    print(result)
