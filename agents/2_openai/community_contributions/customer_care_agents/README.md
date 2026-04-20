# Customer Care Agent – Google ADK Project

This project is a **Customer Care Agent** developed using the **Google ADK (Agent Development Kit)**. The primary goal of this project is to demonstrate an AI agent's capability to assist customers with queries related to perfume products.

## 🧪 Project Features

- A **dummy dataset** of perfume products is generated at runtime.
- The dataset can be saved as an **Excel file** and reloaded into a pandas DataFrame.
- This allows users to **cross-check the agent’s responses** against the product information.

## 🚀 Getting Started

### 1. Install Requirements

Make sure you have [**uv**](https://github.com/astral-sh/uv) installed, then run:

```bash
uv add google-adk pandas
```

### 2. Set Up Environment Variables
Create a .env file in the root of the project using the provided .env-example as a template:

```bash
cp .env-example .env
```
Fill in the required API keys and configuration values inside the .env file.

### 3. Run the Web Interface

Navigate to the community-contributions directory and run:
Make sure you are standing in community contributions directory
Directory should look like this

agents\2_openai\community_contributions>

```bash
uv run adk web
```

### 4. Interact with the Agent
You can now access the web interface and interact with the AI customer care agent. Ask questions about the perfume products, and the agent will respond based on the generated dataset.

📁 Notes
The product data is randomly generated each run, but you can export it to Excel.

You can reload the saved Excel file into a DataFrame to cross-check the accuracy of the agent's answers.

