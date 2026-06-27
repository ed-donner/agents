from pathlib import Path

PAGE_BREAK = "<div style=\"page-break-after: always;\"></div>\n\n"

def add_page_break():
    """
    Returns a markdown/html page break.
    """
    return PAGE_BREAK

def image_markdown(image_path: str, alt_text: str = "") -> str:
    """
    Returns a markdown image tag.
    
    Args:
        image_path (str): Relative or absolute path to image.
        alt_text (str): Alternative text for the image.
        
    Returns:
        str: Markdown image tag.
        
    Example:
        image_markdown('images/cover.png', 'Book Cover')
        # -> "![Book Cover](images/cover.png)"
    """
    return f"![{alt_text}]({image_path})\n\n"

def header_markdown(text: str, level: int = 1) -> str:
    """
    Returns a markdown header of the specified level.
    
    Args:
        text (str): Header text.
        level (int): Header level (1-6).
    
    Returns:
        str: Markdown header.
    """
    return f"{'#' * level} {text}\n\n"

def write_markdown(content: str, file_path: str, mode: str = "a"):
    """
    Appends or writes markdown content to a file.
    
    Args:
        content (str): The markdown text to write.
        file_path (str): Path to the markdown file.
        mode (str): File mode, "a" for append, "w" for overwrite.
    """
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, mode, encoding="utf-8") as f:
        f.write(content)

def code_block_markdown(code: str, language: str = "") -> str:
    """
    Returns a markdown code block.
    
    Args:
        code (str): The code to include in the block.
        language (str): (Optional) Language identifier for syntax highlighting.
    
    Returns:
        str: Markdown code block.
    """
    return f"```{language}\n{code}\n```\n\n"
