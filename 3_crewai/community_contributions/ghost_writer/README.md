[![Python CI](https://github.com/DeanPhillipsOKC/ghost_writer/actions/workflows/python-ci.yml/badge.svg?branch=main)](https://github.com/DeanPhillipsOKC/ghost_writer/actions/workflows/python-ci.yml)

# Ghost Writer

[**Ghost Writer**](https://github.com/DeanPhillipsOKC/ghost_writer) is a modular, multi-agent AI framework built on top of [crewAI](https://crewai.com). It enables the orchestration of multiple AI agents to collaboratively tackle complex tasks, maximizing efficiency and intelligence through structured collaboration.



![Ghost Writer](./assets/ghost_writer_logo.png)

## 🚀 Features

- **Multi-Agent Collaboration**: Coordinate multiple AI agents to work together seamlessly.
- **Modular Architecture**: Easily customize and extend agents, tools, and workflows.
- **Powered by crewAI**: Leverages the robust capabilities of the crewAI framework for agent management.
- **Environment Configuration**: Utilize `.env` files for secure and flexible environment variable management.

## 🛠️ Installation

### Prerequisites

- Python >= 3.10 and < 3.13
- [uv](https://docs.astral.sh/uv/) for dependency management

### Steps

1. **Install uv** (if not already installed):

   ```bash
   pip install uv
   ```

2. **Clone the repository**:

   ```bash
   git clone https://github.com/DeanPhillipsOKC/ghost_writer.git
   cd ghost_writer
   ```

3. **Install dependencies**:

   ```bash
   uv pip install -r requirements.txt
   ```

   Alternatively, if using the `crewAI` CLI:

   ```bash
   crewai install
   ```

4. **Set up environment variables**:

   Create a `.env` file in the root directory and add your OpenAI API key:

   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## 🧩 Customization

- **Agents Configuration**: Modify `src/ghost_writer/config/agents.yaml` to define and customize your AI agents.
- **Task Definitions**: Update `src/ghost_writer/config/tasks.yaml` to specify the tasks your agents will perform.
- **Tool Integrations**: Extend `src/ghost_writer/tools/` with custom tools to enhance agent capabilities.

## 🤖 Agent Pipeline

The GhostWriter Crew operates in a structured pipeline. Each agent has a distinct role:

1. **Idea Developer**: Takes a seed of an idea and develops it into a compelling concept with depth and richness
2. **Plot Developer**: Explors the rising action, climax, falling action, and resolution of the story.
3. **Character Developer**: Creates multi-dimensional characters with emotional arcs that resonate with readers.
4. **Outline Developer**: Creates detailed outline of the novel, including chapter breakdowns and key events.
5. **Author**: Writes the novel based on the developed outline, characters, and plot

These agents work together to automate the creative process from ideation to production.

## 📁 Project Structure

```
ghost_writer/
├── src/
│   └── ghost_writer/
│       ├── config/
│       │   ├── agents.py
│       │   └── tasks.py
│       ├── services/
│       └── tools/
|       └── utils/
├── .env
├── pyproject.toml
├── uv.lock
└── README.md
```

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your enhancements.

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---
