simple-tools-usage is a very basic example of using the OpenAI API with a tool.

The "tool" is simply a Python function that:
- reverses the input string
- converts all letters to lowercase
- capitalizes the first letter of each reversed word

The value of this simple example application:
- illustrates using the OpenAI API for an interactive chat app
- shows how to define a tool schema and pass it to the OpenAI API so the LLM can make use of the tool
- shows how to implement an interactive chat session that continues until the user stops it
- shows how to maintain the chat history and pass it with each message, so the LLM is aware

To run this example you should:
- create a .env file in the project root (outside the GitHub repo!!!) and add the following API keys:
- OPENAI_API_KEY=your-openai-api-key
- install Python 3 (might already be installed, execute python3 --version in a Terminal shell)
- install the uv Python package manager https://docs.astral.sh/uv/getting-started/installation
- clone this repository from GitHub:
    https://github.com/glafrance/agentic-ai.git
- CD into the repo folder tools-usage/simple-tools-usage
- uv venv         # create a virtual environment
- uv pip sync     # installs all exact dependencies from uv.lock
- execute the app: uv run main.py

When prompted, enter some text and experience the wonder and excitement of the OpenAI API!