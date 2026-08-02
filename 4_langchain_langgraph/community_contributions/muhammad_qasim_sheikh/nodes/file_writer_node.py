import os
from state import ResearchState
from tools import sandbox_dir 
from langchain_community.tools.file_management import WriteFileTool

def file_writer_node(state: ResearchState) -> ResearchState:
    print("EXECUTING: FILE WRITER NODE")
    
    final_report = state.best_report or state.report
    if not final_report:
        state.final_status = "No report available to save."
        return state

    safe_query = "".join(c for c in state.user_query if c.isalnum() or c in " _-").rstrip()[:50]
    filename = f"{safe_query.replace(' ', '_')}.md"
    state.filename = filename 

    try:
        write_tool = WriteFileTool(root_dir=sandbox_dir)
        result = write_tool.run({
            "file_path": filename,
            "text": final_report
        })
        
        print(f"  File write result: {result}")
        state.final_status = result 
    
    except Exception as e:
        print(f"  Error writing file: {e}")
        state.final_status = f"Error writing file: {e}"

    return state