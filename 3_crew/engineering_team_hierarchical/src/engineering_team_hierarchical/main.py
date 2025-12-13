#!/usr/bin/env python
import warnings
from engineering_team_hierarchical.crew import EngineeringTeamHierarchical
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
from dotenv import load_dotenv
load_dotenv(override=True) 

requirements = """
    Web Page Language Validation System — Short Requirements

    1. URL Input
    - Accept a list of HTTPS URLs (example: https://www.pmi.com/, https://www.pmi.com/markets/algeria/fr/overview/).
    - Process only valid HTTPS URLs.

    2. HTML Fetching & Text Extraction
    For each URL:
    - Fetch HTML content.
    - Extract visible text only (ignore scripts, styles, metas).
    - Handle network or parsing errors gracefully.

    3. Language Detection
    - Detect the language of the extracted text using a robust library (e.g., langdetect, polyglot, or langid).
    - Use a library-based approach (not AI) for efficiency, speed, and cost-effectiveness.
    - Read the declared language from <html lang="xx">.
    - Compare detected language vs HTML lang attribute.

    4. Validation Rules
    For each page record:
    - URL
    - Detected language
    - Declared lang attribute
    - Status:
        ✔️ Match
        ❌ Mismatch
        ⚠️ Error (network, parsing, or missing lang)

    5. Modules
        Keep all of them as Tabs in UI applying Gradio Blocks and Tabs
        A. Dashboard / Summary
            Display:
            - Total URLs checked
            - Percent language match
            - Percent language mismatch
            - Number of failed pages
        B. Input
            Accept URL input as textbox and process the URLs when submitted.
        C. Detailed Results
            - Results table with:
                - URL
                - Detected language
                - HTML lang
                - Status

    6. Error Handling
    - Network errors must not stop the full run.
    - Failed URLs must appear with:
        Status: Error
        Reason (timeout, DNS, missing lang, etc.)
    """
    
modules = [
    {"module_name": "dashboard", "class_name": "Dashboard"},
    {"module_name": "input", "class_name": "Input"},
    {"module_name": "results", "class_name": "Results"}
]

DESIGN_FILE_PATH = "/output/design/master_design.md"
OUTPUT_APP_PATH = "/output/app.py"
OUTPUT_MODULES_PATH = "/output/modules"
OUTPUT_PATH = "/output/"

def run_engineering_team():
    """
    Run the research crew.
    """
    inputs = {
        'requirements': requirements,
        'modules': modules,
        'design_markdown_file': DESIGN_FILE_PATH, 
        'app_file_path': OUTPUT_APP_PATH, 
        'modules_folder_path': OUTPUT_MODULES_PATH, 
        'app_folder': OUTPUT_PATH, 
    }

    # Create and run the crew
    result = EngineeringTeamHierarchical().crew().kickoff(inputs=inputs)


if __name__ == "__main__":
    run_engineering_team()
