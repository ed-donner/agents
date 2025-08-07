IN USING THE CODE IN THIS EXAMPLE APP, YOU RELEASE GREGORY LAFRANCE
AND ANY ORGANIZATIONS ASSOCIATED WITH HIM FROM ANY LIABILITY RELATED
TO FEES FOR TOKEN USAGE OR ANY OTHER FEES OR PENALTIES INCURRED.

This app is an example of performing deep research using the OpenAI Agent SDK.

It enables you to easily generate novels.

Input parameters you can input include:

- number of pages to generate for the novel
- number of chapters in the novel
- title of the novel
- the general plot of the novel
- maximum tokens to use in creating the novel, after which an error message will be displayed

Here is a general formula for calculating tokens per page:

T ≈ pages * 1600 tokens

Example for a 99 page novel, everything to GPT-4o-mini:
- Total tokens (1600 per page, 99 pages): ~158,400
- Cost (input/output combined):
  - Assume 50% input @ $0.0005 = 79.2K × $0.0005 = $0.04
  - 50% output @ $0.0015 = 79.2K × $0.0015 = $0.12
  - Total = ~$0.16 per book

To run this example you should:
- create a .env file in the project root (outside the GitHub repo!!!) and add the following API keys:
- OPENAI_API_KEY=your-openai-api-key
- install Python 3 (might already be installed, execute python3 --version in a Terminal shell)
- install the uv Python package manager https://docs.astral.sh/uv/getting-started/installation
- clone this repository from GitHub:
    https://github.com/glafrance/agentic-ai.git
- CD into the repo folder deep-research/novel-generator
- uv venv         # create a virtual environment
- uv pip sync     # installs all exact dependencies from uv.lock
- execute the app: uv run main.py

When prompted, enter specifications for the novel to be generated, such as:

- number of pages to generate for the novel
- number of chapters in the novel
- title of the novel
- the general plot of the novel
- maximum tokens to use in creating the novel, after which an error message will be displayed

Note that you can just press Enter to accept the defaults, 
and auto-generated title, novel plot.