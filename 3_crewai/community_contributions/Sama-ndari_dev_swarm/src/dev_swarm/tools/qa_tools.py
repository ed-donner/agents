import subprocess
import os
from crewai.tools import BaseTool

class CodeExecutionTool(BaseTool):
    name: str = "Code Execution Tool"
    description: str = "Executes a python file and returns the output or error. Use this to verify code works."

    def _run(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return f"Error: File {file_path} not found. Ensure the Lead Developer has created it."
            
        try:
            # Runs the code and captures output
            result = subprocess.run(
                ["python3", file_path], 
                capture_output=True, 
                text=True, 
                timeout=15
            )
            
            if result.returncode == 0:
                return f"SUCCESS: Output:\n{result.stdout}"
            else:
                return f"CRASHED: Error Log:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "CRASHED: Execution timed out (possible infinite loop)."
        except Exception as e:
            return f"Execution Error: {str(e)}"