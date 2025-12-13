#!/usr/bin/env python
import warnings
from software_team_crew_hierarchical.crew import SoftwareTeamCrewHierarchical
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
        If below modules are requested try:
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

DESIGN_FILE_PATH = "/output/app/design/master_design.md"
OUTPUT_APP_FILE_PATH = "/output/app/app.py"
OUTPUT_MODULES_FOLDER_PATH = "/output/app/modules"
APP_FOLDER_PATH = "/output/app"
ZIP_FOLDER_PATH = "/output/zip"

def run():
    """
    Run the research crew.
    """
    inputs = {
        'requirements': requirements,
        'modules': modules,
        'design_file': DESIGN_FILE_PATH, 
        'app_file': OUTPUT_APP_FILE_PATH, 
        'modules_folder': OUTPUT_MODULES_FOLDER_PATH, 
        'app_folder': APP_FOLDER_PATH, 
        'zip_folder': ZIP_FOLDER_PATH, 
    }

    # Create and run the crew
    result = SoftwareTeamCrewHierarchical().crew().kickoff(inputs=inputs)

if __name__ == "__main__":
    run()
