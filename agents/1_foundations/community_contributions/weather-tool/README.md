# Weather Tool – Personal Assistant with Weather Integration

Created by [Ayaz Somani](https://www.linkedin.com/in/ayazs) as a community contribution.

## Overview

This Weather Tool community contribution gives the personal assistant chatbot the ability to discuss weather casually and contextually. It integrates real-time weather data from the Open-Meteo API, allowing the assistant to respond naturally to weather-related topics.

The assistant can reference weather in its current (simulated) location, the user’s location (if mentioned), or any other city brought up in conversation. This builds a more engaging, humanlike interaction while preserving the assistant’s focus on personal and professional topics defined in the `me` folder.

## Features

### New Capabilities
- **Real-Time Weather Updates** | Seamless integration with Open-Meteo’s API
- **Natural Weather Mentions** | Assistant introduces weather organically during conversation, not just in response to questions

### Technical Enhancements
- **Location Resolution** | Uses Open-Meteo’s geocoding API to convert place names to coordinates
- **Weather Lookup** | Fetches current temperature, conditions, and other data from Open-Meteo

## File Structure
weather-tool/
├── app.py                     # Main application
├── requirements.txt           # Python dependencies
└── me/                        # Required dependency for the app to run

## Environment Variables

The following variable is required to personalize assistant responses:
- `BOT_SELF_NAME` – Name the assistant uses to refer to itself (e.g. "Ed", "Alex", etc.)

## Getting Started

1. Install dependencies:
   ```bash
   uv add openmeteo_requests


## Getting Started

1. Install dependencies:
```bash
uv add openmeteo_requests
```

2.	Set the necessary environment variables in `.env`, including:
```text
BOT_SELF_NAME=YourAssistantName
```

3.	Add your personal files to the me/ directory:
- linkedin.pdf
- summary.txt

4. Launch the application:
```bash
uv run app.py
```

5.	Open the Gradio interface in your browser to start interacting with the assistant.

## Try These Example Prompts

To test the weather functionality in context, try saying:
- “What’s the weather like where you are today?”
- “I’m heading to London. Wonder if I need an umbrella?”
- “Is it really snowing in Calgary right now?”

