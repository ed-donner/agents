"""Base agent class with real LLM-powered function calling behavior."""

import os
import json
import inspect
from typing import Any, Callable, List, Optional, Dict
from dataclasses import dataclass
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv(override=True)


def function_tool(func: Callable) -> Callable:
    """Decorator to mark a function as a tool for agents.
    
    Extracts function metadata for LLM function calling.
    
    Args:
        func: Function to be decorated as a tool
        
    Returns:
        Decorated function with tool metadata
    """
    func._is_tool = True
    func._tool_name = func.__name__
    func._tool_description = func.__doc__ or ""
    return func


def _python_type_to_gemini_type(python_type: type) -> str:
    """Convert Python type annotations to Gemini API types."""
    type_mapping = {
        str: "STRING",
        int: "INTEGER",
        float: "NUMBER",
        bool: "BOOLEAN",
        list: "ARRAY",
        dict: "OBJECT",
        List: "ARRAY",
        Dict: "OBJECT",
    }
    
    # Handle typing module types
    origin = getattr(python_type, '__origin__', None)
    if origin is not None:
        return type_mapping.get(origin, "STRING")
    
    return type_mapping.get(python_type, "STRING")


def _convert_tool_to_function_declaration(tool: Callable) -> Dict[str, Any]:
    """Convert a Python function to Gemini function declaration format.
    
    Args:
        tool: Function decorated with @function_tool
        
    Returns:
        Dictionary in Gemini function declaration format
    """
    sig = inspect.signature(tool)
    parameters = {}
    required = []
    
    for param_name, param in sig.parameters.items():
        # Skip self and cls parameters
        if param_name in ('self', 'cls'):
            continue
            
        param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
        gemini_type = _python_type_to_gemini_type(param_type)
        
        parameters[param_name] = {
            "type": gemini_type,
            "description": f"Parameter {param_name}"
        }
        
        # Mark as required if no default value
        if param.default == inspect.Parameter.empty:
            required.append(param_name)
    
    return {
        "name": tool.__name__,
        "description": tool.__doc__ or f"Function {tool.__name__}",
        "parameters": {
            "type": "OBJECT",
            "properties": parameters,
            "required": required
        }
    }


@dataclass
class Agent:
    """Agent with real LLM-powered autonomous behavior.
    
    The agent uses Gemini's function calling to autonomously decide
    when and how to use tools based on user requests.
    
    Example:
        agent = Agent(
            name="Email agent",
            instructions="Send emails to users",
            tools=[send_email],
            model="gemini-2.5-flash",
        )
        
        result = await agent.run("Send an email to john@example.com")
    """
    name: str
    instructions: str
    tools: List[Callable]
    model: str = "gemini-2.5-flash"
    
    def __post_init__(self):
        """Initialize Gemini client and validate tools."""
        # Validate tools
        for tool in self.tools:
            if not hasattr(tool, '_is_tool'):
                raise ValueError(
                    f"Tool {tool.__name__} must be decorated with @function_tool"
                )
        
        # Initialize Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be set in environment variables")
        
        genai.configure(api_key=api_key)
        
        # Convert tools to function declarations
        self.function_declarations = [
            _convert_tool_to_function_declaration(tool) 
            for tool in self.tools
        ]
        
        # Create tool lookup dictionary
        self.tool_map = {tool.__name__: tool for tool in self.tools}
        
        # Initialize model with tools
        self.model_instance = genai.GenerativeModel(
            model_name=self.model,
            tools=self.function_declarations,
            system_instruction=self.instructions
        )
    
    async def run(
        self, 
        user_message: str, 
        context: Optional[Dict[str, Any]] = None,
        return_raw_tool_result: bool = False
    ) -> Any:
        """Run the agent with a user message.
        
        The agent will:
        1. Analyze the user message
        2. Decide which tools to call (if any)
        3. Execute tool calls
        4. Return the final result
        
        Args:
            user_message: The user's request/query
            context: Optional context dictionary to pass to the agent
            return_raw_tool_result: If True, return the raw tool result instead of LLM's final response
            
        Returns:
            The agent's response (could be text or structured data)
        """
        # Build the full prompt
        full_prompt = user_message
        if context:
            full_prompt = f"Context: {json.dumps(context)}\n\nTask: {user_message}"
        
        # Start chat session
        chat = self.model_instance.start_chat(enable_automatic_function_calling=False)
        
        # Send initial message
        response = chat.send_message(full_prompt)
        
        # Agent loop: handle function calls until we get a final response
        max_iterations = 10
        iteration = 0
        last_tool_result = None  # Track the last tool result for raw return
        
        while iteration < max_iterations:
            # Check if model wants to call a function
            if not response.candidates:
                break
                
            parts = response.candidates[0].content.parts
            
            # Check if any part is a function call
            function_calls = [part.function_call for part in parts if part.function_call]
            
            if not function_calls:
                # No more function calls, we have the final response
                break
            
            # Execute all requested function calls
            function_responses = []
            
            for function_call in function_calls:
                function_name = function_call.name
                function_args = dict(function_call.args)
                
                print(f"[{self.name}] Calling tool: {function_name} with args: {function_args}")
                
                # Execute the function
                if function_name in self.tool_map:
                    try:
                        tool_func = self.tool_map[function_name]
                        
                        # Check if function is async
                        if inspect.iscoroutinefunction(tool_func):
                            result = await tool_func(**function_args)
                        else:
                            result = tool_func(**function_args)
                        
                        # Convert result to JSON-serializable format
                        if not isinstance(result, (str, int, float, bool, list, dict, type(None))):
                            result = str(result)
                        
                        function_responses.append({
                            "name": function_name,
                            "response": result
                        })
                        
                        # Track last tool result for potential raw return
                        last_tool_result = result
                        
                    except Exception as e:
                        function_responses.append({
                            "name": function_name,
                            "response": f"Error: {str(e)}"
                        })
                else:
                    function_responses.append({
                        "name": function_name,
                        "response": f"Error: Function {function_name} not found"
                    })
            
            # Send function results back to model
            response = chat.send_message(
                [genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=fr["name"],
                        response={"result": fr["response"]}
                    )
                ) for fr in function_responses]
            )
            
            iteration += 1
        
        # Return raw tool result if requested
        if return_raw_tool_result and last_tool_result is not None:
            return last_tool_result
        
        # Extract final response text
        if response.candidates and response.candidates[0].content.parts:
            final_text = ""
            for part in response.candidates[0].content.parts:
                if part.text:
                    final_text += part.text
            return final_text.strip() if final_text else "Task completed successfully"
        
        return "Task completed successfully"
    
    def __repr__(self) -> str:
        return f"Agent(name='{self.name}', model='{self.model}', tools={len(self.tools)})"
