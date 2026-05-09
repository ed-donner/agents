# Software Engineer Team


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
