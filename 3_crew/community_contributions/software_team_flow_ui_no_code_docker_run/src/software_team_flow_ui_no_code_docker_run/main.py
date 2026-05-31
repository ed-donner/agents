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

OUTPUT_FOLDER_PATH = "./output/"
os.makedirs(OUTPUT_FOLDER_PATH, exist_ok=True)
APP_FOLDER_PATH = "./output/app"
os.makedirs(APP_FOLDER_PATH, exist_ok=True)
MODULES_FOLDER_PATH = "./output/app/modules"
os.makedirs(MODULES_FOLDER_PATH, exist_ok=True)
ZIP_FOLDER_PATH = "./output/zip"
os.makedirs(ZIP_FOLDER_PATH, exist_ok=True)
DESIGN_FILE_PATH = "./output/app/design/master_design.md"
APP_FILE_PATH = "./output/app/app.py"

class AppModules(BaseModel):
    module_name: str = Field("", description = "Module python file name")
    class_name: str = Field("", description = "Module class name")

class DesignState(BaseModel):
    requirements: str = Field("", description="Description of requirements")
    modules: List[AppModules] = Field(default_factory=list, description="List of modules")
    design: str = Field("", description="Result of design")
    success_e2e_flag: bool = False
    success_zip_flag: bool = False

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
 
        else:
            # Proper fallback defaults
            self.state.requirements = "No requirements provided"
            self.state.modules = []
            self.state.design = ""
            self.state.success_e2e_flag = False
            self.state.success_zip_flag = False

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
                "design_file_path": DESIGN_FILE_PATH,
                "modules_folder": MODULES_FOLDER_PATH,
            })
            print(f"Code generated for {module.module_name}")

    @listen(generate_code)
    def generate_ui(self):
        print("Generating UI...")
        modules_for_kickoff = [m.model_dump() for m in self.state.modules]

        UiCrew().crew().kickoff(inputs={
            "modules": modules_for_kickoff,
            "design_file_path": DESIGN_FILE_PATH,
            "modules_folder": MODULES_FOLDER_PATH,
            "app_file_path": APP_FILE_PATH,
            "app_folder": APP_FOLDER_PATH
        })

        print("UI generation complete.")

    @listen("generate_ui")
    def zip_app(self):
        print("Zipping app...")
        result = ZipCrew().crew().kickoff(inputs={
            "zip_folder": ZIP_FOLDER_PATH,
            "app_folder": APP_FOLDER_PATH
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
    Frontend (Gradio / Python)
	Inputs
		URL Input: 
			Textbox accepting a comma-separated list of valid HTTPS URLs (e.g., https://www.pmi.com/, https://www.pmi.com/markets/algeria/en). Invalid URLs must be rejected or ignored.
		Modules Input: 
			Textbox for comma-separated module names used as UI tabs.
			Example modules/tabs:
				Dashboard: Total URLs checked, % language match/mismatch, number of failed pages.
				Input: URL input + submit button.
				Results: Table output.
	Output Table Columns
		checked_url
		detected_language
		declared_language (<html lang="xx">)
		Status → ✔️ Match | ❌ Mismatch | ⚠️ Error (network/parsing/missing lang)
	UI Layout
		Each module name corresponds to a Gradio tab inside a Blocks interface.
Backend (Python)
	HTML Fetching & Extraction
		Fetch each URL’s HTML.
		Extract visible text only (ignore scripts, styles, meta tags).
		Return errors without interrupting the full execution.
	Language Detection
		Detect language using a fast, library-based detector (e.g., langdetect, langid, polyglot).
		Read declared language from <html lang="xx">.
		Compare detected vs. declared language and assign status.
	Error Handling
		Network or parsing failures must not stop execution.
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