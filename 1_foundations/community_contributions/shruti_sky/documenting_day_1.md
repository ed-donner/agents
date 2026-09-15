help me convert these notes in .md format
----Day 1: Setup
i) Open VS code (installation of cursor ide was done in the tutorial, but I went and read it on reddit, everyone said its just shit)
ii) Create a folder named project
    mkdir project
    cd project
iii) Clone the github repo
    git clone https://github.com/ed-donner/agents.git agents2
    repo has been cloned, and you will have a agents2 folder inside the project folder
iv) Open the agents2 folder as your project in the vs code
v) Make sure you have python and jupyter notebook extensions installed here
vi) on the internet, go to the uv installation guide 
    and from there copy the command line command for your terminal
    and run
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ( wait,, .. what is uv
      python package manager and project manager created by Astral (the company behind Ruff). It's designed to be a much faster replacement for tools like pip, venv, virtualenv, pip-tools, and even parts of Poetry.

What is uv?

Think of uv as an all-in-one tool for Python development.

With uv, you can:

📦 Install Python packages (like pip)
🏗️ Create and manage projects (like Poetry)
🌐 Create and manage virtual environments (like venv)
🔒 Lock dependencies for reproducible builds
🐍 Install and manage Python versions
⚡ Do all of this much faster because it's written in Rust
      )


    then excecute
    uv venv
venv here refers to a virtual environment that python creates specifically for a project, because many versions, dependencies may work or be compatible with each other in one project might not work for other projects,
so after creating the venv, all the dependencies, libraries installed will be done within the environment, not globally.
    then do
    uv sync (will install all the required packages into the environment)
    
vii) then add that directory to the path
    in cmd  set Path=C:\Users\ss\.local\bin;%Path% 
    (what is a Path?
    Think of PATH as a list of folders that your operating system searches whenever you type a command.
    If you add:

        C:\Users\ss\.local\bin

    to PATH, then from any directory you can simply run:

        uv --version

    instead of:

        C:\Users\ss\.local\bin\uv.exe --version
    )


viii)   create a file named .env ( this will signal vscode to ignore this file so that it doesnt      send           it   across online or anywhere, as here we are going to put our api key, so we don't wanna expose it)

        Adding the api key
        since openApi, claudAi will cost you, I am using gemini api key
        create your own api key
        and then
        paste it in the .env file
        GOOGLE_API_KEY=
        GEMINI_API_KEY=
        second one is just duplicate, because sometimes somethings look for the former, sometimes the latter


            What are the "somethings"?

                They could be:

                An AI framework (e.g., LangChain, CrewAI, LlamaIndex)
                An SDK provided by Google
                A CLI tool
                A VS Code extension
                A sample project from GitHub
                A Python package
                An agent framework


-----excecuting the instructions in python first lab------
ix) in the jupyter notebook, in every lab
     we'll select kernel, kernel is the python that runs behine the notebook
     -select the one with Python .venv ()
     and run the first cell

     After you click "Select Kernel", if there is no option like `.venv (Python 3.12.12)` then please do the following:  
        1. On Mac: From the Cursor menu, choose Settings >> VS Code Settings (NOTE: be sure to select `VSCode Settings` not `Cursor Settings`);  
        On Windows PC: From the File menu, choose Preferences >> VS Code Settings(NOTE: be sure to select `VSCode Settings` not `Cursor Settings`)  
        2. In the Settings search bar, type "venv"  
        3. In the field "Path to folder with a list of Virtual Environments" put the path to the project root, like C:\Users\username\projects\agents (on a Windows PC) or /Users/username/projects/agents (on Mac or Linux).  
        And then try again.

    what excecuting the code cells is doing
    i) importing the dotenv file (.env where the api key is)
    ii) loading that file
    iii) checking if the api key you are going to use exists
    iv) Will import the openAI library
    (Throughout the course, we use APIs for connecting with the strongest LLMs on the planet.

        The companies behind these LLMs, such as OpenAI, Anthropic, Google and DeepSeek, have built web endpoints. You call their models by making an HTTP request to a Web Address and passing in all the information about your prompts.

        But it would be painful if we needed to build HTTP requests every time we wanted to call an API.

        To make this simple, the team at OpenAI wrote a python utility known as a "Python Client Library" which wraps the HTTP call. So you write python code and it calls the web.

        And THAT is what the library openai is.)

    v) Make an instance of it, you'll need to slightly modify it because openAI will look by default for the openai_key, so you change it a bit (follow the guide9, its great) but you will need to hardcode it no other option
    vi) creating a list of messaages to send (openAI accepts them in the form of python list)A Python list is a built-in data type used to store an ordered collection of items inside a single variable
    vii) and now calling the gemini (the guide 9 helped to setup that message to help with the model name to be used, and yeah, till now it is confirmed I am using a free tier model)

