from research_manager_agent import run_research
import gradio as gr
import re


#functions for gradio

#email functions
def trigger_email(email):
    return f"EMAIL_REPORT, Email address: {email}"

def show_email_fields():
    return gr.update(visible=True,interactive=True), gr.update(visible=True), gr.update(visible=True,interactive=True)

def validate_email(email):
    "Validates an email address using a regular expression."
    
    if not email:
        return "Email cannot be empty."
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if re.match(pattern, email):
        return "Valid email address."
    else:
        return "Invalid email address format."

#main function
#first run
async def run_initial(company: str, industry: str, query: str):

    # Validation
    if not company or not company.strip():
        raise gr.Error("Please enter a company name")
    if not industry or not industry.strip():
        raise gr.Error("Please enter an industry")
    if not query or not query.strip():
        raise gr.Error("Please enter a research query")

    async for chunk in run_research(company, industry, query, None, None):
        yield chunk

#feedback run
async def run_feedback(company: str, industry: str, query: str, feedback: str):
    # Validation
    if not feedback or not feedback.strip():
        raise gr.Error("Please enter your feedback")

    async for chunk in run_research(company, industry, query, feedback, None):
        yield chunk

#email handoff run
async def run_email(company: str, industry: str, query: str, feedback: str, email_trigger: str):
    async for chunk in run_research(company, industry, query, feedback, email_trigger):
        yield chunk

# final run and gradio
import gradio as gr

with gr.Blocks(theme=gr.themes.Ocean()) as ui:
    gr.Markdown("Deep Research for Companies")
    gr.Markdown("Generate comprehensive company research reports with AI-powered analysis")
    
    with gr.Row():
        with gr.Column(scale=1):
            org_textbox = gr.Textbox(label="Organisation Name",placeholder="e.g. ComplAI",info="The company you want to research")
            industry_textbox = gr.Textbox(label="Industry", placeholder="e.g. Finance, Healthcare, SaaS",info="Primary industry or sector")
            query_textbox = gr.Textbox(label="Research Topic",placeholder="e.g. Analyze competitor pricing strategies",lines=3,info="What specific aspect would you like to research?")
            
            with gr.Row():
                run_button = gr.Button("Start Research", variant="primary", size="lg")

        with gr.Column(scale=1):
            feedback_textbox = gr.Textbox(label="Feedback", placeholder="e.g. Can you provide more information on...?",lines=3,info="Provide feedback to improve the research")
            email_trigger_textbox = gr.Textbox(label="Email trigger", visible=False)
            feedback_button = gr.Button("Provide Feedback", variant="primary",scale=1)
            send_button = gr.Button("Email me the report", variant ="secondary",scale=1)
            with gr.Column(scale=1):
                email_address = gr.Textbox(label="Email address:",type="email",visible=False,interactive=True)
                email_validation = gr.Markdown(visible=False)
                confirm_send_button = gr.Button("Go, please send!", variant ="primary",visible=False)
        
        with gr.Column(scale=2):
            report = gr.Markdown(label="Research Report",value="Your research report will appear here...",height=600)
    
    # Event handlers
    run_button.click(fn=run_initial, inputs=[org_textbox, industry_textbox, query_textbox], outputs=report, show_progress=True)
    feedback_button.click(fn=run_feedback, inputs=[org_textbox, industry_textbox, query_textbox, feedback_textbox], outputs=report, show_progress=True)
    send_button.click(fn=show_email_fields,inputs=[],outputs=[email_address, email_validation, confirm_send_button])
    confirm_send_button.click(fn=validate_email, inputs=email_address, outputs=email_validation).then(fn=trigger_email, inputs=email_address, outputs=email_trigger_textbox).then(
    fn=run_email, inputs=[org_textbox, industry_textbox, query_textbox, feedback_textbox, email_trigger_textbox], outputs=report)
        
    gr.ClearButton(components=[org_textbox,industry_textbox,query_textbox,feedback_textbox,report,email_address],value="Clear all fields")

ui.launch(inbrowser=True, share=False)

