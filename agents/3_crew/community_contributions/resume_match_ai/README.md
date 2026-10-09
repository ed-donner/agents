# ResumeMatchAi Crew

Welcome to the ResumeMatchAi Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

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

**Add your `MODEL` into the `.env` file**
**Add your `ANTHROPIC_API_KEY` into the `.env` file**

- Modify `src/resume_match_ai/config/agents.yaml` to define your agents
- Modify `src/resume_match_ai/config/tasks.yaml` to define your tasks
- Modify `src/resume_match_ai/crew.py` to add your own logic, tools and specific args
- Modify `src/resume_match_ai/main.py` to add custom inputs for your agents and tasks

## Running the Project

Go to this project directory
```bash
$ cd 3_crew/community_contributions/resume_match_ai
```

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:
```bash
$ crewai run
```

This command initializes the resume-match-ai Crew, assembling the agents and assigning them tasks as defined in your configuration.

will run the create the following files
- `output/analyst_report.md`
- `output/job_matching_report.md`,
- `output/job_scraping_report.md`
- `output/resume_advising_report.md`


## Running the Test
```bash
crewai test --n_iterations 1 --model claude-3-haiku-20240307
```

# Resume Match AI

CrewAI App
[Resume Match CrewAI](https://resume-match-ai-599528b1-cf57-446a-8922-4b5-ec219a74.crewai.com)
A production-ready CrewAI application that intelligently matches resumes to job descriptions using multi-agent AI systems. The app analyzes resume content and job requirements to provide compatibility scores and detailed matching insights.


Gradio App Demo
[Resume Match AI](https://huggingface.co/spaces/kenneth-andales/resume-match-ai)
Interactive Gradio interface deployed on Hugging Face Spaces that integrates with the CrewAI backend API. This user-friendly demo allows users to upload resumes and job descriptions to instantly see matching scores and compatibility analysis in a clean, accessible web interface.
