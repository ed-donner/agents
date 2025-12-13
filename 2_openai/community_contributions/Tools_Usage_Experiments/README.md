## WARNINGS AND DISCLAIMERS

Executing the code in this tutorial may result in fees from token
usage due to use of the OpenAI API and OpenAI Agents SDK. By executing
the code in this tutorial you understand this and accept that there
may be some such costs.

The code in this tutorial is provided for education and illustrative
purposes and is in no way production quality code. Do not use this
code in production systems without adequate testing and enhancement,
in order to ensure such code is robust and suitable for use in a
production environment. You assume all responsibility for use of this
code outside of this tutorial environment.

## Experiments with OpenAI Agents and Tools

This program takes you through a series of experiments designed
to help you understand how to use tools, handoffs, and guardrails
with OpenAI Agents. 

Much of what you will learn is how prompts are key to getting 
agents to work properly with tools. Often your agents will not
call tools because of insufficient prompts. Getting agentic 
systems to work as designed often comes down to experimenting
with prompts, until you figure out what works. 

Over time, you will develop an intuition around crafting good
prompts, but as each agent is different, you need to put in the
time to experiment and see what works. Remember, you are dealing
with LLMs that have been trained with data and simply respond to
your prompts. This is not programming, this is data science!

Often, the experiments will progress, from scenarios in which the
agents do not work, due to insufficient prompts, toward prompts
which enable the agents to work as designed.

Along the way, examples of using tools, handoffs, and guardrails
are introduced.

## Setup

To use this tutorial you must install the uv virtual environment
for Python, and you need to add a variety of Python packages.

Because uv is being used, and because the pyproject.toml file
lists required packages, you may be able to simply execute:

uv sync

But you may need to ask ChatGPT or your favorite chatbot for
help if you execute the scripts.

You need to create an environment variable PROJECT_ENV_PATH
that points to your .env file that contains the OPENAI_API_KEY
environment variable. 

## Running the Experiments

Due to the way the uv project is set up, you may need to 
execute the experiments like this:

uv run -m Tools_Usage_Experiments.1_no_tools.main
uv run -m Tools_Usage_Experiments.2_simple_tool.main