from typing import Dict
from agents import Agent, function_tool


@function_tool
def print_text(txt: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body"""
    print(txt)


INSTRUCTIONS = """You are able to send a nicely formatted plain text based on a detailed report.
You will be provided with a detailed report. You should use your tool to print the report, providing the
report converted into clean, well presented plain text.
The report may contain sections, bullet points, and other formatting.
Your job is to convert this into a plain text format that is easy to read and understand.
Use newlines, indentation, and other plain text formatting techniques to make the report as clear as possible.
Do not include any additional commentary or information that is not in the original report.
Your output should be a clean, well formatted plain text version of the original report."""

printer_agent = Agent(
    name="Printer agent",
    instructions=INSTRUCTIONS,
    tools=[print_text],
    model="gpt-4o-mini",
)
