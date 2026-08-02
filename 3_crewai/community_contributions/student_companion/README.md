# StudentCompanion Crew

StudentCompanion is a small Crewai based implementation that helps to carefully generate a study plan for the topic given by the user. There are multiple agents in the setup which are designed for specific tasks. <br>
* `intent_recognizer` - This agent is responsible for analysing the input given by the user and returns the topic, difficulty level and additional info (if any) from the question in a structured json format.
* `topic_generator` - This agent will analyse the topic given by the previous agent and generates a comprehensive list of sub-topics to be covered for the given topic.
* `study_content_generator` - This agent will generate study content for each of the sub-topics suggested by the previous agent. While generating the content, it will also consider the difficulty level and additional info (if any) given by the user.
* `question_generator` - This agent analyses the study content generated so far and generates some questions for the user to answer, enabling a thorough understanding of the topic.
* `output_parser` - This agent will convert the response generated till now from json object to markdow for rendering.


## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```
### Customizing

**Add your API secrets into the `.env` file**

- Modify `src/student_companion/config/agents.yaml` to define your agents
- Modify `src/student_companion/config/tasks.yaml` to define your tasks
- Modify `src/student_companion/crew.py` to add your own logic, tools and specific args
- Modify `src/student_companion/main.py` to add custom inputs for your agents and tasks

This project uses `gemini/gemini-2.0-flash-001` as the LLM and `SerperDevTool`.
If you are using gemini, make sure you add the required dependency using 
```
uv add "crewai[google-genai]"
```

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ crewai run
```

This command initializes the student_companion Crew, assembling the agents and assigning them tasks as defined in your configuration.

You will be prompted to enter the topic which you want to learn. Enter the topic and crew execution will start.

The outputs from all the individual agents will be stored in the `./outputs` folder

## Understanding Your Crew

The student_companion Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding the StudentCompanion Crew  - drop me an email on surbhit3812@gmail.com. Feel free to connect on Linkedin https://www.linkedin.com/in/surbhit-kumar/.

