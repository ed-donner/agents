# Software Engineer Team

folder: eng_team_flow

I have implemented a software engineer team using CREWAI Flows. This team consists of 
one business personal, one technical manager, 1 software engineer and 1 tech lead agents.
It has a self eval loop between business personal and tech manager wherein tech manager 
upto 3 times can ask clarifications.
Tech manager then creates task for software engineer to develop.
Software engineer once done with code generation passes the code to the tech lead to review.
Tech lead upto 3 times can ask software engineer to do code improvements.
Agents used:
gpt-4o-mini     - business personal
gpt-4o          - tech manager
claude-sonnet-4 - software engineer / tech lead


Challenges and findings:
* Even after good enough prompt hallucinations are witnessed.
* Engineering tasks can at time show up to be very length contextually even though LLM shows it as it very quick to implement.
* CrewAI itself is slow to initiate.
* The output on the console is very decent.
* Crew is difficult to initiate with but once you get the flow, its fun and still has problems with hardcoded requirements in the framework itself.
* Output from LLM is curbed at times - this is one thing I am trying to fix.
* I have used state to save and use generated output. But, I believe memory will be a better option - Need to explore this as well.

<img width="1884" height="938" alt="image" src="https://github.com/user-attachments/assets/7569267a-eb28-4e57-a328-34951b567029" />



folder: eng_team_flow_se_agents_combined

I have implemented a software engineer team using CREWAI Flows. This team consists of 
one business personal, one technical manager, 1 software engineer, 1 tech lead and 1 code summarizer agents.
THE MAIN DIFFERENCE FROM THE PREVIOUS ONE IS SOFTWARE ENGINEER, TECH LEAD AND CODE SUMMARIZER ARE ALL THE PART 
OF THE SAME CREW TO EASE CONTEXT MAAGEMENT AND TO SEE IF THE FLOW CHANGE HELPS.
It has a self eval loop between business personal and tech manager wherein tech manager 
upto 3 times can ask clarifications.
I did enable delegation and see if it improes the output, but result shows not much of help comes up. Maybe I should approach in a different manner possibly.
Tech manager then creates task for software engineer to develop.
For every tas:
*   Software engineer once done with code generation passes the code to the tech lead to review.
*   Tech lead passes the context to code summarizer.
*   The output from code summarizer is fed to the software engineer again.
The loop goes on for either max 2 times or if the code generated is correct according to the tech lead. 

Agents used:
gpt-4o-mini     - business personal
gpt-4o          - tech manager
gpt-4o - software engineer / code summarizer
claude-sonnet-4 - tech lead


Imporovements and Findings:
*   Passing the context from summzrizer to the agent actually improved code quality.
*   Using hetero agents did work good. Claude being a better code generator did make gpt improve.
*   Prompt tweaks did work but can work better.
*   Letting LLM use memory does imporve it run in iterations suggesting the fact that either make the prompt heavy or provide summarized learnings at places necessary.
*   Rate limit application is a serious need.
*   Respecting token limits of a LLM model is the main requirement. Not doing it shows side-effects very clearly.
*   Task breakdown and summary helps improve a lot in general.




THIS SOLUTION IS STILL NOT FOOL PROOF DUE TO LLM'S OWN LIMITATIONS BUT WORKS IF YOU WANT SOMETHING SIMPLE TO BE IMPLEMENTED.
