# Professional digital twin

A Gradio assistant for my professional profile, with English/Spanish responses,
lexical FAQ retrieval, a lightweight evaluator, and Lupai/Gupshup notifications.

## Run

Use the course environment. From this folder, run `uv run app.py`.
Deployment is pending; the application has been tested locally.

Configure the following in your local `.env` (never commit its values):

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Chat and evaluator API access |
| `CHANNEL_TOKEN` | Lupai notification token (`GUPSHUP_TOKEN` also supported) |
| `DESTINATION` | WhatsApp notification recipient |
| `RECORD_USER_DETAIL` | Contact notification template ID |
| `RECORD_UNKNOWN_QUESTION` | Unanswered-question notification template ID |
| `TWIN_LINKEDIN_URL` | Public PDF file URL |
| `TWIN_SUMMARY_URL` | Public UTF-8 summary file URL |
| `TWIN_FAQS_EN_URL` | Public English FAQ JSON URL |
| `TWIN_FAQS_ES_URL` | Public Spanish FAQ JSON URL |

Individual Google Drive file links are supported; folder links are not.
Without a URL, the corresponding file is loaded from local `docs/`:
`linkedin.pdf`, `summary.txt`, `twin_faqs_en.json`, or `twin_faqs_es.json`.
FAQ JSON uses `{"language": "en", "faqs": [{"id": "profile",
"question": "What is your background?", "answer": "Your verified answer",
"tags": ["profile"]}]}` (use `es` for Spanish). Blank answers are excluded.
Restart after updating documents because resources are cached in memory.

The evaluator checks professional scope, privacy, tone, and selected language.
Application code validates tool results and confirms contact registration.
New contacts are deduplicated in local `data/emails.txt`; an existing
`../emails.txt` is also consulted. The local `.gitignore` excludes runtime data.
Contact emails and source documents should remain outside the contribution.
