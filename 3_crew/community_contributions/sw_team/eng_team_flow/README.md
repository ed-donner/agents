# Software Engineer Team

I have implemented a software engineer team using CREWAI Flows. This team consists of 
one business personal, one technical manager, 1 software engineer and 1 tech lead agents.
It has a self eval loop between business personal and tech manager wherein tech manager 
upto 3 times can ask clarifications.
Tech manager then creates task for software engineer to develop.
Software engineer once done with code generation passes the code to the tech lead to review.
Tech lead upto 3 times can ask software engineer to do code improvements.
Agents used:
gpt-4o-mini     - business personal
gpt-40          - tech manager
claude-sonnet-4 - software engineer / tech lead


Challenges:
* Even after good enough prompt hallucinations are witnessed.
* Engineering tasks can at time show up to be very length contextually even though LLM shows it as it very quick to implement.
* CrewAI itself is slow to initiate.
* The output on the console is very decent.
* Crew is difficult to initiate with but once you get the flow, its fun and still has problems with hardcoded requirements in the framework itself.
* Output from LLM is curbed at times - this is one thing I am trying to fix.
* I have used state to save and use generated output. But, I believe memory will be a better option - Need to explore this as well.