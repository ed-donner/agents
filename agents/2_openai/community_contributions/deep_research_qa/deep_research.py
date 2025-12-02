import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager, ResearchManagerAgent
from agents import Runner, trace, gen_trace_id

load_dotenv(override=True)

async def handle_query_submission(query: str, current_state: dict):
    """Handle initial query submission - generate clarifying questions with progress"""
    if not query.strip():
        return "Please enter a research query.", gr.update(visible=False), gr.update(visible=False), current_state
    
    try:
        # Show progress
        progress_update = "🔄 **Generating clarifying questions...**\n\nPlease wait while our AI analyzes your query and creates focused questions to improve the research quality."
        
        research_manager = ResearchManager()
        result = await research_manager.run_with_clarification(query)
        
        # Format questions for display
        questions_text = "\n\n".join([f"**{i+1}.** {q}" for i, q in enumerate(result["questions"])])
        display_text = f"**✅ Clarifying Questions Generated:**\n\n{questions_text}\n\n**Please answer these questions to help focus the research:**"
        
        # Update state with query and questions
        new_state = {
            "query": query,
            "questions": result["questions"],
            "trace_id": result["trace_id"]
        }
        
        return display_text, gr.update(visible=True), gr.update(visible=True), new_state
        
    except Exception as e:
        return f"❌ Error generating clarifying questions: {str(e)}", gr.update(visible=False), gr.update(visible=False), current_state

async def handle_research_with_answers(answers: str, current_state: dict, email_address: str, send_email: bool):
    """Handle research execution with clarification answers with progress updates"""
    if not current_state.get("query"):
        return "Please start by entering a research query first.", current_state
    
    if not answers.strip():
        return "Please provide answers to the clarifying questions.", current_state
    
    try:
        # Show progress
        progress_message = f"""🔄 **Research in Progress...**

**Original Query:** {current_state['query']}

**Status:** Processing your clarifications and starting comprehensive research...

⏳ This may take 1-2 minutes. We're:
1. Planning search strategy
2. Conducting multiple web searches  
3. Writing initial report
4. Evaluating quality
5. Optimizing if needed
6. Preparing final delivery"""
        
        # Use the enhanced manager with email settings
        from research_manager import create_custom_research_agent
        
        # Parse answers (one per line)
        answer_list = [line.strip() for line in answers.split('\n') if line.strip()]
        
        # Format the query with clarifications
        clarified_query = f"""Original query: {current_state['query']}

Clarifications provided:
{chr(10).join([f"{i+1}. {answer}" for i, answer in enumerate(answer_list)])}

Please use these clarifications to focus and refine the research approach."""
        
        # Create custom agent with email settings
        custom_agent = create_custom_research_agent(
            email_address=email_address if send_email else None,
            send_email=send_email
        )
        
        # Run research with custom agent
        trace_id = gen_trace_id()
        with trace("Focused Research with Clarifications", trace_id=trace_id):
            result = await Runner.run(
                custom_agent,
                f"Research Query: {clarified_query}"
            )
        
        email_status = ""
        if send_email and email_address:
            email_status = f"\n📧 **Email sent to:** {email_address}"
        elif send_email and not email_address:
            email_status = f"\n⚠️ **Email not sent:** No email address provided"
        else:
            email_status = f"\n📄 **Report generated:** Email sending disabled"
        
        final_report = f"""**✅ Research Complete!**

**🔗 Trace ID:** {trace_id}

**Original Query:** {current_state['query']}

**📊 Enhanced Final Report:**

{result.final_output}

{email_status}

---
*Research completed using enhanced AI system with quality assurance and your clarifications.*"""
        
        return final_report, current_state
        
    except Exception as e:
        return f"❌ Error during research: {str(e)}", current_state

