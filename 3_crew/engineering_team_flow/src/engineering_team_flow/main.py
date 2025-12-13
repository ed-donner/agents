#!/usr/bin/env python
from pydantic import BaseModel, Field
from typing import List
from crewai.flow import Flow, listen, start, router
from engineering_team_flow.crews.design_crew.design_crew import DesignCrew
from engineering_team_flow.crews.ui_crew.ui_crew import UiCrew
from engineering_team_flow.crews.code_crew.code_crew import CodeCrew
from engineering_team_flow.crews.e2e_crew.e2e_crew import E2ECrew
from dotenv import load_dotenv
import os
#print(os.getenv("SERPER_API_KEY"))
# from anthropic import Anthropic

# client = Anthropic(
#     api_key=os.getenv("ANTHROPIC_API_KEY"),
# )
# page = client.beta.models.list()
# page = page.data
# for model in page:
#     print(model.id)
# Load environment variables
load_dotenv(override=True)  # ensure .env keys override system vars

# Paths relative to project root (where main.py is executed from)
DESIGN_FILE_PATH = "./output/design/master_design.md"
OUTPUT_MODULES_PATH = "./output/modules"
OUTPUT_PATH = "./output/"
OUTPUT_APP_PATH = "./output/app.py"

class AppModules(BaseModel):
    module_name: str = Field("", description = "Module python file name")
    class_name: str = Field("", description = "Module class name")

class DesignState(BaseModel):
    requirements: str = Field("", description="Description of requirements")
    modules: List[AppModules] = Field(default_factory=list, description="List of modules")
    design: str = Field("", description="Result of design")
    success_flag: bool = False
    retry_count: int = 0


class AppFlow(Flow[DesignState]):
    @start()
    def prepare_design_inputs(self, crewai_trigger_payload: dict = None):
        print("Preparing app design")

        # Use trigger payload if available
        if crewai_trigger_payload:
            print("Using trigger payload:", crewai_trigger_payload)
            if "requirements" in crewai_trigger_payload:
                self.state.requirements = crewai_trigger_payload["requirements"]
            if "modules" in crewai_trigger_payload:
                self.state.modules = [
                    AppModules(**module_dict)
                    for module_dict in crewai_trigger_payload["modules"]
                ]
            if "design" in crewai_trigger_payload:
                self.state.design = crewai_trigger_payload["design"]
            if "success_flag" in crewai_trigger_payload:
                self.state.success_flag = crewai_trigger_payload["success_flag"]
            if "retry_count" in crewai_trigger_payload:
                self.state.retry_count = crewai_trigger_payload["retry_count"]
        else:
            # No payload at all → fallback defaults
            self.state.requirements = "No requirements provided"
            self.state.modules = []
            self.state.design = ""
            self.state.success_flag = False
            self.state.retry_count = 0

    @listen(prepare_design_inputs)
    def generate_design(self):
        print("Generating designs...")
        modules_for_kickoff = [
            module.model_dump() # Converts AppModules object to a dict
            for module in self.state.modules
        ]
        
        result = (
            DesignCrew()
            .crew()
            .kickoff(inputs={
                "requirements": self.state.requirements,
                "modules": modules_for_kickoff
            })
        )

        print("Designs generated")
        self.state.design = result.raw
    
    @listen(generate_design)
    def generate_code(self):
        
        print("Generating Code...")
        modules_for_kickoff = [
            module.model_dump() # Converts AppModules object to a dict
            for module in self.state.modules
        ]
        for module in self.state.modules:   
            CodeCrew().crew().kickoff(inputs={
                "modules": modules_for_kickoff,
                "module_name": module.module_name, 
                "class_name": module.class_name, 
                "design_file_path": DESIGN_FILE_PATH,
                "modules_folder": OUTPUT_MODULES_PATH, 
            })
            print(f"Code generated for {module.module_name} and tested")
    @listen(generate_code)
    def generate_ui(self):
        print("Generating ui....")
        modules_for_kickoff = [
            module.model_dump() # Converts AppModules object to a dict
            for module in self.state.modules
        ]
        UiCrew().crew().kickoff(inputs={
                "modules": modules_for_kickoff, 
                "design_file_path": DESIGN_FILE_PATH,
                "modules_folder": OUTPUT_MODULES_PATH,
                "app_file_path": OUTPUT_APP_PATH,
                "output_folder": OUTPUT_PATH
            })
        print("Completed UI...")

    @listen(generate_ui)
    def end2end_test(self):
        print("Testing e2e")
        result = E2ECrew().crew().kickoff(inputs={
            "design_file_path": DESIGN_FILE_PATH,
            "app_file_path": OUTPUT_APP_PATH,
            "modules_folder": OUTPUT_MODULES_PATH, 
            "output_folder": OUTPUT_PATH
        })
        # Convert result to boolean (result.raw might be string "True"/"False" or boolean)
        raw = result.raw
        print(raw, "RAW VALUE FROM E2E")
        if isinstance(raw, bool):
            self.state.success_flag = raw
        elif isinstance(raw, str):
            self.state.success_flag = raw.strip().lower() == "true"  # handles "true"/"false" strings safely
        else:
            self.state.success_flag = bool(raw)
    
    @router(end2end_test)
    def check(self):
        if self.state.success_flag:
            return 'success'
        else:
            return 'fail'
    @listen('success')
    def check_pass(self):
        print('App created')
    
    @listen('fail')
    def check_fail(self):
        print("App not created — sending task back to Code Team for rewrite...")
        self.state.retry_count += 1
        if self.state.retry_count > 3:
            print("❌ Too many retries. Stopping flow.")
            return "give_up"
        return "generate_code"
    

def kickoff():
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
    app_flow = AppFlow()
    app_flow.kickoff({
    "crewai_trigger_payload": {
        "requirements": requirements,
        "modules": modules, 
    }
})


def plot():
    app_flow = AppFlow()
    app_flow.plot()


def run_with_trigger():
    """
    Run the flow with trigger payload.
    """
    import json
    import sys

    # Get trigger payload from command line argument
    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    # Create flow and kickoff with trigger payload
    # The @start() methods will automatically receive crewai_trigger_payload parameter
    app_flow = AppFlow()

    try:
        result = app_flow.kickoff({"crewai_trigger_payload": trigger_payload})
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the flow with trigger: {e}")

if __name__ == "__main__":
    kickoff()
    #plot()
