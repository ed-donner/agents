from app_agents import *
from agent_handoff import *

# Tools for Developer agent
component_tool = component_agent.as_tool(tool_name='Component Generator', tool_description='Use this tool to generate React components based on the app requirements.'),

page_tool = page_creator_agent.as_tool(tool_name='Page Generator', tool_description='Use this tool to generate React pages based on the app requirements.'),

hooks_tool = hooks_creator_agent.as_tool(tool_name='Hooks Generator', tool_description='Use this tool to generate custom React hooks for state management and side effects.'),

database_tool = database_creator_agent.as_tool(tool_name='Database Designer', tool_description='Use this tool to design the database schema and relationships.'),

api_tool = api_creator_agent.as_tool(tool_name='API Generator', tool_description='Use  this tool to generate the backend APIs for data interaction.'), 

payment_tool = payment_handling_agent.as_tool(tool_name='Payment Handler', tool_description='Use this tool to implement payment gateway integration and handling.'),

dependencies_tool = dependencies_generator_agent.as_tool(tool_name='Dependency Generator', tool_description='Use this tool to list the required dependencies and libraries.'),

tester_tool = tester_agent.as_tool(tool_name='QA Tester', tool_description='Use this tool to test the developed React app for bugs and issues.'), 

# Tools for developer agent
developer_agent_tools = [
component_tool,
page_tool,
hooks_tool,
database_tool,
api_tool,
payment_tool,
dependencies_tool,
tester_tool,
]

developer_agent.tools=developer_agent_tools
