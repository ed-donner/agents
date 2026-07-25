# LinkedIn Manager Agent

Create and publish a LinkedIn post based on your recent local code changes. This mini project uses the OpenAI Agents SDK to generate a post and a simple API client to publish it.

## What it does
- Scans recently modified Python files (last 24 hours) for context
- Crafts a concise LinkedIn post (max 150 words)
- Publishes the post to LinkedIn using the Upload-Post API

## Project layout
- `app.py`: runs the LinkedIn manager agent end-to-end
- `linkedin_manager_agent.py`: orchestrates crafting and posting the update
- `craft_post_agent.py`: generates the LinkedIn post from recent files
- `tools.py`: file context tool + LinkedIn post tool

## Requirements
- Python 3.10+
- `agents` SDK
- `python-dotenv`
- `requests`

If you are working from the repo root, install dependencies from the workspace `requirements.txt` files as needed.

## Setup
1. Create a `.env` file in this folder or at the repo root:
   ```
   LINKEDIN_POST_API_KEY=your_upload_post_api_key
   ```
2. (Optional) Update the LinkedIn username in `tools.py` if you want to post to a different account.

## Run
From this folder:
```
python app.py
```

This will:
1. Generate a post using your recent code changes
2. Publish the post to LinkedIn

## Notes
- The post is written in first person and kept under 150 words.
- The file context tool only reads `.py` files and limits each file to 1000 characters.
- If no content is generated, the agent skips posting.
