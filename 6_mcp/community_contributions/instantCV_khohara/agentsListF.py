import os
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio

model = "gpt-4.1-mini"

def get_fileserver_params():
    return {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
        "env": {}
    }

async def run_cv_agent(details: str):
    instructions = """
    Take the provided information and save it in a file 'cv.md' using the write_file tool.
    Format as:
    Name: ...
    Email: ...
    Contact: ...
    Education: ...
    Experience: ...
    Skills: ...
    """
    async with MCPServerStdio(params=get_fileserver_params(), client_session_timeout_seconds=60) as server:
        agent = Agent(name="cv_maker", model=model, instructions=instructions, mcp_servers=[server])
        with trace("CV Maker"):
            await Runner.run(agent, details)

async def run_extender_agent():
    instructions = """
    Read the file 'cv.md' using the filesystem MCP server.
    Expand the Experience into detailed bullet points.
    Add inferred skills. Add the details to make the cv more professional and appealing like details about skills and experience.
    Format into a professional CV in Markdown.
    Overwrite 'cv.md'.
    """
    async with MCPServerStdio(params=get_fileserver_params(), client_session_timeout_seconds=60) as server:
        agent = Agent(name="extender", model=model, instructions=instructions, mcp_servers=[server])
        with trace("Extender"):
            await Runner.run(agent, "Please improve the CV")

async def run_html_agent():
    instructions = """
    Read cv.md and convert into a professional HTML CV.
    Style:
    - Two-column layout (left: contact/skills, right: education/experience).
    - Use clean fonts (Arial/Helvetica).
    - Bold section titles, subtle separators.
    - Add proper color and styles to make cv more impactfull
    Save as cv.html.
    """
    async with MCPServerStdio(params=get_fileserver_params(), client_session_timeout_seconds=60) as server:
        agent = Agent(name="stylingagent", model=model, instructions=instructions, mcp_servers=[server])
        with trace("Styling"):
            await Runner.run(agent, "Convert CV to styled HTML")

def convert_html_to_pdf(input_file="cv.html", output_file="cv.pdf"):
    import pdfkit
    pdfkit.from_file(input_file, output_file)
    return output_file
