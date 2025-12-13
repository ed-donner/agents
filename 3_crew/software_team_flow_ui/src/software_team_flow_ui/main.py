from pydantic import BaseModel, Field
from typing import List
from crewai.flow import Flow, listen, start, router
from .crews.design_crew.design_crew import DesignCrew
from .crews.ui_crew.ui_crew import UiCrew
from .crews.code_crew.code_crew import CodeCrew
from .crews.zip_crew.zip_crew import ZipCrew
from dotenv import load_dotenv
import os

load_dotenv(override=True)  

OUTPUT_FOLDER = "./output/"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
APP_FOLDER = "./output/app"
os.makedirs(APP_FOLDER, exist_ok=True)
ZIP_FOLDER = "./output/zip"
os.makedirs(ZIP_FOLDER, exist_ok=True)
MODULES_FOLDER = "./output/app/modules"
os.makedirs(MODULES_FOLDER, exist_ok=True)
DESIGN_FILE = "./output/app/design/master_design.md"
APP_PATH = "./output/app/app.py"

class AppModules(BaseModel):
    module_name: str = Field("", description = "Module python file name")
    class_name: str = Field("", description = "Module class name")

class DesignState(BaseModel):
    requirements: str = Field("", description="Description of requirements")
    modules: List[AppModules] = Field(default_factory=list, description="List of modules")
    design: str = Field("", description="Result of design")
    success_e2e_flag: bool = False
    success_zip_flag: bool = False
    zip_retry_count: int = 0
    e2e_retry_count: int = 0

class AppFlow(Flow[DesignState]):
    @start()
    def prepare_design_inputs(self, crewai_trigger_payload: dict = None):
        print("Preparing app design")
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
            if "success_e2e_flag" in crewai_trigger_payload:
                self.state.success_e2e_flag = crewai_trigger_payload["success_e2e_flag"]
            if "success_zip_flag" in crewai_trigger_payload:
                self.state.success_zip_flag = crewai_trigger_payload["success_zip_flag"]
            if "retry_count" in crewai_trigger_payload:
                self.state.e2e_retry_count = crewai_trigger_payload["retry_count"]
            if "zip_retry_count" in crewai_trigger_payload:
                self.state.zip_retry_count = crewai_trigger_payload["zip_retry_count"]
        else:
            # Proper fallback defaults
            self.state.requirements = "No requirements provided"
            self.state.modules = []
            self.state.design = ""
            self.state.success_e2e_flag = False
            self.state.success_zip_flag = False
            self.state.e2e_retry_count = 0
            self.state.zip_retry_count = 0


    @listen(prepare_design_inputs)
    def generate_design(self):
        print("Generating designs...")
        modules_for_kickoff = [m.model_dump() for m in self.state.modules]
        result = DesignCrew().crew().kickoff(inputs={
            "requirements": self.state.requirements,
            "modules": modules_for_kickoff
        })

        print("Designs generated")
        self.state.design = result.raw

    @listen(generate_design)
    def generate_code(self):
        print("Generating Code...")
        modules_for_kickoff = [m.model_dump() for m in self.state.modules]

        for module in self.state.modules:
            CodeCrew().crew().kickoff(inputs={
                "modules": modules_for_kickoff,
                "module_name": module.module_name,
                "class_name": module.class_name,
                "design_file_path": DESIGN_FILE,
                "modules_folder": MODULES_FOLDER,
            })
            print(f"Code generated for {module.module_name}")

    @listen(generate_code)
    def generate_ui(self):
        print("Generating UI...")
        modules_for_kickoff = [m.model_dump() for m in self.state.modules]

        UiCrew().crew().kickoff(inputs={
            "modules": modules_for_kickoff,
            "design_file_path": DESIGN_FILE,
            "modules_folder": MODULES_FOLDER,
            "app_file_path": APP_PATH,
            "app_folder": APP_FOLDER
        })

        print("UI generation complete.")

    @listen("generate_ui")
    def zip_app(self):
        print("Zipping app...")
        result = ZipCrew().crew().kickoff(inputs={
            "zip_folder": ZIP_FOLDER,
            "app_folder": APP_FOLDER
        })
        raw = result.raw
        print(raw , f'RESULT PLEASE HAVE A LOOK {raw}')
        if isinstance(raw, bool):
            self.state.success_zip_flag = raw
        elif isinstance(raw, str):
            self.state.success_zip_flag = raw.strip().lower() == "true"
        else:
            self.state.success_zip_flag = bool(raw)

    @router(zip_app)
    def check_zip(self):
         return "zip_success" if self.state.success_zip_flag else "zip_fail"
    
    @listen('zip_success')
    def check_zip_success(self):
        print('App is zipped')

    @listen('zip_fail')
    def check_zip_fail(self):
        print('App is not zipped, trying again to zip')
        return 'zip_app'
        

def kickoff():
    requirements = """
    Web Page Language Validation System — Requirements
    1. URL Input
    - Accept a list of valid HTTPS URLs (e.g., https://www.pmi.com/).
    - Ignore or reject invalid URLs.
    2. HTML Fetching & Text Extraction
    - Fetch HTML content for each URL.
    - Extract visible text only (ignore scripts, styles, meta tags).
    - Handle network or parsing errors gracefully without stopping execution.
    3. Language Detection
    - Detect page language using a reliable library (e.g., langdetect, polyglot, langid).
    - Use library-based detection (not AI) for speed and efficiency.
    - Read the declared language from <html lang="xx">.
    - Compare detected language against the HTML lang attribute.
    4. Validation Rules
    For each page, store:
    - URL
    - Detected language
    - Declared language (<html lang="xx">)
    - Status:
    	✔️ Match, ❌ Mismatch, ⚠️ Error (network, parsing, or missing lang)
    5. Modules / UI Tabs (Gradio Blocks)
    - Dashboard / Summary
    	- Total URLs checked
    	- Percent language match
    	- Percent language mismatch
    	- Number of failed pages
    - Input
    	- Textbox for URL input
    	- Trigger validation on submission
    - Detailed Results
    	- Table showing:
    		- URL
    		- Detected language
    		- HTML lang
    		- Status
    6. Error Handling
    - Network or parsing errors must not stop the full run.
    - Failed URLs must include:
    	- Status: Error
    	- Reason (e.g., timeout, DNS failure, missing lang)
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
    app_flow.plot("My app flow")


def run_with_trigger():
    """
    Run the flow with trigger payload.
    """
    import json
    import sys
    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    app_flow = AppFlow()

    try:
        result = app_flow.kickoff({"crewai_trigger_payload": trigger_payload})
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the flow with trigger: {e}")

if __name__ == "__main__":
    kickoff()
    plot()