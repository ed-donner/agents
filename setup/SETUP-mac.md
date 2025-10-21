## Master AI Agentic Engineering -  build autonomous AI Agents

# Setup instructions for Mac

Welcome, Mac people!

Setting up a powerful environment to work at the forefront of AI is not as easy as I'd like. It can be challenging. But I really hope these instructions are bullet-proof!

If you hit problems, please don't hesitate to reach out. I am here to get you up and running quickly. There's nothing worse than feeling _stuck_. Message me, email me or LinkedIn message me and I will unstick you quickly!

Email: ed@edwarddonner.com  
LinkedIn: https://www.linkedin.com/in/eddonner/  

_If you're looking at this in Cursor, please right click on the filename in the Explorer on the left, and select "Open preview", to view the formatted version._

### Before we begin

If you're less familiar with using the Terminal, please review this excellent [guide](https://chatgpt.com/canvas/shared/67b0b10c93a081918210723867525d2b) for some details and exercises.

If you're new to developing on your Mac, you may need to install XCode developer tools. Here are [instructions](https://chatgpt.com/share/67b0b8d7-8eec-8012-9a37-6973b9db11f5).

One "gotcha" to keep in mind: if you run anti-virus software, VPN or a Firewall, it might interfere with installations or network access. Please temporarily disable if you have problems.

### Part 1: Clone the Repo

This gets you a local copy of the code on your box.

1. **Install Git** if not already installed (it will be in most cases)

- Open Terminal (Applications > Utilities > Terminal)
- Type `git --version` If not installed, you'll be prompted to install it

2. **Navigate to your projects folder:**

If you have a specific folder for projects, navigate to it using the cd command. For example:
`cd ~/projects`

If you don't have a projects folder, you can create one:
```
mkdir ~/projects
cd ~/projects
```

3. **Clone the repository:**

Enter this in the terminal in the Projects folder:

`git clone https://github.com/ed-donner/agents.git`

This creates a new directory `agents` within your Projects folder and downloads the code for the class. Do `cd agents` to go into it. This `agents` directory is known as the "project root directory".

### Part 2: Install Cursor

A word about Cursor: it's a cool product, but it's not to everyone's liking. It can also have a habit of being flakey with the AI recommendations. As student Alireza points out, you can use VS Code (or any IDE) in its place if you prefer. Cursor itself is built from VS Code and everything on this course will work fine in either.

1. Visit cursor at https://www.cursor.com/
2. Click Sign In on the top right, then Sign Up, to create your account
3. Download and follow its instructions to install and open Cursor

After you start Cursor, you can pick the defaults for all its questions.  
When it's time to open the project in Cursor:  
1. Launch Cursor, if it's not already running  
2. File menu >> New Window  
3. Click "Open project"  
4. Navigate into the project root directory called `agents` (probably within projects) and click Open or Select Folder
5. When your project opens, you may be prompted to "install recommended extensions" for Python and Jupyter. If so, choose Yes! Otherwise:
- Open extensions (View >> extensions)
- Search for python, and when the results show, click on the ms-python one, and Install it if not already installed
- Search for jupyter, and when the results show, click on the Microsoft one, and Install it if not already installed

Now open the Explorer (View >> Explorer) and Cursor should show each of the weeks in the file explorer on the left.

### Part 3: The amazing `uv`

For this course, I'm using uv, the blazingly fast package manager. It's really taken off in the Data Science world -- and for good reason.

It's fast and reliable. You're going to love it!

Follow the instructions here to install uv - I recommend using the Standalone Installer approach at the very top:

https://docs.astral.sh/uv/getting-started/installation/

