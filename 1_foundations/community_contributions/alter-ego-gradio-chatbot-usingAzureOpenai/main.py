from agent import ConversationAgent


def main():
    """Initialize and launch the chat interface."""
    from gradio.chat_interface import ChatInterface
    
    # TODO: Change this to your actual name
    agent = ConversationAgent(name="Harsh Patel")
    
    ChatInterface(
        fn=agent.chat,
        title=f"Chat with {agent.name}",
        description="Ask me anything about my professional background, experience, and skills.",
        examples=[
            "What's your background?",
            "Tell me about your technical skills",
            "What kind of projects have you worked on?",
        ],
    ).launch()


if __name__ == "__main__":
    main()