********* time for agentic AI calls *******
now we are gonna make calls to the llms where the result of one call will be used as an input to another call

and the quest goes on.
So the homework that has been given is to ask AI to identify a business problem to solve
and then a pain point
and then, on the basis of the pain point and the business problem, come up with a agentic AI solution, and you can submit it in contributions and create a pull request!



## Mistakes I Made day 1

- Installed `uv` but forgot to create the virtual environment.



Some coding learning about API response


---

# API Response & Conversation History

### 1. API Response is **not** a string

When we call the model:

```python
response = client_which_is_gemini.chat.completions.create(
    model="gemini-2.5-flash-lite",
    messages=messages
)

you can also use other models, gemini 3.5 has even higher limits (reason:With every new generation of AI, Google optimizes the underlying architecture and TPU (Tensor Processing Unit) hardware.

Gemini 3.1 Flash Lite is a highly compressed, ultra-efficient model specifically engineered for high-volume, low-latency tasks. 1)
Because it is so highly optimized, it requires significantly less computing power and cost for Google to run per request compared to the older Gemini 2.5 architecture. Google can easily afford to give you 500 free requests of a highly optimized model because it barely dents their server capacity.2. Encouraging Migration to the New PlatformGoogle wants developers building on their newest, most advanced platform. Gemini 3.1 comes with a completely redesigned native reasoning engine (letting you control "thinking levels" from minimal to high) and improved tool integrations.By offering generous free limits on Gemini 3.1, Google incentivizes developers to migrate their projects to the newer version.By contrast, restricting older "legacy" models like Gemini 2.5 to 20 daily requests gently pushes developers away from outdated tech.
```

The model **does not** return just the generated text.

Instead, it returns a **response object** containing several pieces of information, such as:

* Metadata (e.g., response ID)
* Token usage
* Finish reason
* Choices
* Assistant message

A simplified response looks like:

```python
response = {
    "id": "...",
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "If a clockmaker creates..."
            }
        }
    ]
}
```

To access only the generated text, use:

```python
print(response.choices[0].message.content)
```

---

# Roles in Chat APIs

Every message sent to the model has a **role** that identifies who is speaking.

### User

Represents a message sent by the human.

```python
{"role": "user", "content": "How are you?"}
```

### Assistant

Represents a message generated by the AI.

```python
{"role": "assistant", "content": "I'm doing well!"}
```

### System

Provides instructions that guide the model's behavior throughout the conversation.

```python
{"role": "system", "content": "You are a helpful Python tutor."}
```

---

# Conversation History (`messages`)

The model maintains context using a list called `messages`.

Each new message is **appended** (added to the end) of this list.

```python
messages = []

messages.append({"role": "user", "content": "How are you?"})

messages.append({"role": "assistant", "content": "I'm doing well!"})

messages.append({"role": "user", "content": "Tell me a joke."})
```

The conversation history now looks like:

```python
messages = [
    {"role": "user", "content": "How are you?"},
    {"role": "assistant", "content": "I'm doing well!"},
    {"role": "user", "content": "Tell me a joke."}
]
```

When this list is sent back to the model, it can understand the entire conversation and respond with the correct context.

---

### Key Takeaways

* `response` is an **object**, not a string.
* The generated text is accessed using:

  ```python
  response.choices[0].message.content
  ```
* `messages` stores the **entire conversation history**.
* `role` indicates **who spoke the message** (`user`, `assistant`, or `system`).
* Every new message is **appended** to the `messages` list, allowing the model to maintain context across the conversation.



