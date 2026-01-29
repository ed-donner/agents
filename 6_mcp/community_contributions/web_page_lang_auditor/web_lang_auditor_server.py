import os
from mcp.server.fastmcp import FastMCP
from web_lang_auditor import WebPageLangAuditor

BASE_INPUT_DIR = "input"
BASE_OUTPUT_DIR = "output"

mcp = FastMCP("web-lang-auditor")

def resolve_input_path(filename: str) -> str:
    path = os.path.join(BASE_INPUT_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {filename}")
    return path

def ensure_output_dir_exists(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

@mcp.tool()
def run_web_lang_audit(input_csv: str) -> str:
    """
    Synchronous MCP tool to run web page language audit.
    """

    input_path = resolve_input_path(input_csv)
    output_dir = ensure_output_dir_exists(BASE_OUTPUT_DIR)
    auditor = WebPageLangAuditor(input_path, output_dir)
    auditor.run_full_audit()  
    return f"Audit of {input_csv} completed successfully in {output_dir}"

if __name__ == "__main__":
    print("Starting web-lang-auditor MCP server…")
    mcp.run() 