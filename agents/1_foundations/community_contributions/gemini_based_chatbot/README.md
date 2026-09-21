
# Gemini Chatbot of Users (Me)

A simple AI chatbot that represents **Rishabh Dubey** by leveraging Google Gemini API, Gradio for UI, and context from **summary.txt** and **Profile.pdf**.

## Screenshots
![image](https://github.com/user-attachments/assets/c6d417df-aa6a-482e-9289-eeb8e9e0f3d2)


## Features
- Loads background and profile data to answer questions in character.
- Uses Google Gemini for natural language responses.
- Runs in Gradio interface for easy web deployment.

## Requirements
- Python 3.10+
- API key for Google Gemini stored in `.env` file as `GOOGLE_API_KEY`.

## Installation

1. Clone this repo:

   ```bash
   https://github.com/rishabh3562/Agentic-chatbot-me.git
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Add your API key in a `.env` file:

   ```
   GOOGLE_API_KEY=<your-api-key>
   ```


## Usage

Run locally:

```bash
python app.py
```

The app will launch a Gradio interface at `http://127.0.0.1:7860`.

## Deployment

This app can be deployed on:

* **Render** or **Hugging Face Spaces**
  Make sure `.env` and static files (`summary.txt`, `Profile.pdf`) are included.

---

**Note:**

* Make sure you have `summary.txt` and `Profile.pdf` in the root directory.
* Update `requirements.txt` with `python-dotenv` if not already present.

---



