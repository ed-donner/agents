# Digital Twin Setup

## What You Need

### 1. Your Files (in `me/` folder)
- **CV/Resume**: PDF file (like `dalin-cv.pdf`)
- **Summary**: Text file (`summary.txt`) with a short bio about yourself

### 2. Main Files
- **app.py**: Gradio chatbot app
- **requirements.txt**: Python dependencies
- **README.md**: Hugging Face Space config

## Upload to Hugging Face

### Quick Steps
1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Choose:
   - Name: whatever you want
   - SDK: Gradio
   - Make it public or private
4. Upload these files:
   - README.md
   - app.py
   - requirements.txt
   - me/ folder with your CV and summary
5. Add secrets in Settings → Repository secrets:
   - `OPENAI_API_KEY`: Your OpenAI key
   - `PUSHOVER_TOKEN`: From pushover.net (for notifications)
   - `PUSHOVER_USER`: Your Pushover user key

## Getting Notified

Use Pushover (free mobile notifications):
1. Sign up at https://pushover.net
2. Install the app on your phone
3. Create an application to get your token
4. Add both token and user key to Hugging Face secrets

When someone wants more info or asks questions your bot can't answer, you'll get a push notification on your phone.

## Files Structure
```
dc_dalin/
├── README.md              # Hugging Face config
├── app.py                 # Your chatbot
├── requirements.txt       # Dependencies
└── me/
    ├── dalin-cv.pdf      # Your CV
    └── summary.txt        # Your bio
```

## See Examples
Check these folders for reference:
- `digital_twin_joshua/`
- `1_foundations_using_gemini/`
- `DanielMaru/`