async def run_direct_research(query: str, email_address: str = "", send_email: bool = False):
    """Run research directly without clarification using the new agent-based system"""
    if not query.strip():
        return "Please enter a research query."
    
    try:
        trace_id = gen_trace_id()
        with trace("Enhanced Research Manager", trace_id=trace_id):
            print(f"🔗 Starting enhanced research with trace: {trace_id}")
            
            # Import the function here to avoid circular imports
            from research_manager import create_custom_research_agent
            
            # Create agent with email settings
            custom_agent = create_custom_research_agent(
                email_address=email_address if send_email else None,
                send_email=send_email
            )
            
            # Use the custom agent
            result = await Runner.run(
                custom_agent,
                f"Research Query: {query}"
            )
            
            email_status = ""
            if send_email and email_address:
                email_status = f"\n📧 **Email sent to:** {email_address}"
            elif send_email and not email_address:
                email_status = f"\n⚠️ **Email not sent:** No email address provided"
            else:
                email_status = f"\n📄 **Report generated:** Email sending disabled"
            
            return f"""**✅ Research Complete!**

**🔗 Trace ID:** {trace_id}
**👀 View Detailed Trace:** https://platform.openai.com/traces/trace?trace_id={trace_id}

**📊 Enhanced Research Report with Quality Assurance:**

{result.final_output}

{email_status}

---
*🤖 This research was conducted using our enhanced agent-based system with automatic quality evaluation and optimization. Check the trace link above to see the full workflow including planning, searching, writing, evaluation, and optimization steps.*"""
             
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error details: {error_details}")
        return f"❌ Error during research: {str(e)}\n\nPlease try the Legacy Quick Research option if this persists."

async def run_legacy_research(query: str, email_address: str, send_email: bool):
    """Run research using the original ResearchManager class with email options"""
    if not query.strip():
        return "Please enter a research query."
    
    try:
        # Use the enhanced system but call it "legacy" for the user
        trace_id = gen_trace_id()
        with trace("Quick Research", trace_id=trace_id):
            from research_manager import create_custom_research_agent
            
            # Create agent with email settings
            custom_agent = create_custom_research_agent(
                email_address=email_address if send_email else None,
                send_email=send_email
            )
            
            result = await Runner.run(
                custom_agent,
                f"Research Query: {query}"
            )
            
            email_status = ""
            if send_email and email_address:
                email_status = f"\n📧 **Email sent to:** {email_address}"
            elif send_email and not email_address:
                email_status = f"\n⚠️ **Email not sent:** No email address provided"
            else:
                email_status = f"\n📄 **Report generated:** Email sending disabled"
            
            return f"""**✅ Quick Research Complete!**

**🔗 Trace ID:** {trace_id}

**📊 Research Report:**

{result.final_output}

{email_status}

---
*Quick research completed successfully.*"""
            
    except Exception as e:
        return f"❌ Error during research: {str(e)}"

async def run_enhanced_research_with_progress(query: str, email_address: str = "", send_email: bool = False):
    """Run enhanced research with real-time step-by-step progress updates"""
    if not query.strip():
        yield "Please enter a research query."
        return
    
    # Import the new progress function
    from research_manager import run_research_with_progress
    
    try:
        # Collect all progress updates
        progress_updates = []
        async for update in run_research_with_progress(
            query=query,
            email_address=email_address if send_email else None,
            send_email=send_email
        ):
            progress_updates.append(update)
            # Return current progress to update the UI
            yield "\n\n".join(progress_updates)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error details: {error_details}")
        yield f"❌ Error during research: {str(e)}\n\nPlease try a different approach if this persists."

