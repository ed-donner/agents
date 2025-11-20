---
title: RapidResume
app_file: main.py
sdk: gradio
sdk_version: 5.34.2
---
# 🚀 RapidResume
**Tagline:** Make your CV in 60 seconds — answer 6 questions and your CV is ready!

RapidResume is an AI-powered CV builder built with the **OpenAI Agent SDK** and **MCP servers**.  
It collects your details, generates a polished Markdown CV, extends it with professional detail, converts it to styled HTML, and finally exports it as a beautiful PDF.

---

## ✨ Features
1. **Answer 6 Questions** → Provide your Name, Email, Phone, Education, Experience, and Skills.  
2. **Markdown CV** → Saved as `cv.md`.  
3. **Auto Enhancement** → AI extends your experience and adds inferred skills.  
4. **Styled HTML** → CV is formatted as a professional HTML template (`cv.html`).  
5. **Polished PDF** → Exported with styling into `cv.pdf`.  

---

## ⚙️ Requirements

### 📦 Python Packages
Install with `uv` (or `pip`):

```bash
uv pip install -r requirements.txt
```

### 🗝️ OpenAI API Key
This project requires an OpenAI API key.  
Create a `.env` file in the root directory and add your key:

```env
OPENAI_API_KEY=your_openai_api_key_here
MODEL_NAME=gpt-4.1-mini   # You can change this to another model
```

### 📑 MCP Servers
The project uses MCP servers for filesystem access.  
Make sure you have **Node.js** and `npx` installed, then run:

```bash
npx -y @modelcontextprotocol/server-filesystem .
```

This allows the agents to read/write `cv.md` and `cv.html` locally.

### 🖨️ PDF Conversion Dependency
`pdfkit` is used for HTML → PDF conversion.  
It requires `wkhtmltopdf` installed on your system.

On Ubuntu/Debian:
```bash
sudo apt-get install -y wkhtmltopdf
```

On Windows/Mac: download from [wkhtmltopdf.org/downloads](https://wkhtmltopdf.org/downloads.html).

---

## ▶️ Usage

Run the main script:

```bash
python main.py
```

You’ll be asked 6 questions:  
- Name  
- Email  
- Phone  
- Education  
- Experience  
- Skills  

After completion, the following files will be created in your project folder:  
- `cv.md` → raw Markdown CV  
- `cv.html` → styled HTML CV  
- `cv.pdf` → professional PDF CV  

---

## 📂 Project Files

- `main.py` → Entry point, runs the workflow sequentially.  
- `agents.py` → Contains agent definitions and helper functions.  
- `requirements.txt` → Python dependencies.  
- `README.md` → Setup and usage guide.  
- `.env.example` → Example environment variables file.  

---

## 📖 Example

```bash
$ python main.py
Full Name: John Doe
Email: john@example.com
Phone: +123456789
Education: BS Computer Science, XYZ University
Experience: 3 years as Data Analyst
Skills: Python, SQL, Power BI

✅ CV successfully generated: cv.pdf
```

---

## 💡 Notes
- You can customize the `MODEL_NAME` in `.env` to switch between models (`gpt-4.1-mini`, `gpt-4`, etc.).  
- Ensure MCP servers are installed and accessible via `npx`.  
- This project is modular — you can extend it with more agents (e.g., LinkedIn optimizer, Cover Letter generator).

---

## 🏆 Why RapidResume?
- ⏱️ Get a professional CV in under 60 seconds.  
- 🤖 Powered by AI Agents + MCP servers.  
- 📄 Export polished Markdown → HTML → PDF seamlessly.  