Any installation problems with uv, please see [Q11 on my FAQ page](https://edwarddonner.com/faq/#11).

Then within Cursor, select View >> Terminal, to see a Terminal window within Cursor.  
Type `pwd` to see the current directory, and check you are in the 'agents' directory. For me it is `/Users/ed/projects/agents` and it should be something similar for you.

Start by running `uv self update` to make sure you're on the latest version of uv.

And now simply run:  
`uv sync`  
And marvel at the speed and reliability! If necessary, uv should install python 3.12, and then it should install all the packages.  

Any uv problems, please see [Q11 on my FAQ page](https://edwarddonner.com/faq/#11).

Finally, run these commands to be ready to use CrewAI in week 3:  
`uv tool install crewai`   
Followed by:  
`uv tool upgrade crewai`  

Checking that everything is set up nicely:  
1. Confirm that you now have a folder called '.venv' in your project root directory (agents)
2. If you run `uv python list` you should see a Python 3.12 version in your list (there might be several)
3. If you run `uv tool list` you should see crewai as a tool

Just FYI on using uv:  
With uv, you do a few things differently:  
- Instead of `pip install xxx` you do `uv add xxx` - it gets included in your `pyproject.toml` file and will be automatically installed next time you need it  
- Instead of `python my_script.py` you do `uv run my_script.py` which updates and activates the environment and calls your script  
- You don't actually need to run `uv sync` because uv does this for you whenever you call `uv run`  
- It's better not to edit pyproject.toml yourself, and definitely don't edit uv.lock. If you want to upgrade all your packages, run `uv lock --upgrade`
- uv has really terrific docs [here](https://docs.astral.sh/uv/) - well worth a read!

### Part 4: OpenAI Key

This is OPTIONAL - there's no need to spend money on APIs if you don't want to.

But it is strongly recommended for the best performance of your Agentic system.

If you have concerns about API costs and would prefer to use cheap or free alternatives, please see [this guide](../guides/09_ai_apis_and_ollama.ipynb)  
This includes instructions for using OpenRouter instead of OpenAI, which may have a more convenient billing system for some countries.

_If you decide to use the free alternative (Ollama), then please skip the Part 4 and Part 5 of this setup guide; there's no need for an API key or a .env file. Go straight to the section headed "And that's it!" below._

For OpenAI:

1. Create an OpenAI account if you don't have one by visiting:  
https://platform.openai.com/

2. OpenAI asks for a minimum credit to use the API. For me in the US, it's \$5. The API calls will spend against this \$5. On this course, we'll only use a small portion of this. I do recommend you make the investment as you'll be able to put it to excellent use. Do keep in mind: Agentic systems are less predictable than traditional software engineering, and that's usually the intention! It also means there are some risks when it comes to costs. Set a fixed budget for your LLMs, and be sure to monitor costs carefully.

You can add your credit balance to OpenAI at Settings > Billing:  
https://platform.openai.com/settings/organization/billing/overview

I recommend you **disable** the automatic recharge!

3. Create your API key

The webpage where you set up your OpenAI key is at https://platform.openai.com/api-keys - press the green 'Create new secret key' button and press 'Create secret key'. Keep a record of the API key somewhere private; you won't be able to retrieve it from the OpenAI screens in the future. It should start `sk-proj-`.

We will also set up keys for Anthropic and Google, which you can do here when we get there.  
- Claude API at https://console.anthropic.com/ from Anthropic
- Gemini API at https://aistudio.google.com/ from Google

During the course, I'll also direct you to set up a number of other APIs that are free or very low cost.

### Part 5: The `.env` file

When you have the key, it's time to create your `.env` file:

1. In Cursor, go to the File menu and select "New Text File".

Type the following, being SUPER careful that you get this exactly right:

`OPENAI_API_KEY=`

And then after the equals sign, paste in your key from OpenAI. So after you've completed this, it should look like this:

`OPENAI_API_KEY=sk-proj-lots_of_characters_here`

But obviously the stuff to the right of the equals sign needs to match your key exactly.

Some people have got stuck because they've mistyped the start of the key as OPEN_API_KEY (missing the letters AI) and some people have the value as `sk-proj-sk-proj-...`.

If you have other keys, you can add them too, or come back to this in future weeks:  
```
GOOGLE_API_KEY=xxxx
ANTHROPIC_API_KEY=xxxx
DEEPSEEK_API_KEY=xxxx
```

2. Now go to File menu >> Save As.. and save the file in the directory called `agents` (also known as the project root directory) with the name `.env`  

Here's the thing: it **needs** to go in the directory named `agents` and it **needs** to be named precisely `.env` -- not "env" and not "env.txt" or ".env.txt" but exactly the 4 characters `.env` otherwise it won't work!! 

Hopefully you're now the proud owner of your very own `.env` file with your key inside, and you're ready for action.

**IMPORTANT: be sure to Save the .env file after you edit it.**

## And that's it!!

To get started in Cursor, check that you've installed the Python and Jupyter extensions as described in Part 2 above. Then, open the directory called `1_foundations` in the explorer on the left, and double click on `1_lab1.ipynb` to launch the first lab. Click where it says "Select Kernel" near the top right, and select the option called `.venv (Python 3.12.9)` or similar, which should be the first choice or the most prominent choice (you might need to click 'Python Environments' first). Then click in the first cell with code, and press Shift + Enter to execute it.

After you click "Select Kernel", if there is no option like `.venv (Python 3.12.9)` then please do the following:  
1. From the Cursor menu, choose Settings >> VSCode Settings (NOTE: be sure to select `VSCode Settings` not `Cursor Settings`)  
2. In the Settings search bar, type "venv"  
3. In the field "Path to folder with a list of Virtual Environments" put the path to the project root, like /Users/username/projects/agents  
And then try again.


If you have any problems, I've included a Guide called [troubleshooting.ipynb](troubleshooting.ipynb) to figure it out.

Please do message me or email me at ed@edwarddonner.com if this doesn't work or if I can help with anything. I can't wait to hear how you get on.