async def run_clarified_research_with_progress(answers: str, current_state: dict, email_address: str, send_email: bool):
    """Handle research execution with clarification answers and real-time progress"""
    if not current_state.get("query"):
        yield "Please start by entering a research query first."
        return
    
    if not answers.strip():
        yield "Please provide answers to the clarifying questions."
        return
    
    # Import the new progress function
    from research_manager import run_research_with_progress
    
    try:
        # Parse answers (one per line)
        answer_list = [line.strip() for line in answers.split('\n') if line.strip()]
        
        # Format the query with clarifications
        clarified_query = f"""Original query: {current_state['query']}

Clarifications provided:
{chr(10).join([f"{i+1}. {answer}" for i, answer in enumerate(answer_list)])}

Please use these clarifications to focus and refine the research approach."""
        
        # Show initial setup
        yield f"🚀 **Starting Focused Research with Clarifications**\n\n**Original Query:** {current_state['query']}\n\n**Your Clarifications:**\n{chr(10).join([f'• {answer}' for answer in answer_list if answer])}\n\n---\n\n"
        
        # Collect all progress updates
        progress_updates = [f"🚀 **Starting Focused Research with Clarifications**\n\n**Original Query:** {current_state['query']}\n\n**Your Clarifications:**\n{chr(10).join([f'• {answer}' for answer in answer_list if answer])}\n\n---\n\n"]
        
        async for update in run_research_with_progress(
            query=clarified_query,
            email_address=email_address if send_email else None,
            send_email=send_email
        ):
            progress_updates.append(update)
            # Return current progress to update the UI
            yield "\n\n".join(progress_updates)
        
    except Exception as e:
        yield f"❌ Error during research: {str(e)}"

