import os
import sys
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from crewai import Agent, Task, Crew, Process
from crewai_tools import DirectoryReadTool, FileReadTool
from langchain_community.tools import DuckDuckGoSearchRun

# Ensure API key is set
if not os.environ.get("OPENAI_API_KEY"):
    print("WARNING: OPENAI_API_KEY environment variable is not set.")
    print("Please set it in your .env file or environment before running the script.")

# Initialize Tools
directory_read_tool = DirectoryReadTool()
file_read_tool = FileReadTool()
search_tool = DuckDuckGoSearchRun()

# --- AGENTS ---

parser_agent = Agent(
    role='Dependency and Code Parser',
    goal='Scan a target repository or local project directory to extract dependency versions (e.g., from requirements.txt, package.json) and flag potential insecure code patterns such as hardcoded credentials or unvalidated inputs.',
    backstory='You are an expert static analysis tool and code parser. You meticulously traverse project structures, read dependency files, and quickly identify common security anti-patterns in source code.',
    verbose=True,
    allow_delegation=False,
    tools=[directory_read_tool, file_read_tool]
)

advisory_researcher_agent = Agent(
    role='Vulnerability Advisory Researcher',
    goal='Match identified packages and their specific versions against published CVEs and security advisories to find known vulnerabilities.',
    backstory='You are a seasoned cybersecurity researcher. You leverage search engines and vulnerability databases to find out if specific versions of software dependencies have known security flaws.',
    verbose=True,
    allow_delegation=False,
    tools=[search_tool]
)

remediation_specialist_agent = Agent(
    role='Remediation and Patch Specialist',
    goal='Evaluate whether suggested dependency upgrades will introduce breaking changes, and draft concrete patch recommendations with exact version pins and remediation strategies.',
    backstory='You are a senior DevSecOps engineer. You understand semantic versioning deeply and know how to recommend safe upgrades that patch security holes without breaking existing code. You also provide guidance on fixing insecure code patterns.',
    verbose=True,
    allow_delegation=False,
    tools=[search_tool]
)

# --- TASKS ---

def run_audit(target_dir):
    parse_task = Task(
        description=(
            f'1. Use the directory_read_tool to scan the target project directory provided: {target_dir}\n'
            '2. Identify dependency files like requirements.txt, package.json, etc.\n'
            '3. Use the file_read_tool to read the contents of these dependency files and extract package names and their exact versions.\n'
            '4. Read main source code files and briefly scan for hardcoded credentials (e.g., passwords, API keys) or obvious insecure patterns like eval() or exec() with user inputs.\n'
            '5. Compile a detailed report of all dependencies found and any insecure code patterns spotted.'
        ),
        expected_output='A structured list of project dependencies with their versions, and a list of any identified insecure code patterns.',
        agent=parser_agent
    )

    research_task = Task(
        description=(
            '1. Take the list of dependencies and versions provided by the Dependency and Code Parser.\n'
            '2. For each dependency, use the search_tool to look up known vulnerabilities or CVEs associated with that specific version.\n'
            '3. Summarize the vulnerabilities found, noting severity and any available context.\n'
            '4. Document dependencies that appear to be secure based on the search.'
        ),
        expected_output='A comprehensive vulnerability report detailing CVEs and security issues for the identified dependencies.',
        agent=advisory_researcher_agent,
        context=[parse_task]
    )

    remediation_task = Task(
        description=(
            '1. Analyze the vulnerability report provided by the Vulnerability Advisory Researcher.\n'
            '2. For each vulnerable package, recommend a safe upgrade path (e.g., specific version to pin) that patches the vulnerability.\n'
            '3. Evaluate if the upgrade is likely to introduce breaking changes (major version bumps).\n'
            '4. Provide specific remediation advice for any insecure code patterns identified by the Parser.\n'
            '5. Compile everything into a final, structured Markdown Audit Report.'
        ),
        expected_output='A final structured Markdown Audit Report containing dependencies, found vulnerabilities, recommended patches (with exact version pins), and remediation steps for insecure code.',
        agent=remediation_specialist_agent,
        context=[parse_task, research_task],
        output_file='security_audit_report.md'
    )

    # --- CREW ---
    auditor_crew = Crew(
        agents=[parser_agent, advisory_researcher_agent, remediation_specialist_agent],
        tasks=[parse_task, research_task, remediation_task],
        process=Process.sequential,
        verbose=True
    )

    return auditor_crew.kickoff()

if __name__ == "__main__":
    print("======================================================")
    print("  Automated Dependency & Security Auditor for Code  ")
    print("======================================================")
    
    if len(sys.argv) > 1:
        target_directory = sys.argv[1]
    else:
        target_directory = input("Enter the path to the project directory you want to audit (default: './sample_project'): ").strip()
        if not target_directory:
            target_directory = './sample_project'
            
    print(f"\n[i] Starting audit on: {target_directory}\n")
    
    result = run_audit(target_directory)
    
    print("\n======================")
    print("### AUDIT COMPLETE ###")
    print("======================")
    print("\nReport has been saved to: security_audit_report.md\n")
