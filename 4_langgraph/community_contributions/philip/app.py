"""
Gradio UI for Content Creation Assistant.
"""

import gradio as gr
from content_agent import ContentAgent
import asyncio


async def setup():
    """Set up the content agent."""
    agent = ContentAgent()
    await agent.build_graph()
    return agent


async def process_request(agent, message, success_criteria, history):
    """Process a content creation request."""
    if not agent:
        return history, agent
    
    try:
        result = await agent.run(message, success_criteria or "Content should be high quality and meet all requirements")
        
        # Extract content
        content = result.get("final_content", "No content generated.")
        content_type = result.get("content_type", "unknown")
        seo_metadata = result.get("seo_metadata", {})
        feedback = result.get("feedback", "")
        
        # Format response
        response_parts = [f"**Content Type:** {content_type}\n\n"]
        
        if seo_metadata:
            response_parts.append("**SEO Metadata:**\n")
            if seo_metadata.get("title"):
                response_parts.append(f"- Title: {seo_metadata['title']}\n")
            if seo_metadata.get("meta_description"):
                response_parts.append(f"- Meta Description: {seo_metadata['meta_description']}\n")
            response_parts.append("\n")
        
        response_parts.append("**Generated Content:**\n\n")
        response_parts.append(content)
        
        if feedback:
            response_parts.append(f"\n\n**Feedback:** {feedback}")
        
        response = "".join(response_parts)
        
        # Update history
        user_msg = {"role": "user", "content": message}
        assistant_msg = {"role": "assistant", "content": response}
        
        return history + [user_msg, assistant_msg], agent
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        return history + [{"role": "user", "content": message}, {"role": "assistant", "content": error_msg}], agent


async def reset():
    """Reset the agent."""
    new_agent = ContentAgent()
    await new_agent.build_graph()
    return "", "", [], new_agent


# Build UI
with gr.Blocks(title="Content Creation Assistant", theme=gr.themes.Default(primary_hue="blue")) as ui:
    gr.Markdown("## 📝 Content Creation Assistant")
    gr.Markdown("Create high-quality content: blog posts, social media, SEO content")
    
    agent = gr.State()
    
    with gr.Row():
        chatbot = gr.Chatbot(label="Content Assistant", height=500, type="messages")
    
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(
                show_label=False,
                placeholder="What content would you like to create? (e.g., 'Create a 1000-word blog post about AI in healthcare')",
                lines=3
            )
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False,
                placeholder="Success criteria (optional): Content should be engaging, well-structured, and SEO-optimized",
                lines=2
            )
    
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Create Content", variant="primary")
    
    with gr.Accordion("Examples", open=False):
        gr.Markdown("""
        **Blog Post:**
        - "Create a 1500-word blog post about 'The Future of AI in Healthcare' with SEO optimization, professional tone"
        
        **Social Media:**
        - "Create 5 LinkedIn posts about AI trends, each 200-300 words, professional tone, include hashtags"
        - "Create a Twitter thread about Python programming tips"
        
        **SEO Content:**
        - "Create SEO-optimized article about 'Python for Data Science', 2000 words, keywords: python, data science, machine learning"
        """)
    
    # Event handlers
    ui.load(setup, [], [agent])
    
    def process_sync(agent, message, success_criteria, history):
        return asyncio.run(process_request(agent, message, success_criteria, history))
    
    message.submit(
        process_sync,
        [agent, message, success_criteria, chatbot],
        [chatbot, agent]
    )
    
    success_criteria.submit(
        process_sync,
        [agent, message, success_criteria, chatbot],
        [chatbot, agent]
    )
    
    go_button.click(
        process_sync,
        [agent, message, success_criteria, chatbot],
        [chatbot, agent]
    )
    
    reset_button.click(
        reset,
        [],
        [message, success_criteria, chatbot, agent]
    )


if __name__ == "__main__":
    ui.launch(inbrowser=True)

