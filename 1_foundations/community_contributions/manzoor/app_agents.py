from agents import Agent, Runner, trace, function_tool, tool
from agent_instructions import *

# our model names
openai_model="gpt-4o-mini"
deepseek_model='deepseek-chat'

# Manager Agent oversees the entire React app development process.
manager_agent = Agent(name='Manager Agent', instructions=manager_instructions,model=openai_model)

developer_agent = Agent(name='Developer Agent', instructions=developer_instructions,model=openai_model)

# Innovator agent comes up with innovative ideas,to solve problems for small business.
innovator_agent = Agent(name="Innovator Agent",instructions=innovator_instructions, model=openai_model)

# Idea Selector Agent selects the best idea from the list, based on solving user's problems and cost considerations.
idea_selector_agent = Agent(name="Idea Selector Agent",instructions=idea_selector_instructions,model=openai_model)

# App File Structure Agent creates the file and folder structure for the React app.
app_file_structure_agent = Agent(name='App Structure Generator Agent',instructions=app_file_structure_instructions,model=openai_model)

# File Structure Evaluator Agent evaluates the generated file structure for completeness and correctness.
file_structure_evaluator_agent = Agent(name='App Evaluator Agent ',instructions=file_structure_evaluator_instructions,model=openai_model)

component_agent = Agent(name='Component Generator Agent',instructions=components_instructions,model=openai_model)
# Page Creator Agent generates the React pages based on the requirements.
page_creator_agent = Agent(name='Page Generator Agent',instructions=pages_instructions,model=openai_model)

# Hook Creator Agent generates custom React hooks for state management and side effects.
hooks_creator_agent = Agent(name='Hooks Generator Agent',instructions=hooks_instructions,model=openai_model)

# Database Creator Agent designs the database schema and relationships.
database_creator_agent = Agent(name='Database Designer Agent',instructions=database_instructions,model=openai_model)

# API Creator Agent generates the backend APIs for data interaction.
api_creator_agent = Agent(name='API Generator Agent',instructions=api_instructions,model=openai_model)

# Payment Handling Agent implements payment gateway integration and handling.
payment_handling_agent = Agent(name='Payment Handler Agent',instructions=payment_instructions,model=openai_model)

# Dependency Generator Agent lists the required dependencies and libraries.
dependencies_generator_agent = Agent(name='Dependency Generator Agent',instructions=dependencies_instructions,model=openai_model)

# Tester Agent tests the developed React app for bugs and issues.
tester_agent = Agent(name='QA Tester Agent',instructions=tester_instructions,model=openai_model)