# Custom CSS for better readability and contrast
custom_css = """
/* Main container improvements */
.gradio-container {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

/* Ensure good contrast for all text inputs */
.gradio-container input[type="text"],
.gradio-container textarea {
    background-color: #4b5563 !important;
    border: 2px solid #6b7280 !important;
    border-radius: 8px !important;
    padding: 12px !important;
    font-size: 14px !important;
    color: #f9fafb !important;
    font-weight: 400 !important;
    line-height: 1.5 !important;
    transition: border-color 0.2s ease !important;
}

.gradio-container input[type="text"]:focus,
.gradio-container textarea:focus {
    border-color: #60a5fa !important;
    box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2) !important;
    outline: none !important;
}

/* Placeholder styling for all inputs */
.gradio-container input[type="text"]::placeholder,
.gradio-container textarea::placeholder {
    color: #9ca3af !important;
    opacity: 0.8 !important;
    font-style: italic !important;
}

/* Simple button styling with good contrast */
.gradio-container button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    padding: 8px 16px !important;
    border: 2px solid transparent !important;
    transition: all 0.2s ease !important;
}

/* Primary buttons */
button[variant="primary"] {
    background-color: #3b82f6 !important;
    color: white !important;
    border-color: #3b82f6 !important;
}

button[variant="primary"]:hover {
    background-color: #2563eb !important;
    border-color: #2563eb !important;
}

/* Secondary buttons */
button[variant="secondary"] {
    background-color: #f8fafc !important;
    color: #374151 !important;
    border-color: #d1d5db !important;
}

button[variant="secondary"]:hover {
    background-color: #f1f5f9 !important;
    border-color: #9ca3af !important;
}

/* Theme-adaptive section styling */
.clarification-section {
    border: 2px solid var(--border-color-primary, #e5e7eb) !important;
    border-radius: 12px !important;
    padding: 20px !important;
    margin: 16px 0 !important;
    background-color: var(--background-fill-secondary, #f8fafc) !important;
    color: var(--body-text-color, #374151) !important;
}

.clarification-section * {
    color: inherit !important;
}

.clarification-section h1, 
.clarification-section h2, 
.clarification-section h3 {
    color: inherit !important;
    font-weight: 600 !important;
}

/* Dark theme specific styles for clarification section */
.gradio-container.dark .clarification-section {
    background-color: #374151 !important;
    border-color: #4b5563 !important;
    color: #ffffff !important;
}

.gradio-container.dark .clarification-section * {
    color: #ffffff !important;
}

.gradio-container.dark .clarification-section h1,
.gradio-container.dark .clarification-section h2,
.gradio-container.dark .clarification-section h3 {
    color: #ffffff !important;
}

/* Clean answer box */
.answer-textbox {
    background-color: #4b5563 !important;
    border: 2px solid #6b7280 !important;
    border-radius: 8px !important;
    padding: 12px !important;
    color: #d1d5db !important;
    line-height: 1.5 !important;
}

.answer-textbox:focus {
    border-color: #60a5fa !important;
    box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2) !important;
}

/* Target the actual textarea element inside answer-textbox */
.answer-textbox textarea {
    background-color: #4b5563 !important;
    color: #f9fafb !important;
    border: 2px solid #6b7280 !important;
    border-radius: 8px !important;
    padding: 12px !important;
    font-size: 14px !important;
    font-weight: 400 !important;
    line-height: 1.5 !important;
}

.answer-textbox textarea:focus {
    border-color: #60a5fa !important;
    box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2) !important;
}

/* Make sure placeholder text is visible on dark background */
.answer-textbox textarea::placeholder {
    color: #9ca3af !important;
    opacity: 0.8 !important;
    font-style: italic !important;
}

/* Make all textareas have proper white text */
.gradio-container textarea {
    color: #f9fafb !important;
}

.answer-textbox::placeholder {
    color: #9ca3af !important;
    opacity: 0.9 !important;
}

/* Theme-adaptive results display */
.results-display {
    border: 2px solid var(--border-color-primary, #e5e7eb) !important;
    border-radius: 8px !important;
    padding: 16px !important;
    margin: 12px 0 !important;
    line-height: 1.6 !important;
    background-color: var(--background-fill-secondary, #f8fafc) !important;
    color: var(--body-text-color, #374151) !important;
}

/* Make sure markdown in results display adapts to theme */
.results-display * {
    color: inherit !important;
}

/* Dark theme specific styles */
.gradio-container.dark .results-display {
    background-color: #374151 !important;
    border-color: #4b5563 !important;
    color: #ffffff !important;
}

.gradio-container.dark .results-display * {
    color: #ffffff !important;
}

/* Style links in results display for visibility */
.results-display a {
    color: #60a5fa !important;
    text-decoration: underline !important;
}

.results-display a:hover {
    color: #93c5fd !important;
}

/* Accordion improvements */
.gradio-accordion {
    border: 1px solid #e5e7eb !important;
    border-radius: 8px !important;
    margin: 8px 0 !important;
}

/* Status indicators with good contrast */
.status-success {
    color: #059669 !important;
    font-weight: 500 !important;
}

.status-info {
    color: #0369a1 !important;
    font-weight: 500 !important;
}

.status-warning {
    color: #d97706 !important;
    font-weight: 500 !important;
}

/* Theme-adaptive headers */
h1, h2, h3 {
    color: var(--body-text-color) !important;
    font-weight: 600 !important;
}

/* Fallback for when CSS variables aren't available */
@media (prefers-color-scheme: dark) {
    h1, h2, h3 {
        color: #ffffff !important;
    }
}

@media (prefers-color-scheme: light) {
    h1, h2, h3 {
        color: #1f2937 !important;
    }
}

/* Specific overrides for Gradio themes */
.gradio-container.dark h1,
.gradio-container.dark h2,
.gradio-container.dark h3 {
    color: #ffffff !important;
}

.gradio-container.light h1,
.gradio-container.light h2,
.gradio-container.light h3 {
    color: #1f2937 !important;
}

/* Remove unnecessary gradients and shadows for simplicity */
* {
    box-shadow: none !important;
}

/* Keep only essential shadows for depth */
.gradio-container button,
.gradio-container input,
.gradio-container textarea {
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
}

.gradio-container button:hover {
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15) !important;
}
"""

