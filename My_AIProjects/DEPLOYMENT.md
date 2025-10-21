# WindowWolf Chatbot - Deployment Guide

## 🚀 Quick Deployment to Hugging Face Spaces

### Prerequisites
1. Your `.env` file with API keys
2. All files in `My_AIProjects/` folder

### Step 1: Create a New Space

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Choose:
   - Space name: `windowwolf-chatbot`
   - License: `mit`
   - Space SDK: `Gradio`
   - Space hardware: `CPU basic` (free tier)

### Step 2: Upload Files

Upload these files to your Space:
```
✅ 3_run_chatbot.py
✅ WindowWolfApp.py
✅ requirements.txt
✅ README.md
✅ source_documents/WindowWolfChatbot.pdf
✅ source_documents/WindowWolfSummary.txt
✅ rag_system/ (entire folder)
```

**DO NOT upload:**
- ❌ `.env` file (add as Secrets instead)
- ❌ Any `.db` or `.sqlite3` files
- ❌ Any `__pycache__` folders
- ❌ Any UUID folders (like `c2891577-277a-4c07-b6d1-70c47bdde102/`)

### Step 3: Add Environment Variables

In your Space settings, add these Secrets:
```
OPENAI_API_KEY = your_openai_key_here
GEMINI_API_KEY = your_gemini_key_here
PUSHOVER_TOKEN = your_pushover_token_here (optional)
PUSHOVER_USER = your_pushover_user_here (optional)
```

### Step 4: Deploy

1. The Space will automatically build (this takes 3-5 minutes)
2. Wait for:
   - ✅ Dependencies to install
   - ✅ Sentence transformers model to download (~80MB)
   - ✅ RAG system to auto-initialize
3. Your chatbot will be live!

---

## ⏱️ Why Deployment Takes Time

The first build is slow because:
1. **Installing dependencies** (30-60 seconds)
2. **Downloading sentence-transformers model** (90-120 seconds) - This is a one-time download
3. **Auto-initializing RAG** (30-60 seconds) - Loads your documents

**Total first build time: 3-5 minutes**

Subsequent builds are much faster!

---

## 🐛 Troubleshooting

### "Build failed" or stuck at "Building..."
- **Solution:** Check that all required files are uploaded
- Make sure `source_documents/` folder contains your PDF and summary

### "Application startup failed"
- **Solution:** Check that environment variables (Secrets) are set correctly
- Verify your API keys are valid

### "Module not found" errors
- **Solution:** Make sure `requirements.txt` was uploaded correctly
- Check that `rag_system/` folder with all `.py` files was uploaded

### Chatbot starts but RAG not working
- **Solution:** The auto-initialization will run on first startup
- Check the logs for "First-time setup: Initializing RAG system..."
- If it fails, manually upload a pre-initialized database

---

## 📊 Monitoring Your Deployment

### Check Logs
In your Space, click on "Logs" to see:
- Initialization progress
- Any errors or warnings
- User interactions (if logging is enabled)

### Performance
- **Cold start:** 3-5 minutes (first time)
- **Warm start:** 10-30 seconds (subsequent times)
- **Response time:** 2-5 seconds per query

---

## 🔄 Updating Your Deployed App

### To update documents:
1. Edit `source_documents/WindowWolfChatbot.pdf` or `WindowWolfSummary.txt`
2. Upload the updated files to your Space
3. Restart the Space (it will auto-reinitialize)

### To update code:
1. Edit your Python files locally
2. Upload the updated files to your Space
3. The Space will automatically rebuild

---

## 💡 Pro Tips

1. **Use Space Secrets** for all API keys - never commit them to your code
2. **Monitor your API usage** - each conversation uses OpenAI/Gemini API
3. **Enable analytics** in Space settings to track usage
4. **Upgrade hardware** if you need faster response times (costs money)

---

## 🎉 Your App is Live!

Once deployed, share your Space URL:
```
https://huggingface.co/spaces/YOUR_USERNAME/windowwolf-chatbot
```

Need help? Check the logs or see the main README for local testing first.

