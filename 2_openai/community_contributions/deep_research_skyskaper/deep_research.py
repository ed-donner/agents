import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager
import re
from typing import Dict, List

load_dotenv(override=True)

# Define response tuning templates for specific question types
RESPONSE_TEMPLATES = {
    "environmental_impact": {
        "patterns": [
            r"environmental.*impact.*skyscrapers?",
            r"skyscrapers?.*environment",
            r"green.*building.*tall.*buildings?"
        ],
        "guidance": "Focus on: 1) Carbon footprint during construction 2) Energy efficiency in operation 3) Urban heat island effects 4) Materials sustainability 5) Water management systems 6) Lifecycle assessment"
    },
    "urban_planning": {
        "patterns": [
            r"urban.*planning.*tall.*buildings?",
            r"zoning.*skyscrapers?",
            r"city.*planning.*high.*rises?",
            r"density.*regulations.*tall.*buildings?"
        ],
        "guidance": "Focus on: 1) Zoning laws and FAR ratios 2) Transportation infrastructure 3) Shadow studies and wind effects 4) Mixed-use development 5) Historical preservation vs modern development 6) Smart city integration"
    },
    "engineering_breakthroughs": {
        "patterns": [
            r"engineering.*breakthroughs?.*megatall",
            r"megatall.*buildings?.*technology",
            r"Jeddah.*Tower.*engineering",
            r"super.*tall.*construction.*advances?"
        ],
        "guidance": "Focus on: 1) Advanced materials (UHPC, composite systems) 2) Wind engineering solutions 3) Elevator technologies (multi-elevator systems) 4) Foundation engineering 5) Seismic design innovations 6) Construction automation and robotics"
    }
}

class TunedResearchManager:
    def __init__(self):
        self.research_manager = ResearchManager()
        
    def _categorize_question(self, query: str) -> Dict:
        """Categorize the question and return appropriate tuning parameters"""
        query_lower = query.lower()
        
        for category, data in RESPONSE_TEMPLATES.items():
            for pattern in data["patterns"]:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    return {
                        "category": category,
                        "guidance": data["guidance"],
                        "original_query": query
                    }
        
        # Default response for uncategorized questions
        return {
            "category": "general",
            "guidance": "Provide comprehensive research on the topic",
            "original_query": query
        }
    
    async def run(self, query: str):
        # Categorize the question
        tuned_params = self._categorize_question(query)
        
        # Prepare enhanced query with guidance
        enhanced_query = f"""
        Original Question: {tuned_params['original_query']}
        
        Research Focus Guidance:
        {tuned_params['guidance']}
        
        Please provide a thorough, well-structured research report addressing these specific aspects.
        Include data, examples, and current best practices where applicable.
        """
        
        # Add category-specific introduction
        category_intros = {
            "environmental_impact": "## Research Report: Environmental Impacts of Skyscrapers\n\n",
            "urban_planning": "## Research Report: Urban Planning and Tall Buildings\n\n",
            "engineering_breakthroughs": "## Research Report: Engineering Innovations for Megatall Buildings\n\n",
            "general": "## Research Report\n\n"
        }
        
        intro = category_intros.get(tuned_params["category"], "## Research Report\n\n")
        yield intro
        
        # Run the research with enhanced query
        async for chunk in self.research_manager.run(enhanced_query):
            yield chunk


async def run(query: str):
    async for chunk in TunedResearchManager().run(query):
        yield chunk


# Enhanced UI with better visual feedback
with gr.Blocks(theme=gr.themes.Default(
    primary_hue="sky",
    secondary_hue="blue",
    font=["Helvetica", "Arial", "sans-serif"]
)) as ui:
    
    gr.Markdown("""
    # 🏙️ Skyscraper Research Specialist
    
    *Specialized in environmental impacts, urban planning, and engineering innovations for tall buildings*
    """)
    
    with gr.Row():
        with gr.Column(scale=3):
            query_textbox = gr.Textbox(
                label="Research Topic",
                placeholder="Enter your question about skyscrapers, urban planning, or building engineering...",
                lines=3
            )
            
            with gr.Row():
                run_button = gr.Button("🚀 Start Research", variant="primary", scale=1)
                clear_button = gr.Button("Clear", variant="secondary", scale=0)
                
            # Quick examples
            with gr.Accordion("💡 Example Questions", open=False):
                gr.Examples(
                    examples=[
                        "What are the environmental impacts of constructing skyscrapers?",
                        "How does urban planning influence the development of tall buildings in major cities?",
                        "What engineering breakthroughs have enabled the construction of megatall buildings like Jeddah Tower?",
                        "Compare the sustainability features of the Burj Khalifa and Shanghai Tower",
                        "How do zoning laws affect skyscraper development in New York City?"
                    ],
                    inputs=query_textbox,
                    label="Click to load example questions"
                )
        
        with gr.Column(scale=1):
            gr.Markdown("### 📊 Research Focus")
            category_display = gr.Markdown(
                "*Waiting for question...*",
                label="Detected Category"
            )
    
    report = gr.Markdown(
        label="Research Report",
        elem_classes="report-output"
    )
    
    # Status indicator
    status = gr.Textbox(
        label="Status",
        value="Ready",
        interactive=False
    )
    
    def update_category_display(query):
        """Update the category display based on query"""
        if not query.strip():
            return "*Waiting for question...*"
        
        tuned_params = TunedResearchManager()._categorize_question(query)
        category_names = {
            "environmental_impact": "🏭 Environmental Impact Analysis",
            "urban_planning": "🗺️ Urban Planning & Policy",
            "engineering_breakthroughs": "⚙️ Engineering Innovations",
            "general": "📚 General Research"
        }
        
        display_name = category_names.get(tuned_params["category"], "📚 General Research")
        return f"**{display_name}**\n\n{tuned_params['guidance']}"
    
    def clear_all():
        return "", "*Waiting for question...*", "Ready", ""
    
    # Connect events
    query_textbox.change(
        fn=update_category_display,
        inputs=query_textbox,
        outputs=category_display
    )
    
    run_button.click(
        fn=lambda: "Researching...",
        outputs=status
    ).then(
        fn=run,
        inputs=query_textbox,
        outputs=report
    ).then(
        fn=lambda: "Complete",
        outputs=status
    )
    
    query_textbox.submit(
        fn=lambda: "Researching...",
        outputs=status
    ).then(
        fn=run,
        inputs=query_textbox,
        outputs=report
    ).then(
        fn=lambda: "Complete",
        outputs=status
    )
    
    clear_button.click(
        fn=clear_all,
        outputs=[query_textbox, category_display, status, report]
    )
    
    # Custom CSS for better styling
    ui.css = """
    .report-output {
        padding: 20px;
        background-color: #f8f9fa;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        max-height: 600px;
        overflow-y: auto;
    }
    .report-output h2 {
        color: #1a73e8;
        border-bottom: 2px solid #1a73e8;
        padding-bottom: 10px;
    }
    .report-output h3 {
        color: #5f6368;
        margin-top: 20px;
    }
    .report-output ul, .report-output ol {
        padding-left: 25px;
    }
    .report-output li {
        margin-bottom: 8px;
    }
    """

ui.launch(
    inbrowser=True,
)