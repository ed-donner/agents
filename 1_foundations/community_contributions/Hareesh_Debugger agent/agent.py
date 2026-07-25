import json
from openai import OpenAI
from tools import run_python_script, write_to_file, push_notification, tools_schema

class DebugAgent:
    def __init__(self):
        self.client = OpenAI()
        # Update the System Prompt in your DebugAgent class
        self.system_prompt = (
            "You are a Senior Software Architect. Your goal is to fix 'sandbox.py'.\n"
            "Follow this Agentic Loop:\n"
            "1. RUN the script to see the current error.\n"
            "2. THINK: Explain the error (e.g., NumPy API changes or matrix dimension mismatches).\n"
            "3. ACT: Write the FULL corrected code to 'sandbox.py'.\n"
            "4. REPEAT until the output says 'SUCCESS'.\n"
            "5. NOTIFY: Use the push_notification tool to alert the user once all loops are complete."
        )

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            if name == "run_python_script":
                content = run_python_script()
            elif name == "write_to_file":
                content = write_to_file(args['code'])
            elif name == "push_notification":
                content = push_notification(args['message'])
            
            results.append({"role": "tool", "tool_call_id": tool_call.id, "content": content})
        return results

    def run(self, buggy_code):
        # Initialize the file
        write_to_file(buggy_code)
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": "Fix the bugs in sandbox.py and notify me when it runs perfectly."}
        ]
        
        done = False
        loop_count = 0
        while not done and loop_count < 10:
            loop_count += 1
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools_schema
            )
            
            choice = response.choices[0]
            messages.append(choice.message)

            if choice.finish_reason == "tool_calls":
                results = self.handle_tool_call(choice.message.tool_calls)
                messages.extend(results)
            else:
                done = True
        
        return choice.message.content, loop_count