from state import ResearchState
from tools import send_email

def email_node(state: ResearchState) -> ResearchState:
    print("EXECUTING: EMAIL NODE")
    
    # Read the data from the state
    report_html = state.report_html
    filename = state.filename
    
    if not report_html or not filename:
        state.final_status += "\nSkipping email: Missing HTML report or filename."
        return state
        
    try:
        subject = f"Research Report: {state.user_query}"
        result = send_email(
            subject=subject,
            html_body=report_html, 
            file_to_attach=filename
        )
        print(f"  Email result: {result}")
        state.final_status += f"\n{result}"
        
    except Exception as e:
        print(f"  Error sending email: {e}")
        state.final_status += f"\nError sending email: {e}"
        
    return state