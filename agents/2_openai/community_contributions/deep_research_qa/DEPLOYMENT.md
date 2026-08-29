# 🚀 Deployment Guide for Hugging Face Spaces

## Quick Deploy to Hugging Face Spaces

### Option 1: Direct Upload
1. **Create a new Space** on [Hugging Face Spaces](https://huggingface.co/spaces)
2. **Choose "Gradio" as the SDK**
3. **Upload these files** from the `deep_research` folder:
   - `app.py`
   - `deep_research.py`
   - `requirements.txt`
   - `README.md`
   - `metadata.json`
   - All the agent files (`*_agent.py`, `research_manager.py`)

### Option 2: Git Repository
1. **Create a new repository** or fork this one
2. **Copy the `deep_research` folder contents** to the root of your repository
3. **Create a new Space** and connect it to your repository

## Environment Configuration

In your Hugging Face Space settings, add these secrets:

### Required
- `OPENAI_API_KEY`: Your OpenAI API key

### Optional (for email functionality)
- `SENDGRID_API_KEY`: Your SendGrid API key
- `SENDGRID_FROM_EMAIL`: Your verified sender email

## Files Structure for Deployment

```
your-space/
├── app.py                 # Main entry point for HF Spaces
├── deep_research.py       # Core application logic
├── requirements.txt       # Python dependencies
├── README.md             # Space documentation
├── metadata.json         # HF Spaces configuration
├── research_manager.py   # Research orchestration
├── clarifier_agent.py    # Clarification agent
├── planner_agent.py      # Planning agent
├── search_agent.py       # Search agent
├── writer_agent.py       # Writing agent
├── evaluator_agent.py    # Quality evaluation agent
├── email_agent.py        # Email delivery agent
├── .gitignore           # Git ignore rules
└── env_example.txt      # Environment variables template
```

## Testing Your Deployment

1. **Local Testing**: Run `python app.py` to test locally
2. **Check Dependencies**: Ensure all imports work correctly
3. **Environment Variables**: Test with your actual API keys
4. **Gradio Interface**: Verify the UI loads and functions work

## Common Issues & Solutions

### Import Errors
- Make sure all agent files are in the same directory
- Verify `openai-agents` package is installed correctly

### API Key Issues
- Check that environment variables are set correctly in HF Spaces
- Ensure OpenAI API key has sufficient credits

### Email Functionality
- Email features are optional and will be disabled if SendGrid isn't configured
- Verify your SendGrid sender email is verified

## Performance Tips

- The app uses OpenAI's Agents framework which can take 1-2 minutes for complex research
- Consider upgrading to a paid HF Spaces plan for better performance
- Monitor usage to avoid API rate limits

## Support

If you encounter issues:
1. Check the Space logs in Hugging Face
2. Verify all environment variables are set
3. Test locally first to isolate the issue
4. Check OpenAI API status and quotas 