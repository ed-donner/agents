WARNING: EXECUTING THIS SYSTEM CONSUMES OPENAI TOKENS. 
AI AGENTS HAVE BEEN KNOWN TO LOOP, WHICH CAN RESULT IN
UNEXPECTED INCREASED TOKEN USAGE. DO NOT EXECUTE THIS
SYSTEM UNLESS YOU ACKNOWLEGE THE RISK OF TOKEN USAGE,
AND THUS COST, AND YOU ACCEPT RESPONSIBILITY FOR THE RESULT.

WARNING: THE CODE IN THE SYSTEM IS FOR EDUCATIONAL AND 
ILLUSTRATIVE PURPOSES, AND IS NOT DESIGNED TO BE USED IN
PRODUCTION SYSTEMS. IN USING THIS CODE YOU ACCEPT 
RESPONSIBILITY FOR CONSEQUENCES OF USING THE CODE.

## Customer Support Agent

This application illustrates using guardrails in agentic AI systems
to protect against undesirable inputs and outputs.

This application also illustrates using agents as tools,
and handoffs in agentic systems.

The system uses a main agent acting as a customer support
agent for a university. This agent fields questions from
users and provides general information on a variety of topics.

Two guardrails are used to ensure the customer supoort agent
does not disclose personal information about any person.

An input guardrail ensures that user messages requesting 
personal information are detected, upon which a handoff is
made to an agent that informs the user that personal information
cannot be disclosed. This is overkill as such a message could 
simply be returned when the input guardrail is triggered,
but this provides an opportunity to illustrate handoffs.

An output guardrail ensures that if the user is able to 
successfully bypass the input guardrail, the output is 
prevented from containing content that resembles personal
information.

Additional handoffs are in place to handle situations where
the support agent cannot provide requested information in
detail, and the user is handed off to a specialized support
agent for a department such as admissions, financial aid,
student housing, etc.

## System Setup

This project uses the uv virtual environment. You may need to execute 
the following commands to install the uv virtual environment tool
and Python packages.

- pip install uv
- uv add python-dotenv
- uv add "openai>=1.55.0b0" "openai-agents>=0.0.23" --pre
- additional "uv add" commands for other packages if you get errors

To start this agentic AI system you execute:

uv run main.py

To stop the system press Ctrl + d

Note: you need an environment variable PROJECT_ENV_PATH that provides
the path to your .env file which contains your OPENAI_API_KEY property.
This is necessary because this program uses the uv virtual environment.