---
title: Pharma Sidekick
emoji: 📈
colorFrom: pink
colorTo: gray
sdk: gradio
sdk_version: 6.5.1
app_file: app.py
pinned: false
license: mit
short_description: A pharmacist aid in dispensing and prescription analysis
---

# 🩺 Pharma Sidekick: AI Clinical Assistant

**Pharma Sidekick** is an intelligent AI agent designed to assist clinical pharmacists in validating prescriptions. By leveraging autonomous agentic workflows, it acts as a "second pair of eyes" to ensure patient safety and optimize pharmacotherapy.

🔗 **[Live Demo on Hugging Face](https://huggingface.co/spaces/Codypharm/pharma-sidekick)**

## 🚀 Features

Unlike standard chatbots, Sidekick doesn't just generate text. It uses a suite of specialized tools to perform clinical checks before forming a conclusion:

*   **Allergy & Interaction Checking**: Screens for drug-drug interactions and cross-sensitivity with patient allergies.
*   **Dosing Verification**: Validates dosages based on:
    *   **Pediatrics**: Weight-based dosing for children.
    *   **Geriatrics**: Beers Criteria and age-related adjustments.
    *   **Renal Function**: Adjustments for reduced eGFR/CrCl.
*   **Pregnancy & Lactation**: Safety profiles for pregnant or breastfeeding patients.
*   **Data Source**: Utilizes **openFDA** data for authoritative drug information.
*   **Structured Assessment**: Delivers a clear "Dispense" or "Do Not Dispense" verdict with clinical reasoning and recommendations.

## 🏗️ Technical Architecture

This project demonstrates **Agentic AI** engineering concepts:

*   **[LangGraph](https://langchain-ai.github.io/langgraph/)**: Orchestrates the cyclic graph workflow, managing state between the "Worker" (which uses tools) and the "Evaluator" (which ensures quality).
*   **[OpenAI GPT-4o](https://openai.com/)**: Provides the reasoning and clinical judgment capabilities.
*   **[Gradio](https://gradio.app/)**: Powers the interactive web interface.
*   **[openFDA](https://open.fda.gov/)**: Source for regulatory drug data.

## 🛠️ Installation & Usage

### Prerequisites
*   Python 3.10+
*   An OpenAI API Key

### Steps

1.  **Clone the repository**
    ```bash
    git clone https://github.com/codypharm/pharma-sidekick.git
    cd pharma-sidekick
    ```

2.  **Set up environment variables**
    Create a `.env` file in the root directory:
    ```bash
    OPENAI_API_KEY=your_sk_key_here
    ```

3.  **Install dependencies**
    This project uses `uv` for fast package management, but standard pip works too.
    
    Using uv:
    ```bash
    uv sync
    ```
    
    Using pip:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application**
    ```bash
    # Using uv
    uv run app.py
    
    # Or using python directly
    python app.py
    ```

5.  **Access the UI**
    Open your browser to `http://127.0.0.1:7860`.

## 🎓 Origin & Credits

This project was built as part of **[The Complete Agentic AI Engineering Course](https://www.udemy.com/course/the-complete-agentic-ai-engineering-course/)** by **Ed Donner**. It adapts the core concepts of building autonomous agents to the domain of clinical pharmacy.

## ⚠️ Disclaimer

**Prototype Status**: This tool is a proof-of-concept prototype.
*   **Limitation**: The hosted specific demo on Hugging Face (Free Tier) may timeout on complex queries.
*   **Clinical Use**: This tool is for educational and demonstrative purposes only. It should not replace professional clinical judgment. Always verify outputs with official monographs.

## 📄 License

MIT
