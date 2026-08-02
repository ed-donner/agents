"""
Notifier Node - Sends the learning path PDF via email using Resend API.
"""

from typing import Dict, Any
from state import State
from tools import send_email_with_pdf, create_email_body

class NotifierNode:
    """
    Send the learning path PDF to the user's email via Resend API.
    """
    
    def __init__(self):
        """Initialize the notifier node."""
        pass

    def execute(self, state: State) -> Dict[str, Any]:
        """Execute the notifier node."""
        topic = state["topic"]
        user_email = state.get("user_email")
        pdf_path = state.get("pdf_path")
        curriculum = state.get("curriculum")
        if not user_email:
            return {
                "notification_status": "Error: No email address provided.",
                "notification_sent": False,
                "messages": [{"role": "assistant", "content": "Notification failed: No email address."}]
            }
        
        if not pdf_path:
            return {
                "notification_status": "Error: No PDF file to send.",
                "notification_sent": False,
                "messages": [{"role": "assistant", "content": "Notification failed: No PDF file."}]
            }
        
        total_phases = len(curriculum.milestones) if curriculum else 0
        total_days = curriculum.total_estimated_days if curriculum else 0
        email_body = create_email_body(topic, total_phases, total_days)
        subject = f"Your Learning Path for {topic} is Ready!"
        
        result = send_email_with_pdf(
            to_email=user_email,
            subject=subject,
            body_html=email_body,
            pdf_path=pdf_path,
        )
        
        success = "Successfully" in result
        
        return {
            "notification_status": result,
            "notification_sent": success,
            "messages": [{"role": "assistant", "content": f"Email {'sent' if success else 'failed'}: {result}"}]
        }
