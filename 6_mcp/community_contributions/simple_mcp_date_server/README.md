## Simple date server 

### Create a project
uv init simple_mcp_date_server        
cd simple_mcp_date_server       

### Create the environment 
uv venv      
#### Activate 
source .venv/bin/activate or .venv\Scripts\activate        

### Add dependencies 
uv add mcp anthropic python-dotenv       
        
add API key to the .env file       

### Run 
uv run simple_client.py         
or        
uv run simple_client_llm.py        
