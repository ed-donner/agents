# Deploying to Hugging Face Spaces

This guide will help you deploy the Career Conversation AI app to Hugging Face Spaces.

## Prerequisites

1. A Hugging Face account (sign up at https://huggingface.co)
2. An OpenAI API key
3. (Optional) Pushover credentials for notifications

## Step-by-Step Deployment

### 1. Create a New Space

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Configure your space:
   - **Space name**: Choose a name (e.g., `career-conversation-ai`)
   - **SDK**: Select **Gradio**
   - **Hardware**: Choose **CPU Basic** (free tier) or upgrade if needed
   - **Visibility**: Choose Public or Private
4. Click "Create Space"

### 2. Upload Your Files

You can upload files in one of two ways:

#### Option A: Using Git (Recommended)

1. In your local terminal, navigate to the `1_foundations` directory:
   ```bash
   cd 1_foundations
   ```

2. Initialize git (if not already initialized):
   ```bash
   git init
   ```

3. Add the Hugging Face Space as a remote:
   ```bash
   git remote add origin https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
   ```
   Replace `YOUR_USERNAME` and `YOUR_SPACE_NAME` with your actual values.

4. Add, commit, and push your files:
   ```bash
   git add app.py requirements.txt README.md me/
   git commit -m "Initial commit"
   git push origin main
   ```

#### Option B: Using the Web Interface

1. Go to your Space page on Hugging Face
2. Click on "Files and versions" tab
3. Click "Add file" → "Upload files"
4. Upload these files:
   - `app.py`
   - `requirements.txt`
   - `README.md`
   - `me/linkedin.pdf`
   - `me/summary.txt`

### 3. Set Environment Variables

1. Go to your Space settings (click the gear icon)
2. Navigate to "Variables and secrets"
3. Add the following environment variables:

   **Required:**
   - `OPENAI_API_KEY`: Your OpenAI API key

   **Optional:**
   - `PUSHOVER_TOKEN`: Pushover API token (if you want notifications)
   - `PUSHOVER_USER`: Pushover user key (if you want notifications)

4. Click "Save" after adding each variable

### 4. Wait for Build

Hugging Face will automatically:
- Install dependencies from `requirements.txt`
- Build and launch your Gradio app
- Make it available at `https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME`

The build process usually takes 2-5 minutes. You can monitor progress in the "Logs" tab.

### 5. Test Your Deployment

Once the build completes:
1. Visit your Space URL
2. Test the chat interface
3. Verify that it's working correctly

## File Structure

Your Space should have this structure:
```
├── app.py              # Main Gradio application
├── requirements.txt    # Python dependencies
├── README.md          # Space description and metadata
└── me/
    ├── linkedin.pdf   # LinkedIn profile PDF
    └── summary.txt    # Professional summary
```

## Troubleshooting

### Build Fails

- Check the "Logs" tab for error messages
- Verify all dependencies in `requirements.txt` are correct
- Ensure `app.py` has no syntax errors

### App Runs But Has Errors

- Check the "Logs" tab for runtime errors
- Verify environment variables are set correctly
- Make sure the `me/` directory files are uploaded

### API Key Issues

- Ensure `OPENAI_API_KEY` is set in Space settings
- Verify the API key is valid and has credits
- Check the logs for authentication errors

## Updating Your Space

To update your Space after making changes:

```bash
git add .
git commit -m "Update app"
git push origin main
```

Or upload new files through the web interface.

## Need Help?

- Hugging Face Spaces docs: https://huggingface.co/docs/hub/spaces
- Gradio docs: https://www.gradio.app/docs/


