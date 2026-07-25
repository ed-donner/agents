

# **📘 Homeworker Crew**

Ever found yourself staring at a blank page trying to come up with fresh homework ideas for your students or kids? You’re not alone — and now, you don’t have to struggle anymore. Meet the Assignment Creator, a multi‑agent AI system built with crewAI that collaborates like a tiny digital teaching staff. Powered by [crewAI](https://crewai.com) at its core is a principal agent that intelligently decides which subject‑specialized homework agent is best suited for the task through reasoning. Together, these agents generate personalized assignments, format them beautifully, and deliver them straight to your inbox. Homework creation just got a whole lot easier.

---

## **🚀 System Overview: Homework Assignment Workflow**

This project generates homework assignments for students in **grades 1–10** across three subjects:

- **English**
- **Math**
- **General Studies**

The system uses a multi‑agent CrewAI architecture where:

- A **Principal Agent** selects the appropriate homework‑generation agent.
- The selected agent creates the assignment and writes it to an output file.
- A **mail_composer agent** converts the assignment into an HTML email.
- A **mailer agent** sends the email using **SendGrid**.
- A **Gradio UI** serves as the front-end for user input.


## **🛠 Installation**

Ensure you have **Python >=3.10 <3.14** installed on your system.  
This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

Install `uv` if you haven’t already:

```bash
pip install uv
```

Next, navigate to your project directory and install dependencies:

(Optional) Lock the dependencies and install them using:

```bash
crewai install
```

---

## **⚙️ Customizing**

Add your LLM API Key (e.g `GROQ_API_KEY` or `OPENAI_API_KEY`) into the `.env` file.
For the email functionality to work you'll need a Sendgrid API key. See details [here](https://www.twilio.com/docs/sendgrid/ui/account-and-settings/api-keys). Pass the value as `SENDGRID_API_KEY` into the `.env` file.

You can customize your crew by modifying:

- `src/homeworker/config/agents.yaml` → define your agents  
- `src/homeworker/config/tasks.yaml` → define your tasks  
- `src/homeworker/crew.py` → add logic, tools, and arguments  
- `src/homeworker/main.py` → add custom inputs for agents and tasks  

---

## **▶️ Running the Project**

From the root folder:

```bash
python app.py
```

This initializes the Gradio app at the local endpoint http://127.0.0.1:7860 where you can provide your input.
The app calls the Homeworker Crew, assembles the agents, and executes tasks as defined in your configuration.

The unmodified example will generate a `output` folder which will have a assignment.txt and email.html file. If you have configured email correctly you should receive an email also.

---

## **🧠 Understanding Your Crew**

The Homeworker Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on tasks defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent.

---

## **🔧 Further Enhancements**
Ideas include:
* Richer Assignment Formatting like adding Images, diagrams, or tables.
* Input Validation & Error Handling.
* Add Agent Memory & Assignment History.
* Add Multi‑Topic Assignment Generation.
* Alternative Delivery Channels like downloadable files.
* And more ...

---

## **💬 Support**

For support, questions, or feedback:

- Visit our [documentation](https://docs.crewai.com)
- Reach out via our GitHub repository [(github.com in Bing)](https://www.bing.com/search?q="https%3A%2F%2Fgithub.com%2Fjoaomdmoura%2Fcrewai")
- Join our [Discord](https://discord.com/invite/X4JWnZnxPb)
- Chat with our docs: [https://chat.g.pt/DWjSBZn](https://chat.g.pt/DWjSBZn)

Let’s create wonders together with the power and simplicity of crewAI.

---

