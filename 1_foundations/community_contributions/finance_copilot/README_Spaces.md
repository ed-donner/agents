# 🚀 Finance Copilot - Hugging Face Spaces Deployment

## 📋 **Spaces Configuration**

This repository is configured to deploy on Hugging Face Spaces using Docker.

### **Required Files:**
- `README.md` - Contains the Spaces metadata
- `Dockerfile` - Defines the container environment
- `.dockerignore` - Optimizes build context
- `app.py` - Main application file
- `requirements.txt` - Python dependencies

### **Spaces Metadata (in README.md):**
```yaml
---
title: Finance Copilot - AI-Powered Financial Analysis
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
app_file: app.py
pinned: false
---
```

## 🐳 **Docker Configuration**

### **Base Image:**
- Uses Python 3.10 (same as Hugging Face Spaces)
- Optimized for financial applications

### **Port Configuration:**
- Exposes port 7860 (Gradio default)
- Configured for Hugging Face Spaces networking

### **Environment Variables:**
- `PYTHONPATH=/app`
- `GRADIO_SERVER_PORT=7860`
- `GRADIO_SERVER_HOST=0.0.0.0`

## 🚀 **Deployment Steps**

1. **Push to Hugging Face Repository:**
   ```bash
   git add .
   git commit -m "Configure for Hugging Face Spaces deployment"
   git push origin main
   ```

2. **Create Space:**
   - Go to [Hugging Face Spaces](https://huggingface.co/spaces)
   - Click "Create new Space"
   - Choose your repository
   - Select "Docker" as SDK
   - Click "Create Space"

3. **Environment Variables:**
   - Add your API keys in the Space settings:
     - `OPENAI_API_KEY`
     - `ALPHA_VANTAGE_API_KEY`
     - `PUSHOVER_USER_KEY`
     - `PUSHOVER_APP_TOKEN`

## ✅ **Features Available**

- 🤖 **AI Assistant** - Full conversation interface
- 📊 **Portfolio Management** - Track investments
- 📈 **Market Data** - Real-time stock/crypto prices
- 🔍 **Financial Analysis** - Technical indicators
- 🔔 **Alerts** - Price notifications
- ⚙️ **Settings** - User preferences

## 🔑 **Default Login**

- **Username:** admin
- **Password:** finance123

## 🐛 **Troubleshooting**

### **Common Issues:**
1. **Build Failures:** Check Dockerfile syntax
2. **Port Conflicts:** Ensure port 7860 is exposed
3. **Missing Dependencies:** Verify requirements.txt

### **Logs:**
- Check build logs in Spaces
- Monitor container logs
- Verify environment variables

## 📚 **Local Testing**

Before deploying, test locally with Docker:
```bash
docker build -t finance-copilot .
docker run -p 7860:7860 --env-file .env finance-copilot
```

## 🌐 **Access**

Once deployed, your app will be available at:
`https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME`


