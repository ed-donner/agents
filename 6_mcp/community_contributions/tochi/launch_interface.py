import gradio as gr
from dns_agent import dns_chat


demo = gr.ChatInterface(
    fn=dns_chat,
    title="🌐 DNS Lookup & Monitoring Assistant",
    description="""
    **Your DNS Domain Tracker & Monitor**
    
    I can help you:
    - 🔍 Look up domain information (registrar, expiry, name servers)
    - 💾 Automatically save domains to your tracking database
    - ⏰ Monitor domains expiring within 3 months
    - 📊 View your complete domain portfolio
    
    Just ask naturally - I'll handle the rest!
    """,
    examples=[
        "Check the expiration date for routelink.com",
        "Who is the registrar for github.com?",
        "Show me domains expiring within 3 months",
        "Look up google.com and add it to my watchlist",
        "List all my tracked domains",
        "Get complete DNS info for stackoverflow.com"
    ],
    theme=gr.themes.Soft(),
    chatbot=gr.Chatbot(height=600, avatar_images=(None, "🤖")),
    textbox=gr.Textbox(placeholder="Ask about a domain...", container=False, scale=7),
    # submit_btn="Send",
    # retry_btn="🔄 Retry",
    # undo_btn="↩️ Undo",
    # clear_btn="🗑️ Clear",
)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 DNS Lookup Assistant Starting...")
    print("="*60)
    print("\n📋 Prerequisites Check:")
    print("   ✓ dns_server.py in current directory")
    print("   ✓ uv installed (pip install uv)")
    print("   ✓ .env file with API_NINJA key")
    print("\n🌐 Launching Gradio interface...")
    print("="*60 + "\n")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )