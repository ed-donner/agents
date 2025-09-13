import gradio as gr
from dotenv import load_dotenv
from agents import Runner, trace, gen_trace_id
from research_manager import research_manager
from clarification_agent import clarification_agent

load_dotenv(override=True)

# The hardcoded string to detect if clarification has been provided
CLARIFICATION_MARKER = "Clarification and Additional Context:"


async def process_research_request(message: str, history):
    """Process research request following the workflow logic"""
    if not message.strip():
        yield history, ""
        return
    
    print(history)

    try:
        # Step 2: Analyze if input contains clarification marker
        clarification_found = any(CLARIFICATION_MARKER in response for user_msg, response in history)
        if clarification_found:
            print("✅ Found clarification marker - proceeding directly to research")
            # Step 6: Call research_manager with the complete input
            result = await execute_research(message, history)
            yield history + [(message, result)], ""
            return
        
        else:
            print("🤔 No clarification marker found - running Clarification Agent first")
            # Step 3: Run Clarification Agent for original request
            
            clarification_result = await Runner.run(
                clarification_agent, 
                f"Generate clarifying questions for: {message}"
            )
            
            if hasattr(clarification_result, 'final_output') and hasattr(clarification_result.final_output, 'questions'):
                questions = clarification_result.final_output.questions
                
                # Step 4: Show clarification questions in chat for user to answer
                clarification_response = "**Please answer these clarifying questions:**\n\n"
                
                for i, question in enumerate(questions, 1):
                    clarification_response += f"**{i}.** {question}\n\n"
                
                clarification_response += CLARIFICATION_MARKER
                
                yield history + [(message, clarification_response)], ""
                return
            else:
                # If clarification agent fails, proceed with original request
                print("❌ Clarification agent failed - proceeding with original request")
                result = await execute_research(f"Research this topic comprehensively: {message}", history)
                yield history + [(f"Research this topic comprehensively: {message}", result)], ""
                return
                
    except Exception as e:
        print(f"Error in workflow: {e}")
        error_response = f"❌ **Error occurred:** {str(e)}\n\nPlease try again with a new research query."
        yield history + [(message, error_response)], ""


async def execute_research(research_query: str, history):
    """Execute the research process"""
    try:
        # Generate single trace ID for the entire research session
        trace_id = gen_trace_id()
        
        with trace("Complete Research Session", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            
            # Convert history to concatenated string for research manager
            history_string = ""
            for user_msg, bot_response in history:
                history_string += f"User: {user_msg}\n"
                history_string += f"Assistant: {bot_response}\n"
                history_string += "---\n"
            
            # Add the current research query at the end
            history_string += f"Current Research Query: {research_query}"
            
            # Direct call to research manager with the complete conversation history
            result = await Runner.run(research_manager, history_string)
            
            # Build final response
            response_parts = []
            response_parts.append(f"🚀 **Deep Research Process Complete**")
            response_parts.append(f"📊 [View Trace](https://platform.openai.com/traces/trace?trace_id={trace_id})")
            response_parts.append("---")
            response_parts.append("✅ **RESEARCH HANDOFF CHAIN COMPLETED!**")
            response_parts.append("---")
            response_parts.append("**Process Summary:**")
            response_parts.append("✅ Research Manager → gathered comprehensive information")
            response_parts.append("✅ Writer Agent → created detailed report")  
            response_parts.append("✅ Email Agent → formatted and sent email")
            response_parts.append("---")
            
            # Add the final result
            if hasattr(result, 'final_output'):
                response_parts.append("📄 **Final Report Summary:**")
                response_parts.append(str(result.final_output))
            else:
                response_parts.append(str(result))
            
            response_parts.append("\n✅ **Research Complete!** Check your email for the full formatted report.")
            
            return "\n".join(response_parts)
            
    except Exception as e:
        return f"❌ **Error occurred:** {str(e)}\n\nPlease try again with a new research query."


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("""
    # 🔬 Deep Research System
    
    This intelligent research system uses **agent handoffs** to:
    1. 🔍 **Research Manager** - Plans and executes comprehensive web searches
    2. ✍️ **Writer Agent** - Creates detailed reports from findings  
    3. 📧 **Email Agent** - Formats and sends the final report
    
    **Simply enter your research query below and watch the agents work together!**
    """)
    
    chatbot = gr.Chatbot(
        value=[],
        label="Research Conversation", 
        height=500,
        show_copy_button=True,
        show_label=True,
        avatar_images=("🔬", "🤖"),  # User and assistant avatars
        bubble_full_width=False
    )
    
    with gr.Row():
        msg = gr.Textbox(
            label="Research Query",
            placeholder="What would you like me to research? (e.g., 'latest developments in quantum computing', 'market analysis of electric vehicles')",
            lines=2,
            scale=4
        )
        send_btn = gr.Button(
            "🚀 Start Research", 
            variant="primary",
            scale=1,
            size="lg"
        )
    
    with gr.Row():
        clear = gr.Button("🗑️ Clear Chat", variant="secondary")
        gr.Markdown("*💡 Tip: Be specific in your research queries for better results. The system will create a comprehensive report and email it to you.*")
    
    # Set up the interface interactions
    msg.submit(
        process_research_request,
        inputs=[msg, chatbot],
        outputs=[chatbot, msg],
        show_progress="full"
    )
    
    send_btn.click(
        process_research_request,
        inputs=[msg, chatbot],
        outputs=[chatbot, msg],
        show_progress="full"
    )
    
    clear.click(
        lambda: ([], ""),
        outputs=[chatbot, msg]
    )

if __name__ == "__main__":
    ui.launch(
        inbrowser=True,
        show_error=True,
        share=False
    )