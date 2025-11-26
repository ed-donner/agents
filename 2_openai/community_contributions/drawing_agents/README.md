# openai-drawing-agents

Learning project using OpenAI Agents SDK.
Uses guardrails, tools, handoffs, context management and image inputs.
Uses a wrapper class around the Pillow library for exposing a free draw API to the model.

1. Planning agent:
   Creates a plan for how to draw the request on the canvas.

2. Drawing agent:
   Executes the plan on the provided canvas tool.

3. Evaluation agent:
   Receives the drawing as image input along with the original request, and provides feedback.

This project uses uv as the environment manager.

Run using:
uv run python main.py

Output is saved as agent_output.png and then evaluated.