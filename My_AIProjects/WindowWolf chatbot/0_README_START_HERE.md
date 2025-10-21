# WindowWolf Chatbot - Quick Start Guide

**Simple 3-Step Process: Just run the numbered files in order!**

---

## 🚀 Quick Start (First Time Setup)

### Step 1: Add Your Information (Optional)
```bash
python 1_add_custom_info.py
```
- Add custom information like your height, experience, pricing, service areas, etc.
- This is **OPTIONAL** - skip if you don't need to add anything new
- You can run this anytime to add more information

### Step 2: Initialize the RAG System (Required Once)
```bash
python 2_initialize_rag.py
```
- Loads your documents into the vector database
- **Run this ONCE** when you first set up
- Also run it if you update your PDF or summary files

### Step 3: Run Your Chatbot
```bash
python 3_run_chatbot.py
```
- Starts the chatbot with Gradio interface
- Opens in your web browser automatically
- Uses RAG to answer questions intelligently

---

## 📁 Project Structure

```
My_AIProjects/
├── 0_README_START_HERE.md          ← You are here!
├── 1_add_custom_info.py            ← Step 1: Add info (optional)
├── 2_initialize_rag.py             ← Step 2: Load documents (required once)
├── 3_run_chatbot.py                ← Step 3: Start chatbot (main app)
│
├── source_documents/                ← Your source documents
│   ├── WindowWolfChatbot.pdf       ← Main business info
│   └── WindowWolfSummary.txt       ← Business summary
│
├── rag_system/                      ← RAG system code (don't modify)
│   ├── rag_manager.py
│   ├── rag_system.py
│   └── __init__.py
│
├── WindowWolfApp.py                 ← Main chatbot code
└── requirements.txt                 ← Python dependencies
```

---

## 🔄 Common Workflows

### First Time Setup
1. Make sure `.env` file is in parent directory with your API keys
2. Run: `python 2_initialize_rag.py`
3. Run: `python 3_run_chatbot.py`

### Adding New Information
1. Run: `python 1_add_custom_info.py`
2. No need to restart chatbot - changes take effect immediately

### Updating Source Documents
1. Edit `source_documents/WindowWolfChatbot.pdf` or `WindowWolfSummary.txt`
2. Run: `python 2_initialize_rag.py` (with force reload)
3. Run: `python 3_run_chatbot.py`

### Just Running the Chatbot
```bash
python 3_run_chatbot.py
```
That's it! Everything is already loaded.

---

## ✅ Requirements

Make sure you have:
- Python 3.8+
- Dependencies installed: `pip install -r requirements.txt`
- `.env` file in parent directory with:
  - `OPENAI_API_KEY=your_key`
  - `GEMINI_API_KEY=your_key`
  - `PUSHOVER_TOKEN=your_token` (optional)
  - `PUSHOVER_USER=your_user` (optional)

---

## 🆘 Troubleshooting

**RAG not working?**
- Run `python 2_initialize_rag.py` to reload documents

**Chatbot not starting?**
- Check that `.env` file exists in parent directory
- Verify API keys are set correctly

**Want to add new information?**
- Run `python 1_add_custom_info.py` anytime

---

## 📝 Notes

- **Your RAG data persists** - It's saved to disk in the `rag_system/` folder
- **Restart safe** - You won't lose data when you restart your computer
- **Clean and simple** - Just follow the numbered files!

---

**Ready to start?** Run `python 2_initialize_rag.py` if this is your first time, then `python 3_run_chatbot.py`!

