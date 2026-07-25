## Prerequisite 
### Install Homebrew 
### Install Git

### Install Cursor
* Visit cursor at https://www.cursor.com/
* Click Sign In on the top right, then Sign Up, to create your account
* Download and follow its instructions to install and open Cursor

### Install UV 
* UV is better python package manager to manage the python projects. It is better than conda and pip.
* Instead of pip install xxx you do uv add xxx - it gets included in your pyproject.toml file and will be automatically installed next time you need it
* Instead of python my_script.py you do uv run my_script.py which updates and activates the environment and calls your script
* You don't actually need to run uv sync because uv does this for you whenever you call uv run
* It's better not to edit pyproject.toml yourself, and definitely don't edit uv.lock. If you want to upgrade all your packages, run uv lock --upgrade
* uv has really terrific docs here - well worth a read!

## Project Initialization
* Create the project root. In the context of current project the project_root is deep-research-ai-agent. 
    * mkdir deep-research-ai-agent
    * cd deep-research-ai-agent
* Create the scalaton project 
    * uv init
* Update the python version to 3.12
    * uv python install 3.12
    * uv python pin 3.12
    * uv sync  
* Don't edit the pyproject.toml file mannualy. Instead run following command to add package
    * uv add "gradio>=5.22.0"
    * uv add pytest --dev
    * uv add "python-dotenv>=1.0.1"
    * uv add "sendgrid>=6.11.0"
    * uv add "ipywidgets>=8.1.5",
    * uv add "ipywidgets>=8.1.5"
    * uv add "openai-agents>=0.0.15"
    * uv add "ipykernel>=6.29.5" --dev
    * uv sync
* Create following folders
    * agents - This folder will hold all the agents
    * tools - This folder will hold all the tools
    * models - This folder will hold all the model objects
    * notebook - This folder will hold all the python notebooks for testing.
* Setup git
    * git init

## Setup external integrations
### Setup OpenAI Account
* Create OpenAI account https://platform.openai.com/. You can use gmail SSO.
* Purchase $5 worth of tokens
* Create Project. I gave the project name 'mogo-ai'
* Create an API Key and assign this to mogo-ai.
* Save the API key for future use. In production system, we will save this in AWS Secrete Manager.

### Setup Google Gemini Account
* Go to Google AI Studio - https://aistudio.google.com/
* Create the Project
* Create an API Key
* Save the API key for future use. In production system, we will save this in AWS Secrete Manager.

### Setup Sendgrid Account
* Create Sendgrid account https://sendgrid.com. You can use gmail SSO.
* Create verified send email account. I have used mohan.goyal@mogomantra.com
* Verify the sender account
* Create an API key
* Save the API key for future use. In production system, we will save this in AWS Secrete Manager.

## Setup the local environment.
* For local development create .env file in the project_root i.e. deep-research-ai-agent
* Add following keys
    * OPENAI_API_KEY
    * GOOGLE_API_KEY
    * SENDGRID_API_KEY
* Add the file to gitignore so that the file is not accidently checked into the source code.

## Development Processes
* First create a file using python notebook.
* Test the flow
* Convert it to python modules
* Run and test the python modules using uv run command   

## Deployment Processes