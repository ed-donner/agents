---
title: Career Conversation AI
emoji: 💼
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 5.34.2
app_file: app.py
pinned: false
license: mit
---

# Career Conversation AI

An AI-powered chatbot that answers questions about Keerthi Bheemagani's career, background, skills, and experience. Built with Gradio and OpenAI.

## Features

- 🤖 AI-powered conversation interface
- 📄 Answers questions based on LinkedIn profile and professional summary
- 📧 Can record user contact information
- ❓ Tracks unanswered questions for improvement

## Setup Instructions

1. Set the following environment variables in your Hugging Face Space settings:
   - `OPENAI_API_KEY`: Your OpenAI API key (required)
   - `PUSHOVER_TOKEN`: Pushover API token (optional, for notifications)
   - `PUSHOVER_USER`: Pushover user key (optional, for notifications)

2. The app will automatically load the necessary data files (`me/linkedin.pdf` and `me/summary.txt`)

## Usage

Simply start chatting with the AI about career-related questions. The AI will answer based on the provided background information.
