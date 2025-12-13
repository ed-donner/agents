import gradio as gr
import os
from src.software_team_crew_hierarchical.crew import SoftwareTeamCrewHierarchical

OUTPUT_FOLDER_PATH = "/output"
os.makedirs(OUTPUT_FOLDER_PATH, exist_ok=True)
APP_FOLDER_PATH = "/output/app"
os.makedirs(APP_FOLDER_PATH, exist_ok=True)
OUTPUT_MODULES_FOLDER_PATH = "/output/app/modules"
os.makedirs(OUTPUT_MODULES_FOLDER_PATH, exist_ok=True)
ZIP_FOLDER_PATH = "/output/zip"
os.makedirs(ZIP_FOLDER_PATH, exist_ok=True)
OUTPUT_APP_FILE_PATH = "/output/app/app.py"
DESIGN_FILE_PATH = "/output/app/design/master_design.md"
OUTPUT_ZIP_PATH = "./output/zip/app.zip"

def run_flow(requirements, modules_text):
    # Prepare modules
    cleaned = modules_text.replace("\n", ",").replace(" ", "")
    modules = [{"module_name": m.lower(), "class_name": m.capitalize()} 
               for m in cleaned.split(",") if m.strip()]

    payload = {
        'requirements': requirements,
        'modules': modules,
         'requirements': requirements,
        'modules': modules,
        'design_file': DESIGN_FILE_PATH, 
        'app_file': OUTPUT_APP_FILE_PATH, 
        'modules_folder': OUTPUT_MODULES_FOLDER_PATH, 
        'app_folder': APP_FOLDER_PATH, 
        'zip_folder': ZIP_FOLDER_PATH, 
    }

    # Run AppFlow
    try:
        flow = SoftwareTeamCrewHierarchical().crew()
        flow.kickoff(inputs=payload)
       
    except Exception as e:
        return None, f"❌ Error during flow execution:\n{str(e)}"

    if not os.path.exists(OUTPUT_ZIP_PATH):
        return None, "❌ No ZIP file found in output folder."

    return OUTPUT_ZIP_PATH, "✅ App generated successfully!"


with gr.Blocks() as demo:
    gr.Markdown("# 🚀 Engineering Team Flow UI")
    gr.Markdown("Generate complete applications using CrewAI engineering teams.")

    requirements = gr.Textbox(label="Requirements", placeholder="Paste full project requirements here...", lines=15)
    modules = gr.Textbox(label="Modules (Module Name 1, Module Name 2)", placeholder="Dashboard, Input, Results", lines=6)
    run_button = gr.Button("Run Generation")
    result_message = gr.Markdown("")
    result_zip = gr.File(label="Download app.zip")

    run_button.click(
        fn=run_flow,
        inputs=[requirements, modules],
        outputs=[result_zip, result_message]
        # No show_progress needed, default spinner on button
    )

demo.launch()
