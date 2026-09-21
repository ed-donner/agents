The is an update of the deep research solution from the end of week 2.  Updates:
- Focussed on research for an organisation with company and industry added in addition to query
- Introduction of a research manager agent to orchestrate and review / QA.  I had to use gpt-4o as the results were poor with gpt-4o-mini
- Planner, writer, search and email agents as tools
- Used sessions to allow an initial report be generated in the UI, user feedback for updates, handoff to email agent (based on user confirmation).
- User request to send email and provide email address through UI
- Email agent using gmail rather than sendgrid
- Updates to UI layout

I've kept the .ipynb file that I used to create and test as its useful in anybody wanted to play about with it and make changes.

Note:
As I was putting this together, the instructions for the research manager became quite verbose.  I had spelled out everything in great detail - workflows, handoffs, what needed to be provided to each tool / agent, etc.  I found it didn't feel very agentic!  I decided to vastly simplify the instructions to allow the llm make decisions and the output vastly improved. Its really interesting to see how the llm handles things and the prompts it gives to the agents / tools. There is obviously less control with this approach so if it was ever going to be the basis of a real solution then it would likely need oversight / controls / guardrails!