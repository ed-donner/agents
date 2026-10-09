import os
from dotenv import load_dotenv
from openai import OpenAI
import json
from IPython.display import Markdown, display

load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')

if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set - please head to the troubleshooting guide in the setup folder")

openai = OpenAI()

def form_message(prompt):
    messages = [
        {
            "role": "user", 
            "content": prompt
        }
    ]
    return messages

def pick_business_area():
    prompt ="""
    Identify one realistic business area, workflow, or business process that could be significantly improved using an AI Agentic Solution.

    Choose the industry, type of company, and business process yourself. Do not ask for any additional information.

    The opportunity should specifically benefit from agentic AI, meaning that the solution should require some combination of autonomous reasoning, decision-making, tool usage, information gathering, multi-step execution, monitoring, or interaction with external systems.

    Avoid trivial examples that could be solved equally well with a simple chatbot, deterministic software, or traditional workflow automation.

    Industry:
    The industry where the opportunity exists.
    
    Business Area:
    The department, function, or process.
    
    Output ONLY JSON: {'industry':'', 'business_area':''}
    """
    messages = form_message(prompt)
    response = openai.chat.completions.create(model="gpt-5.4-mini", messages=messages)
    json_output = json.loads(response.choices[0].message.content)
    return json_output['industry'], json_output['business_area']

def find_pain_point(industry, business_area):
    prompt = f"""
    You are a business process analyst.

    Given an industry and a business area, identify one realistic and significant pain point that commonly exists in that area.

    The pain point should be specific enough to potentially serve as the basis for designing an AI or agentic AI solution later.

    Focus on problems involving one or more of the following:

    Repetitive manual work
    Information spread across multiple systems
    Manual data gathering or reconciliation
    Slow decision-making
    Frequent human handoffs
    High volumes of emails, documents, tickets, or requests
    Repeated monitoring or follow-up
    Error-prone processes
    Bottlenecks caused by limited human availability
    Processes that require judgment based on multiple sources of information
    Delays caused by waiting for information or approvals
    Inconsistent execution of a business process

    Do not propose a solution.

    Do not mention AI.

    Do not ask for additional information.

    Select one strong, realistic pain point rather than listing several possibilities.

    Input:

    Industry: {industry}
    Business Area: {business_area}

    Output only:

    Pain point:
    Short description of the problem
    """
    messages = form_message(prompt)
    response = openai.chat.completions.create(model="gpt-5.4-mini", messages=messages)
    return response.choices[0].message.content

def propose_solution(industry, business_area, pain_point):
    prompt = f"""
    You are an AI solutions architect specializing in agentic systems and business process automation.

    Given an `industry`, `business area`, and `pain point`, propose one practical Agentic AI Solution that would help reduce or eliminate the pain point.

    The solution should be realistic and should only use agentic AI where autonomous reasoning, tool usage, multi-step execution, monitoring, or coordination provides clear value.

    Do not over-engineer the solution. Prefer the simplest agentic architecture that can solve the problem effectively.

    Input:

    Industry: {industry}

    Business Area: {business_area}

    Pain Point: {pain_point}

    Analyze the pain point and design a solution that can:

    * Gather relevant information from available systems or data sources
    * Reason about the information
    * Decide what action should be taken
    * Use tools, APIs, databases, documents, or enterprise systems where appropriate
    * Execute multi-step workflows
    * Verify the result of its actions
    * Escalate to a human when confidence is low or when an action has significant business impact

    Do not assume that everything should be fully autonomous.

    Output only:

    **Solution Name:**
    A short descriptive name.

    **Agentic AI Solution:**
    Describe the proposed solution and what the agent does.

    **Agent Workflow:**
    Describe the main agent loop, for example:

    Observe → Analyze → Decide → Act → Verify → Continue or Escalate

    Explain what happens at each stage.

    **Required Tools and Integrations:**
    List the systems, APIs, databases, communication channels, or other tools the agent would likely need access to.

    **Agent Responsibilities:**
    Describe which tasks and decisions the agent handles.

    **Human-in-the-Loop:**
    Describe which actions or decisions should require human approval or escalation.

    **Expected Improvement:**
    Explain how the solution reduces the supplied pain point and what business benefits it could provide.

    **Why Agentic AI:**
    Briefly explain why an agentic approach is appropriate instead of a simple chatbot, deterministic software, or traditional workflow automation.

    Keep the solution concrete, realistic, and focused specifically on the supplied pain point.
    """
    messages = form_message(prompt)
    response = openai.chat.completions.create(model="gpt-5.4", messages=messages)
    return response.choices[0].message.content

# Find a business area in an Industry:
(industry, business_area) = pick_business_area()

print(f"Found the following business area {business_area} in industry {industry}")

pain_point = find_pain_point(industry, business_area)

print(f"Found the following pain point: {pain_point}")

solution = propose_solution(industry, business_area, pain_point)

print("Solution proposed:")
print(solution)