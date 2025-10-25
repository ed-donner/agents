from app_agents import *

# Pass the ideas to the agent so it can select the best one
innovator_agent.handoffs = [developer_agent]
innovator_agent.handoff_description="Here is a list of innovative ideas to solve for small business problems. You will handoff these ideas to the Idea Selector agent to choose the best one."

# Create the app file structure for the selected idea
idea_selector_agent.handoffs= [developer_agent]
idea_selector_agent.handoff_description="I have selected the best idea for the React app. You will handoff this idea to the App File Structure Generator agent to create the file structure."

# Double check if the file structure needs more modification 
app_file_structure_agent.handoffs=[developer_agent]
app_file_structure_agent.handoff_description="""I have created the app file structure for the selected idea.
You will handoff this structure to the File Structure Evaluator agent to evaluate its completeness and correctness."""

# Hand the developer agent the final app structure for development 
file_structure_evaluator_agent.handoffs=[developer_agent]
file_structure_evaluator_agent.handoff_description="""The app file structure has been evaluated and is ready for development.
You will handoff this structure to the Developer agent for implementation."""

# Now these agents will handoff their work to the developer agent for implementation
component_agent.handoffs = [developer_agent]
component_agent.handoff_description="""These are the generated React components based on the app requirements. 
You will handoff these components to the Developer agent."""

# Page Creator Agent handoffs to Developer Agent it's work
page_creator_agent.handoffs = [developer_agent]
page_creator_agent.handoff_description="""I have generated the React pages based on the app requirements. 
You will handoff these pages to the Developer agent."""

# Hook Creator Agent handoffs to Developer Agent it's work
hooks_creator_agent.handoffs = [developer_agent]
hooks_creator_agent.handoff_description="""These are the generated React hooks based on the app requirements. 
You will handoff the generated hooks to the Developer agent."""

# Database Creator Agent handoffs to Developer Agent it's work
database_creator_agent.handoffs = [developer_agent]
database_creator_agent.handoff_description="""These are the database schema and relationships for the app.
You will handoff this to the Developer agent."""

# API Creator Agent handoffs to Developer Agent it's work
api_creator_agent.handoffs = [developer_agent]
api_creator_agent.handoff_description="""Here are the backend APIs for data interaction.
You will handoff this to the Developer agent."""

# Dependency Generator Agent handoffs to Developer Agent it's work
dependencies_generator_agent.handoffs = [developer_agent]
dependencies_generator_agent.handoff_description="""Dependency list for the React app development.
Please handoff this to the Developer agent."""

# Payment Handling Agent handoffs to Developer Agent it's work
payment_handling_agent.handoffs = [developer_agent]
payment_handling_agent.handoff_description="""The payment integration and Stripe payment handling code is ready. 
You will handoff this to the Developer agent."""

# Tester Agent handoffs to Developer Agent it's work
tester_agent.handoffs = [developer_agent]
tester_agent.handoff_description="""The QA testing results and bug reports for the React app are ready. 
You will handoff this to the Developer agent."""
