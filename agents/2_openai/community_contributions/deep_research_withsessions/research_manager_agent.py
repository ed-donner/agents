#research manager
from agents import Agent, handoff, SQLiteSession, gen_trace_id, Runner, trace
from agents.extensions import handoff_filters
from search_agent import search_agent
from planner_agent import planner_agent
from writer_agent import writer_agent
from email_agent import email_agent

# Convert agents to tools
planner_tool = planner_agent.as_tool(tool_name="planner_agent", tool_description="Create search strategy")
search_tool = search_agent.as_tool(tool_name="search_agent", tool_description="Execute web searches and summarises results")
writer_tool = writer_agent.as_tool(tool_name="writer_agent", tool_description="Generate research report")

# Research Manager Agent

#handoff prompt recommended by openai
RECOMMENDED_PROMPT_PREFIX = "# System context\nYou are part of a multi-agent system called the Agents SDK, designed to make agent coordination and execution easy. \
Agents uses two primary abstraction: **Agents** and **Handoffs**. An agent encompasses instructions and tools and can hand off a conversation to another agent when \
appropriate. Handoffs are achieved by calling a handoff function, generally named `transfer_to_<agent_name>`. Transfers between agents are handled seamlessly in the background;\
do not mention or draw attention to these transfers in your conversation with the user.\n"

INSTRUCTIONS = (
    f"""{RECOMMENDED_PROMPT_PREFIX} You research companies and create reports. You have these tools:
- planner_tool: Create search strategies
- search_tool: Find information  
- writer_tool: Create reports

Look at the conversation history to understand what's needed:
- New research request? Plan, search, write.
- Feedback on existing research? Update appropriately.
- Email request? Transfer to email agent.

Use your intelligence to decide which tools to use and when.

Always output only the final markdown report - no commentary or explanations.
    """
)

#simplify handoff
email_handoff = handoff(
    agent=email_agent,
    input_filter=handoff_filters.remove_all_tools,
    tool_description_override="Send the research report via email to the specified email address"
)

research_manager_agent = Agent(
    name="Research Manager",
    instructions=INSTRUCTIONS,
    model="gpt-4o",
    handoffs=[email_handoff],
    tools=[planner_tool, search_tool, writer_tool]
)

# Research run function
session_store = {}

async def run_research(company: str, industry: str, query: str, feedback: str, email_trigger: str):
    
    #session handling - to ensure session persists    
    session_id = f"research_{company}_{query}"
    if session_id not in session_store:
        session_store[session_id] = SQLiteSession(session_id)
    session = session_store[session_id] 
  
    if hasattr(session, 'trace_id') and session.trace_id:
        trace_id = session.trace_id
    else:
        trace_id = gen_trace_id()
        session.trace_id = trace_id
    
    with trace("Research trace", trace_id=trace_id):
        print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")

        if not feedback and not email_trigger:
            # Initial research
            yield "Researching..."
            
            result = await Runner.run(
                research_manager_agent, 
                f"Research: Company: {company} | Industry: {industry} | Query: {query}",
                session=session
            )
            yield result.final_output
        
        elif feedback and not email_trigger:
            # Feedback processing
            yield "Processing feedback..."
            
            result = await Runner.run(
                research_manager_agent, 
                f"Based on your previous research, here is user feedback: {feedback}\n\n\
                Please update and improve the existing research report based on this feedback. Do not start over - build upon what you already provided.",
                session=session
            )
            yield result.final_output

        elif email_trigger.startswith("EMAIL_REPORT"):
            
            yield "Preparing to email report..."
            
            email_address = email_trigger.split("Email address: ")[1]
            result = await Runner.run(
                research_manager_agent,
                f"The user wants to email the report. Please hand off to the emailer agent to send the final research report and share the email: {email_address}",
                session=session
            )
            yield result.final_output

        else:
            yield "The research process is complete.  Please clear and start again."