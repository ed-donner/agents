# Welcome to CrewAI week!

## Installing Crew

__Windows users: be sure to have installed the MS Build Tools per initial setup instructions otherwise you’ll get a complex error involving chroma when you install crewai. Here are [instructions](https://chatgpt.com/share/67b0b762-327c-8012-b809-b4ec3b9e7be0). A student also mentioned that [these instructions](https://github.com/bycloudai/InstallVSBuildToolsWindows) might be helpful for people on Windows 11.__

To start, run this command in the project root (agents):

`uv tool list`

To see the tools you have installed in your environment. If you have the crewai tool, then uninstall it with:

`uv tool uninstall crewai`

Now install crewai, and if you use this then you will have EXACTLY the same version as me:

`uv tool install crewai==1.14.4`

And then do `uv tool list` to confirm you have CrewAI 1.14.4!

If you want, you could use the latest version (just don't pin to 1.14.4) but then you might encounter changes - CrewAI does sometimes make breaking changes.

If you'd like to use Coding Agents to help with CrewAI, then here are instructions:  

1. Install node if you don't have it on your system:
https://nodejs.org/en/download

2. Run this command:  
`npx skills add crewaiinc/skills`

## How to work together

See CrewAI docs here: https://docs.crewai.com/en/introduction

My projects are all in this directory:

`agents/3_crewai/reference/`

You should create your versions in:

`agents/3_crewai/coursework`

And copy across prompts from the reference implementation to save time.

## Creating a CrewAI project

From the `3_crewai` directory:

`crewai create crew [project_name]`

## Community Contributions

It would be great to see your PRs in community_contributions! But please trim back the projects - make them concise.

## Docker for the coding crews

Two of the reference crews, `coder` and `engineering_team`, run the code their agents write inside a Docker container, so anything generated stays sandboxed away from your machine. To run those two projects you'll need Docker installed and running first (the other crews don't need it).

Install Docker Desktop here, then start it so the Docker engine is running before you `crewai run`:

https://www.docker.com/products/docker-desktop/

On Linux, use Docker Desktop for Linux from that page, or install Docker Engine directly: https://docs.docker.com/engine/install/

The first run downloads the container image, so give it a minute the first time.