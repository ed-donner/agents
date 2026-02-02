# HuggingFace Space Deployment Guide
# AI Career Assistant v2.0 - Intellecta Solutions

## 🚀 Deployment Steps

### 1. Create New Private Space

```bash
# Visit: https://huggingface.co/new-space
# Settings:
- Owner: Xeroxat
- Space name: career-assistant-v2
- License: other (proprietary)
- SDK: Gradio
- SDK version: 4.44.1
- Visibility: PRIVATE ⚠️
```

### 2. Upload Files

Upload these files to your Space:
```
├── app_new.py                 # Main application
├── requirements_hf.txt         # Dependencies (rename to requirements.txt)
├── README_HF.md               # Documentation (rename to README.md)
├── .env                       # ⚠️ DON'T UPLOAD - Use Secrets instead
├── me/
│   ├── Profile.pdf
│   ├── summary.txt
│   └── knowledge/
│       ├── company/
│       ├── llmops/
│       ├── agentic_projects/
│       └── github_projects/
└── career_bot.db              # SQLite database
```

### 3. Configure Secrets (IMPORTANT!)

In HuggingFace Space Settings → Repository Secrets:

```bash
OPENAI_API_KEY=sk-...your-key...
PUSHOVER_USER=u...your-user...
PUSHOVER_TOKEN=a...your-token...
```

### 4. Modify app_new.py for HuggingFace

**Replace** the .env loading section with:

```python
# HuggingFace Spaces: Use secrets from environment
import os

# These will be loaded from HF Secrets
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")

# Initialize OpenAI
from openai import OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)
```

### 5. Database Persistence

**⚠️ Important**: HuggingFace Spaces are ephemeral!

Option A: Use Persistent Storage (Recommended)
```bash
# Enable persistent storage in Space settings
# Database will be saved to /data/career_bot.db
```

Option B: Use External Database
```bash
# Connect to PostgreSQL/MySQL
# Or use Firebase/Supabase
```

### 6. Test Deployment

```bash
# Check logs in HuggingFace Space
# Look for:
✅ Loaded intellecta_website.md into KB (company)
✅ Loaded intellecta_cli.md into KB (llmops)
...
* Running on local URL:  http://0.0.0.0:7860
```

### 7. Access Control

Your Space URL will be:
```
https://huggingface.co/spaces/Xeroxat/career-assistant-v2
```

Since it's PRIVATE:
- ✅ Only you can access
- ✅ No public visibility
- ✅ Can share with specific HF users
- ✅ Secure deployment

## 🔐 Security Checklist

- [ ] Space set to PRIVATE
- [ ] .env file NOT uploaded (use Secrets)
- [ ] OPENAI_API_KEY in Secrets
- [ ] PUSHOVER credentials in Secrets
- [ ] Database persistence enabled
- [ ] README.md has copyright notice
- [ ] License set to "other" (proprietary)

## 📊 Monitoring

Monitor your Space:
```
Settings → Logs → View logs
Settings → Usage → Check metrics
Settings → Secrets → Verify keys
```

## 🔄 Updates

To update your Space:
```bash
# Git push to HF repository
git clone https://huggingface.co/spaces/Xeroxat/career-assistant-v2
cd career-assistant-v2
# Make changes
git add .
git commit -m "Update: ..."
git push
```

## 🆘 Troubleshooting

**App won't start:**
- Check logs for errors
- Verify all secrets are set
- Ensure requirements.txt is correct

**Database not persisting:**
- Enable persistent storage
- Check /data directory permissions

**Rate limit errors:**
- Adjust SecurityManager settings
- Check OpenAI API limits

## 📧 Support

For deployment issues: contact@intellectasolutions.com

---

**© 2024-2025 Intellecta Solutions - Patent Pending**
