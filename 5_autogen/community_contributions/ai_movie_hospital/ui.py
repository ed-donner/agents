import gradio as gr
import json
from main import MedicalPipeline
import os
import glob

output_folder = "./output" 
def clean_up_files():
    if os.path.exists(output_folder):
        for file_path in glob.glob(os.path.join(output_folder, "*")):
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted: {file_path}")
    else:
        print("Output folder does not exist.")
    for file_path in glob.glob("doctor*"):
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Deleted: {file_path}")

def format_evaluations(data):
    if "evaluations" not in data:
        return []
    return [[
        e['doctor'].get('doctor_name','N/A'),
        e['doctor'].get('speciality','N/A'),
        e.get('score',0),
        ", ".join(e.get('strengths',[])),
        e["doctor"].get('diagnosis')
    ] for e in data['evaluations']]

async def handle_diagnosis(symptoms):
    yield "", "", [], "",""
    if not symptoms.strip():
        yield "", "", [], "","### ⚠️ WarningPlease enter symptoms."

    pipeline = MedicalPipeline(symptoms)
    progress_log = ""
    final_content = None

    async for step in pipeline.run():
        progress_log += step.get("status", "") + "\n"
        if "content" in step and step["content"]:
            final_content = step["content"]
        yield "", "", [], progress_log
    if final_content:
        try:
            result_json_content = json.loads(final_content)
            chosen = result_json_content['chosen']
            win_info = f"### 🏆 Winner: Dr. {chosen['doctor']['doctor_name']}\n**Speciality:** {chosen['doctor']['speciality']} | **Score:** {chosen['evaluation']['score']}/10"
            win_text = chosen['doctor']['diagnosis']
            table_data = format_evaluations(result_json_content)
            yield win_info, win_text, table_data, progress_log
        except Exception as e:
            yield f"### ❌ Error\n{str(e)}", "The agent pipeline failed to complete.", [], progress_log

with gr.Blocks() as demo:
    gr.Markdown("# 🏥 AI Hospital Dashboard")
    gr.Markdown("Input patient symptoms to receive a multi-agent diagnostic evaluation. If you wish to play again refresh the browser")
    
    with gr.Row():
        symptoms_input = gr.Textbox(label="Patient Symptoms", placeholder="e.g. Chronic headache and sore throat...", lines=3)
        submit_btn = gr.Button("Analyze Diagnoses", variant="primary")
    with gr.Row():
        status_input = gr.Markdown(label="Patient Symptoms")
    with gr.Tabs():
        with gr.TabItem("🏆 Winning Doctor"):
            winner_header = gr.Markdown("")
            winner_body = gr.Markdown(label="Winning Full Diagnostic Report")
            
        with gr.TabItem("📊 All Diagnoses"):
            gr.Markdown("### Comparative Peer Review")
            diagnosis_table = gr.Dataframe(
                headers=["Doctor", "Speciality", "Score", "Key Strengths", "Diagnose"],
                datatype=["str", "str", "number", "str", "str"],
                wrap=True, 
                interactive=False
            )

    submit_btn.click(
        handle_diagnosis,
        inputs=symptoms_input,
        outputs=[winner_header, winner_body, diagnosis_table, status_input]
    )

if __name__ == "__main__":
    clean_up_files() 
    demo.launch(theme=gr.themes.Soft())