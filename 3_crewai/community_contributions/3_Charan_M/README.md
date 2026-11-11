# Automated Dependency & Security Auditor

This is a mini-project using a multi-agent CrewAI setup to scan code repositories for dependencies and code vulnerabilities, research advisories, and propose remediation strategies.

## Agent Architecture

1. **Parser Agent**: Traverses the target project, extracts dependency versions (e.g., from `requirements.txt`), and flags insecure code patterns (e.g., hardcoded credentials, unvalidated inputs).
2. **Advisory Researcher Agent**: Equipped with a DuckDuckGo search tool to match identified packages against published vulnerabilities and CVEs.
3. **Remediation Specialist Agent**: Evaluates whether suggested upgrades introduce breaking changes and drafts concrete patch recommendations with exact version pins.

## Getting Started

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure you have your OpenAI API key set in your environment:
   ```bash
   export OPENAI_API_KEY='your-openai-api-key'
   ```
   (On Windows PowerShell, use `$env:OPENAI_API_KEY="your-openai-api-key"`)

3. Run the auditor script:
   ```bash
   python main.py
   ```
   By default, it will audit the provided `sample_project/` directory which contains deliberately vulnerable dependencies and insecure code patterns.

4. Check the generated `security_audit_report.md` for the results.

## Custom Audit
To audit a different directory, simply pass the path as an argument:
```bash
python main.py /path/to/your/project
```
