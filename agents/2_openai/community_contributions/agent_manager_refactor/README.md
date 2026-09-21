---
title: deep_research
app_file: deep_research.py
sdk: gradio
sdk_version: 5.31.0
---

# 🧠 Deep Research Agent (Modular)

This project is a modular and extended version of the deep research agent. Instead of running the entire research process in a single step, this system breaks it down into reusable **tool-like stages**, orchestrated by a central **Research Manager Agent**. This creates a more natural and interactive experience, similar to tools like ChatGPT.

---

## 🚀 What's different

- Each research stage is implemented as a standalone tool.
- Generates clarifying questions.
- A **manager agent** controls the flow and selects tools dynamically.
- Enables a **more conversational** research experience.
- Rather than hardcoding the user's email address in the script, the agent dynamically prompts the user for their address and uses SendGrid to send the report to that input

---

## 🛠️ Usage

- Just make sure you've defined the environment variables listed in the `.env.example` file.
- If you want to send emails to any address, you need to have a verified domain in SendGrid and use an email address from that domain in the SENDGRID_SENDER_EMAIL variable. Otherwise, you can use your verified single sender email address, but you may encounter issues when sending emails to recipients other than the sender address.
