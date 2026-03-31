---
title: CareerBot
app_file: app.py
sdk: gradio
sdk_version: 6.10.0
---
# Career Chatbot 🤖

An AI-powered career assistant that represents me and answers questions about my experience, skills, and background. Built using Gradio and deployed on Hugging Face Spaces.

---

## 🚀 Features

- Answers questions about my career, skills, and projects  
- Uses real data from my summary and LinkedIn profile  
- Allows users to share their email to get in touch  
- Sends push notifications when a user shares contact details  
- Deployed as a live web app  

---

## 🧠 How it works

- Uses an LLM (OpenAI) to generate responses  
- Injects personal context (summary + LinkedIn data) into prompts  
- Uses tool-calling to detect when a user provides an email  
- Sends notifications via Pushover  

---

## 🛠️ Tech Stack

- Python  
- Gradio  
- OpenAI API  
- Pushover (for notifications)  
- Hugging Face Spaces (deployment)  

---

## 📁 Project Structure
├── app.py
├── linkedin.pdf
└── README.md

## ⚙️ Setup (Local)

1. Create virtual environment
2. Install dependencies
3. Create `.env` file
4. Run: python app.py

## 🌍 Deployment

Deployed using: gradio deploy
