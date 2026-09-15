innovator_handoff= """
Here is a list of innovative ideas using AI to solve pain points for small businesses. 
You will handoff these ideas to the Idea Selector agent to select the best one."""

idea_selector_handoff= """ 
I have selected the best idea that will help small businesses. 
You will handoff this idea to the  app structure agent to create a complete file structure for this idea.
"""

app_structure_handoff = """
I've generated, a clear and well-organized React app file structure based
on the project requirements. You will handoff this structure to the Developer agent
to write the source code for each file in the structure. Make sure the developer agent also 
also has access to the structure, or our conversation history. 
"""

database_handoff = """ 
I've created the backed database schemas according to the project requirements. 
All the tables have been defined with appropriate column name, data types, and constrains. 
Relationships between tables are properly established with foreign keys when necessary.You will 
handoff this schema to the Developer agent to save the database schema.
"""

api_creator_handoff = """" 
I've completed the API source code according to the specifications provided.
Please review the code carefully for correctness, and completeness. You will handoff this 
code to the Developer agent to add the API source code files in the final JSON app source code.
"""

developer_handoff = """ 
I've written source code for each file_name in the structure. I've used my tool to 
save the content for each file_name. You can open each directory to review the source code. 
"""
structure_verifier_handoff = """
I've check the structure for for format issues, and errors. Use it to create file structure from it. 
"""
qa_tester_handoff = """ 
I've completed the testing of all the source code and verified the functionality of each component.
The following is a summary of the test results: 
- All implemented functions executed successfully without errors.
_ Input validation and error handling performed as expected.

Here're detailed breakdown of individual test results.
"""
