from mcp.server.fastmcp import FastMCP
from document import Document

mcp = FastMCP("document_server")

@mcp.tool()
async def file_reader(filepath: str, filetype: str) -> str:
    """Get text from files at a specified path.  Types supported are docx, doc, pdf, txt.

    Args:
        filepath: the full path /location of the file from which the text will be extracted
        filetype: the filetype of the file from which the text will be extracted (limited to docx, doc, pdf, txt)
    """
    doc = Document(filepath= filepath, filetype= filetype)

    return doc.file_reader()

@mcp.tool()
async def text_counts(filepath: str, filetype: str) -> str:
    """Get text counts from files at a specified path. Types supported are docx, doc, pdf, txt.

    Args:
        filepath: the full path /location of the file from which the text statistics will be calculated
        filetype: the filetype of the file from which the text statistics will be calculated (limited to docx, doc, pdf, txt)
    """

    doc = Document(filepath= filepath, filetype= filetype)
   
    return doc.text_counts()

@mcp.tool()
async def text_analyses(filepath: str, filetype: str) -> str:
    """Get readability analysis from files at a specified path. Types supported are docx, doc, pdf, txt.

    Args:
        filepath: the full path /location of the file from which the readability analysis will be performed
        filetype: the filetype of the file from which the readability analysis will be performed (limited to docx, doc, pdf, txt)
    """

    doc = Document(filepath= filepath, filetype= filetype)

    return doc.text_analyses()



if __name__ == "__main__":
    mcp.run(transport='stdio')