with gr.Blocks(theme=gr.themes.Default(primary_hue="blue"), css=custom_css) as ui:
    gr.Markdown("# 🔍 Deep Research Assistant")
    gr.Markdown("**Ask a research question and get comprehensive, AI-powered analysis with quality assurance.**")
    
    # State to track the conversation
    state = gr.State({})
    
    # Main Research Configuration Block
    with gr.Column():
        query_textbox = gr.Textbox(
            label="Research Query", 
            placeholder="What would you like to research? (e.g., 'Latest developments in renewable energy')",
            lines=2,
            elem_classes=["main-input"]
        )
        
        # Email Configuration (part of main block)
        with gr.Accordion("📧 Email Configuration (Optional)", open=False):
            gr.Markdown("**Configure email delivery for your research reports**")
            
            with gr.Row():
                with gr.Column(scale=3):
                    email_textbox = gr.Textbox(
                        label="Email Address", 
                        placeholder="your.email@example.com",
                        lines=1
                    )
                with gr.Column(scale=1):
                    send_email_checkbox = gr.Checkbox(
                        label="Send Email", 
                        value=False,
                        info="Check to receive the report via email"
                    )
            
            gr.Markdown("*This email setting will be used for any research option you choose below.*")
        
        # Start Research Button (below the main configuration)
        submit_button = gr.Button("🚀 Start Research", variant="primary", size="lg")
    
    # Output area for questions and results
    output_area = gr.Markdown(
        label="Research Progress", 
        elem_classes=["results-display"],
        value="👋 Enter your research query above and configure email settings if desired, then click Start Research!"
    )
    
    # Clarification answers section (initially hidden)
    with gr.Column(visible=False, elem_classes=["clarification-section"]) as clarification_row:
        gr.Markdown("### 💭 Help us focus your research")
        gr.Markdown("Please answer these questions to get more targeted results:")
        
        answers_textbox = gr.Textbox(
            label="Your Answers", 
            placeholder="Answer each question on a separate line...\n\nExample:\n1. I'm interested in solar and wind technologies\n2. I need technical details and market analysis\n3. This is for a business presentation",
            lines=6,
            elem_classes=["answer-textbox"],
            show_label=True
        )
        
        research_button = gr.Button(
            "🔍 Run Focused Research", 
            variant="primary", 
            visible=False, 
            size="lg"
        )
    
    # Research options
    with gr.Accordion("🤖 Enhanced Research (Recommended)", open=False):
        gr.Markdown("""
        **New AI-powered research system featuring:**
        
        ✅ **Quality Evaluation** - Each report is automatically assessed  
        ✅ **Smart Optimization** - Reports are improved if needed  
        ✅ **Comprehensive Analysis** - Multiple search strategies  
        
        *Delivers higher quality research through AI quality assurance.*
        """)
        enhanced_button = gr.Button("🤖 Enhanced Research", variant="primary")
    
    with gr.Accordion("⚡ Quick Research (Legacy)", open=False):
        gr.Markdown("*Faster research using the original system - good for quick queries.*")
        direct_button = gr.Button("⚡ Quick Research", variant="secondary")
    
    # Event handlers
    submit_button.click(
        fn=handle_query_submission,
        inputs=[query_textbox, state],
        outputs=[output_area, clarification_row, research_button, state]
    )
    
    query_textbox.submit(
        fn=handle_query_submission,
        inputs=[query_textbox, state],
        outputs=[output_area, clarification_row, research_button, state]
    )
    
    research_button.click(
        fn=run_clarified_research_with_progress,
        inputs=[answers_textbox, state, email_textbox, send_email_checkbox],
        outputs=[output_area]
    )
    
    answers_textbox.submit(
        fn=run_clarified_research_with_progress,
        inputs=[answers_textbox, state, email_textbox, send_email_checkbox],
        outputs=[output_area]
    )
    
    enhanced_button.click(
        fn=run_enhanced_research_with_progress,
        inputs=[query_textbox, email_textbox, send_email_checkbox],
        outputs=[output_area]
    )
    
    direct_button.click(
        fn=run_legacy_research,
        inputs=[query_textbox, email_textbox, send_email_checkbox],
        outputs=[output_area]
    )

if __name__ == "__main__":
    ui.launch(inbrowser=True)

