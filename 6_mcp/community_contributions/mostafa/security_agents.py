from agents import Agent, Tool 
from security_templates import researcher_instructions, system_administrator_instructions, system_expert_instructions



async def get_researcher(mcp_server, model_name):
    researcher = Agent(
        name=f"{model_name}_researcher",
        instructions=researcher_instructions('linux vulnerabilities'),
        model=model_name,
        mcp_servers=[mcp_server]
    )
    return researcher


async def get_researcher_tools(mcp_server, model_name) -> Tool:
    researcher_agent = await get_researcher(mcp_server, model_name)
    researcher_tool = researcher_agent.as_tool(
        tool_name='researcher',
        tool_description=f'Use this tool to gather credible information about a security topic from the web.'
    )
    return researcher_tool


async def get_system_administrator(mcp_server, model_name):
    researcher = await get_researcher_tools(mcp_server, model_name)
    administrator = Agent(
        name=f"{model_name}_administrator",
        instructions=system_administrator_instructions,
        model=model_name,
        mcp_servers=[mcp_server],
        tools=[researcher]
    )
    return administrator

async def get_system_administrator_tools(mcp_server, model_name) -> Tool:
    administrator_agent = await get_system_administrator(mcp_server, model_name)
    administrator_tool = administrator_agent.as_tool(
        tool_name='administrator',
        tool_description=f'Use this tool to identify potential vulnerabilities in a Linux system.'
    )
    return administrator_tool

async def get_security_expert(mcp_server, model_name):
    administrator = await get_system_administrator_tools(mcp_server, model_name)
    researcher = await get_researcher_tools(mcp_server, model_name)

    security_expert = Agent(
        name=f"{model_name}_security_expert",
        instructions=system_expert_instructions,
        model=model_name,
        tools=[administrator, researcher]
    )
    return security_expert


