---
title: WindowWolf Chatbot
app_file: 3_run_chatbot.py
sdk: gradio
sdk_version: 5.34.2
python_version: 3.11
---
# Window Wolf Chatbot

A professional AI chatbot for Window Wolf window cleaning services with RAG (Retrieval-Augmented Generation).

## 🚀 Quick Start

**READ THIS FIRST:** [0_README_START_HERE.md](0_README_START_HERE.md)

### Simple 3-Step Process

1. **Add Info (Optional):** `python 1_add_custom_info.py` - Add custom information
2. **Initialize RAG:** `python 2_initialize_rag.py` - Load documents (run once)
3. **Run Chatbot:** `python 3_run_chatbot.py` - Start the chatbot

## 📁 Project Structure

```
My_AIProjects/
├── 0_README_START_HERE.md      ← START HERE! Complete guide
├── 1_add_custom_info.py        ← Step 1: Add custom info (optional)
├── 2_initialize_rag.py         ← Step 2: Initialize RAG (required once)
├── 3_run_chatbot.py            ← Step 3: Run chatbot
│
├── source_documents/           ← Your source documents
│   ├── WindowWolfChatbot.pdf
│   └── WindowWolfSummary.txt
│
├── rag_system/                 ← RAG system code
├── WindowWolfApp.py            ← Main chatbot code
└── requirements.txt            ← Dependencies
```

## 🔧 Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Make sure `.env` file is in parent directory with API keys
3. Run: `python 2_initialize_rag.py`
4. Run: `python 3_run_chatbot.py`

## 📖 Documentation

Technical documentation is in the `docs/` folder.

---

**For detailed instructions, see:** [0_README_START_HERE.md](0_README_START_HERE.md)
