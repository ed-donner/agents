### Setup environment variables
---

```md
OPENAI_API_KEY=<your-openai-key>
PUSHOVER_USER=<your-pushover-user-key>
PUSHOVER_TOKEN=<your-pushover-token>
RATELIMIT_API="https://ratelimiter-api.ksoftdev.site/api/v1/counter/fixed-window"
REQUEST_TOKEN=<any-token>
```

### Installation
1. Clone the repo
---
```cmd
git clone httsp://github.com/ken-027/agents.git
```

2. Create and set a virtual environment
---
```cmd
python -m venv agent
agent\Scripts\activate
```

3. Install dependencies
---
```cmd
pip install -r requirements.txt
```

4. Run the app
---
```cmd
cd 1_foundations/community_contributions/openai_chatbot_k && py app.py
or
py 1_foundations/community_contributions/openai_chatbot_k/app.py
```
