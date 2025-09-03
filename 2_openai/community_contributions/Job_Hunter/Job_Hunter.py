import gradio as gr
from dotenv import load_dotenv
from job_searchManager import JobSearchManager
import PyPDF2
import io

load_dotenv(override=True)
print("🔧 [INIT] Environment variables loaded")
print("🔧 [INIT] Importing required modules...")
print("✅ [INIT] All modules imported successfully")


def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file"""
    print(f"📄 [PDF EXTRACTION] Starting PDF extraction for file: {pdf_file}")
    
    if pdf_file is None:
        print("❌ [PDF EXTRACTION] No file provided")
        return ""
    
    try:
        print(f"📂 [PDF EXTRACTION] Opening file: {pdf_file}")
        # Gradio returns the file path as a string, not bytes
        # Open the file from the path
        with open(pdf_file, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            print(f"📖 [PDF EXTRACTION] PDF has {len(pdf_reader.pages)} pages")
            
            # Extract text from all pages
            for i, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text += page_text + "\n"
                print(f"📄 [PDF EXTRACTION] Extracted {len(page_text)} characters from page {i+1}")
        
        total_chars = len(text.strip())
        print(f"✅ [PDF EXTRACTION] Successfully extracted {total_chars} total characters")
        return text.strip()
    except Exception as e:
        error_msg = f"Error reading PDF: {str(e)}"
        print(f"❌ [PDF EXTRACTION] {error_msg}")
        return error_msg


async def hunt_jobs(pdf_file, preferences):
    """Main job hunting function"""
    print("\n🚀 [JOB HUNT] Starting job hunt process")
    print(f"📁 [JOB HUNT] PDF file: {pdf_file}")
    print(f"🎯 [JOB HUNT] Preferences: {preferences}")
    
    if pdf_file is None:
        print("❌ [JOB HUNT] No PDF file uploaded")
        yield "❌ Please upload your resume (PDF format)"
        return
    
    if not preferences.strip():
        print("❌ [JOB HUNT] No preferences provided")
        yield "❌ Please specify your job preferences"
        return
    
    # Extract resume text from PDF
    print("📄 [JOB HUNT] Starting PDF text extraction...")
    yield "📄 Reading your resume..."
    resume_text = extract_text_from_pdf(pdf_file)
    
    if resume_text.startswith("Error"):
        print(f"❌ [JOB HUNT] PDF extraction failed: {resume_text}")
        yield resume_text
        return
    
    print(f"✅ [JOB HUNT] Resume text extracted successfully ({len(resume_text)} characters)")
    print(f"📝 [JOB HUNT] Resume preview: {resume_text[:200]}...")
    
    # Run the job search
    print("🔍 [JOB HUNT] Initializing JobSearchManager...")
    manager = JobSearchManager()
    
    print("🔄 [JOB HUNT] Starting job search manager process...")
    async for update in manager.run(resume_text, preferences):
        print(f"📊 [JOB HUNT] Manager update: {update}")
        yield update
    
    print("✅ [JOB HUNT] Job hunt process completed")


# Custom CSS for better styling
custom_css = """
.job-hunter-header {
    text-align: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 20px;
}

.upload-area {
    border: 2px dashed #667eea;
    border-radius: 10px;
    padding: 20px;
    text-align: center;
}

.preferences-area {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 15px;
}
"""

# Create the Gradio interface
with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue"), css=custom_css) as ui:
    
    # Header
    gr.HTML("""
        <div class="job-hunter-header">
            <h1>🎯 AI Job Hunter</h1>
            <p>Upload your resume and let AI find the perfect job opportunities for you!</p>
        </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            # Resume Upload Section
            gr.Markdown("### 📄 Upload Your Resume")
            resume_file = gr.File(
                label="Resume (PDF only)",
                file_types=[".pdf"],
                file_count="single",
                elem_classes="upload-area"
            )
            
            # Job Preferences Section
            gr.Markdown("### 🎯 Job Preferences")
            preferences = gr.Textbox(
                label="What kind of job are you looking for?",
                placeholder="e.g., Remote Python developer, Senior Data Scientist in NYC, Machine Learning Engineer at tech startup...",
                lines=4,
                elem_classes="preferences-area"
            )
            
            # Action Button
            hunt_button = gr.Button(
                "🚀 Start Job Hunt", 
                variant="primary", 
                size="lg"
            )
        
        with gr.Column(scale=1):
            # Results Section
            gr.Markdown("### 📊 Job Hunt Results")
            results = gr.Markdown(
                label="Progress & Results",
                value="Upload your resume and click 'Start Job Hunt' to begin...",
                height=400
            )
    
    # Footer
    gr.HTML("""
        <div style="text-align: center; margin-top: 20px; color: #666;">
            <p>💡 Tip: Be specific in your job preferences for better matches!</p>
        </div>
    """)
    
    # Event handlers
    print("⚙️  [UI SETUP] Configuring event handlers...")
    hunt_button.click(
        fn=hunt_jobs,
        inputs=[resume_file, preferences],
        outputs=results
    )
    
    # Allow Enter key in preferences to trigger search
    preferences.submit(
        fn=hunt_jobs,
        inputs=[resume_file, preferences], 
        outputs=results
    )
    print("✅ [UI SETUP] Event handlers configured successfully")

# Launch the app
if __name__ == "__main__":
    print("🚀 [APP STARTUP] Launching AI Job Hunter application...")
    print("🌐 [APP STARTUP] Server configuration:")
    print("   - Host: 0.0.0.0")
    print("   - Port: 7860")
    print("   - Browser: Auto-open enabled")
    print("   - Share: Disabled")
    print("🔗 [APP STARTUP] App will be available at: http://localhost:7860")
    
    ui.launch(
        inbrowser=True,
        share=False,
        server_name="0.0.0.0",
        server_port=7860
    )
    
    print("🛑 [APP SHUTDOWN] Application stopped")

