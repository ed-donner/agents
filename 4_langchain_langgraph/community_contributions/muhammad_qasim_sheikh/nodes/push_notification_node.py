from state import ResearchState
from tools import push 

def push_notification_node(state: ResearchState) -> ResearchState:
    print("EXECUTING: PUSH NOTIFICATION NODE")
    
    filename = state.filename
    if not filename:
        state.final_status += "\nSkipping push notification: Missing filename."
        return state
        
    try:
        message = f"Your research report '{filename}' has been emailed to you."
        
        result = push(message)
        
        print(f"  Push result: {result}")
        state.final_status += f"\n{result}" 
        
    except Exception as e:
        print(f"  Error sending push notification: {e}")
        state.final_status += f"\nError sending push notification: {e}"
        
    return state