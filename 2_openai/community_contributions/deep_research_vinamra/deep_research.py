import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager
from clarifying_questions import ClarifyingQuestionsTool
import asyncio

load_dotenv(override=True)

# Global state for interactive questions
clarifying_state = {
    "questions": None,
    "answers": [],
    "current_index": 0,
    "original_query": ""
}


async def run_research(query: str, skip_clarifying: bool = False):
    """Run the research process with optional clarifying questions"""
    async for chunk in ResearchManager().run(query, skip_clarifying=skip_clarifying):
        yield chunk


async def start_clarifying_questions(query: str):
    """Generate and start the clarifying questions flow"""
    global clarifying_state
    
    if not query or len(query.strip()) < 3:
        return "Please enter a research query first.", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
    
    try:
        questions = await ClarifyingQuestionsTool.generate_questions(query)
        
        if ClarifyingQuestionsTool.should_ask_questions(questions):
            # Initialize state
            clarifying_state = {
                "questions": questions.questions,
                "answers": [],
                "current_index": 0,
                "original_query": query
            }
            
            # Show first question
            question_text = f"## Question 1 of {len(questions.questions)}\n\n{questions.questions[0]}"
            return question_text, gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)
        else:
            return f"✅ Your query is clear (confidence: {questions.confidence_score:.0%}). No clarifying questions needed!", gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)
    except Exception as e:
        return f"Error generating questions: {str(e)}", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)


def submit_answer(answer: str):
    """Submit answer to current question and move to next"""
    global clarifying_state
    
    if not clarifying_state["questions"]:
        return "No active questions.", gr.update(), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
    
    # Save answer
    clarifying_state["answers"].append(answer)
    clarifying_state["current_index"] += 1
    
    # Check if more questions
    if clarifying_state["current_index"] < len(clarifying_state["questions"]):
        question_text = f"## Question {clarifying_state['current_index'] + 1} of {len(clarifying_state['questions'])}\n\n{clarifying_state['questions'][clarifying_state['current_index']]}"
        return question_text, gr.update(value=""), gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)
    else:
        # All questions answered - show summary
        summary = f"## ✅ All Questions Answered\n\n**Original Query:** {clarifying_state['original_query']}\n\n**Context:**\n"
        for i, (q, a) in enumerate(zip(clarifying_state['questions'], clarifying_state['answers']), 1):
            summary += f"\n**Q{i}:** {q}\n**A{i}:** {a}\n"
        
        return summary, gr.update(value=""), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)


async def run_research_with_context():
    """Run research with the refined query including Q&A context"""
    global clarifying_state
    
    if not clarifying_state["questions"]:
        yield "No clarifying questions answered."
        return
    
    refined_query = ClarifyingQuestionsTool.refine_query_with_answers(
        clarifying_state["original_query"],
        clarifying_state["questions"],
        clarifying_state["answers"]
    )
    
    async for chunk in ResearchManager().run(refined_query, skip_clarifying=True):
        yield chunk


with gr.Blocks() as ui:
    gr.Markdown(
        """
        # 🔬 Deep Research
        
        Advanced AI-powered research assistant with comprehensive guardrails and quality controls.
        
        **Features:**
        - ✅ Input validation and safety checks
        - 🤔 Interactive clarifying questions
        - 📊 Multi-source web research
        - 📝 Comprehensive report generation
        - 📧 Automatic email delivery
        """
    )
    
    with gr.Row():
        with gr.Column(scale=2):
            query_textbox = gr.Textbox(
                label="What topic would you like to research?",
                placeholder="E.g., Impact of artificial intelligence on healthcare delivery",
                lines=3
            )
            
            with gr.Row():
                clarify_button = gr.Button("🤔 Start Clarifying Questions", variant="secondary")
                run_button = gr.Button("🚀 Run Research Directly", variant="primary")
            
            gr.Markdown(
                """
                **Tips:**
                - Use "Start Clarifying Questions" for better, more focused research
                - Answer questions one by one to refine your query
                - Or "Run Research Directly" to skip clarifications
                """
            )
        
        with gr.Column(scale=1):
            gr.Markdown(
                """
                ### 🛡️ Safety Features
                
                ✓ Query validation  
                ✓ Rate limiting  
                ✓ Content filtering  
                ✓ Output verification  
                ✓ Sensitive topic warnings  
                
                ### 📝 Process
                
                1. **Clarify** - Refine your query
                2. **Plan** - Create search strategy
                3. **Search** - Gather information
                4. **Synthesize** - Write report
                5. **Deliver** - Send via email
                """
            )
    
    # Clarifying questions section
    clarifying_output = gr.Markdown(label="Clarifying Questions")
    answer_textbox = gr.Textbox(
        label="Your Answer",
        placeholder="Type your answer here...",
        lines=2,
        visible=False
    )
    submit_answer_button = gr.Button("Submit Answer ➡️", variant="secondary", visible=False)
    run_with_context_button = gr.Button("🚀 Run Research with Context", variant="primary", visible=False)
    
    # Report output
    report_output = gr.Markdown(label="Research Report")
    
    # Event handlers
    clarify_button.click(
        fn=start_clarifying_questions,
        inputs=query_textbox,
        outputs=[clarifying_output, answer_textbox, submit_answer_button, run_with_context_button]
    )
    
    submit_answer_button.click(
        fn=submit_answer,
        inputs=answer_textbox,
        outputs=[clarifying_output, answer_textbox, answer_textbox, submit_answer_button, run_with_context_button]
    )
    
    run_with_context_button.click(
        fn=run_research_with_context,
        inputs=None,
        outputs=report_output
    )
    
    run_button.click(
        fn=run_research,
        inputs=query_textbox,
        outputs=report_output
    )

if __name__ == "__main__":
    ui.launch(inbrowser=True, theme=gr.themes.Default(primary_hue="sky"))

