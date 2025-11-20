## Master AI Agentic Engineering -  build autonomous AI Agents

### 6 week journey to code and deploy AI Agents with OpenAI Agents SDK, CrewAI, LangGraph, AutoGen and MCP

![Autonomous Agent](assets/autonomy.png)

_If you're looking at this in Cursor, please right click on the filename in the Explorer on the left, and select "Open preview", to view the formatted version._

I couldn't be more excited to welcome you! This is the start of your 6 week adventure into the powerful, astonishing and often surreal world of Agentic AI.

### Before you begin

I'm here to help you be most successful! Please do reach out if I can help, either in the platform or by emailing me direct (ed@edwarddonner.com). It's always great to connect with people on LinkedIn to build up the community - you'll find me here:  
https://www.linkedin.com/in/eddonner/  
And this is new to me, but I'm also trying out X/Twitter at [@edwarddonner](https://x.com/edwarddonner) - if you're on X, please show me how it's done 😂  

### The not-so-dreaded setup instructions

Perhaps famous last words: but I really, truly hope that I've put together an environment that will be not too horrific to set up!

- Windows people, your instructions are [here](setup/SETUP-PC.md)
- Mac people, yours are [here](setup/SETUP-mac.md)
- Linux people, yours are [here](setup/SETUP-linux.md)

Any problems, please do contact me.

### Important notes for CrewAI week (Week 3)

Windows PC users: you will need to have checked the "gotcha #4" at the top of the [SETUP-PC](setup/SETUP-PC.md) instructions -- installing Microsoft Build Tools.  
If you don't do this, then CrewAI will fail with an obscure error involving Chroma..


Then, you will need to run this command in a Cursor Terminal in the project root directory in order to run the Crew commands:  
`uv tool install crewai`   
And in case you've used Crew before, it might be worth doing this to make sure you have the latest:  
`uv tool upgrade crewai`  

Then please keep in mind for Crew:

1. There are two ways that you can work on the CrewAI project in week 3. Either review the code for each project while I build it, and then do `crewai run` to see it in action. Or if you prefer to be more hands-on, then create your own Crew project from scratch to mirror mine; for example, create `my_debate` to go alongside `debate`, and write the code alongside me. Either approach works!  
2. Windows users: there's a new issue that was recently introduced by one of Crew's libraries. Until this is fixed, you might get a "unicode" error when you try to run `crewai create crew`.  If that happens, please try running this command in the Terminal first: `$env:PYTHONUTF8 = "1"`  
3. Gemini users: in addition to a key in your `.env` file for `GOOGLE_API_KEY`, you will need an identical key for `GEMINI_API_KEY`

### Super useful resources

- The course [resources](https://edwarddonner.com/2025/04/21/the-complete-agentic-ai-engineering-course/) with videos
- Many essential guides in the [guides](guides/01_intro.ipynb) section
- The [troubleshooting](setup/troubleshooting.ipynb) notebook  
- My overall [FAQ](https://edwarddonner.com/faq) page with common issues and questions

### API costs - please read me!

This course does involve making calls to OpenAI and other frontier models, requiring an API key and a small spend, which we set up in the SETUP instructions. If you'd prefer not to spend on API calls, there are cheaper alternatives like DeepSeek and free alternatives like using Ollama!

Details are [here](guides/09_ai_apis_and_ollama.ipynb).

Be sure to monitor your API costs to ensure you are totally happy with any spend. For OpenAI, the dashboard is [here](https://platform.openai.com/usage).

### ABOVE ALL ELSE -

Be sure to have fun with the course! You could not have picked a better time to be learning about Agentic AI. I hope you enjoy every single minute! And if you get stuck at any point - [contact me](https://www.linkedin.com/in/eddonner/).