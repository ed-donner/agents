### Setup environment variables
---

```md
OPENAI_API_KEY=<your-openai-key>
EJS_PUBLIC_KEY=<your-ejs-public-key>
EJS_SERVICE_ID=<your-ejs-service-id>
EJS_TEMPLATE_ID=<your-ejs-template-id>
EJS_ACCESS_TOKEN=<your-ejs-access-token>
EJS_SELF_EMAIL=<your-ejs-self-email>
RATELIMIT_API="https://ratelimiter-api.ksoftdev.site/api/v1/counter/fixed-window/deep-research"
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
cd 2_openai/community_contributions/deep_research_with_emailjs && py .
or
py 2_openai/community_contributions/deep_research_with_emailjs/.
```

## live demo
[AI Deep Research](https://huggingface.co/spaces/kenneth-andales/deep_research)
