# chrys — Lab 2 assessment (Resend-only loop)

Everything stays **inside Resend**: outbound send, prospect inbox, inbound receiving, webhook.

[`assessment.ipynb`](assessment.ipynb) flow:

1. **`await start_cold_campaign()`** or **`POST /outbound/cold`** — Sales Manager → Email Manager → **`send_html_email`** → Resend sends **to** `SALES_PROSPECT_EMAIL` (default **`chrys@wileeilkue.resend.app`**). For an external prospect, set **`RESEND_REPLY_TO`** to your **`*.resend.app`** address so replies hit **Receiving**.
2. **✅ Threading**: Follow-up emails use `In-Reply-To` and `References` headers so replies stay in the **same email thread** in Gmail/Outlook (not new threads).
3. **Prospect replies** — must arrive at an address with **Resend Receiving** + your webhook. Resend fires **`email.received`** → **`/webhooks/resend`** → follow-up send.
3. **`POST /simulate/inbound`** — Test step 2 locally with a `thread_id` from step 1.

## Env

| Variable | Role |
|----------|------|
| **`RESEND_FROM`** | Outbound **From**. **`onboarding@resend.dev`** is test-only: Resend only delivers to **your** email. To send to another person (e.g. afam), **verify a domain** and use an address on it. |
| **`SALES_PROSPECT_EMAIL`** | Outbound **To** (the prospect). |
| **`RESEND_REPLY_TO`** | Optional **Reply-To** (e.g. `chrys@wileeilkue.resend.app`). If unset and **To** is *not* a `*.resend.app` address, the notebook sets **Reply-To** to **`RESEND_RECEIVING_ADDRESS`** (default `chrys@wileeilkue.resend.app`). |
| **`RESEND_RECEIVING_ADDRESS`** | Inbox used for the auto **Reply-To** fallback above. |
| **`RESEND_API_KEY`** | API key for send + Receiving API. |

Enable **Receiving** + **webhook** (`email.received` → `https://<ngrok>/webhooks/resend`) for your `*.resend.app` subdomain. **`ngrok http 8765`** while the app runs.

**Threading:** The `chrys_inbound_reply` flow (AI response to prospect replies) now preserves thread context. All messages should stay in the same email thread using `In-Reply-To`/`References` headers.

**Gmail:** Use **Reply** (not "Reply to author" if offered); that follows the **Reply-To** header. After sending, confirm `send_html_email` returned a non-empty `reply_to` in the tool output. If `RESEND_RECEIVING_ADDRESS=` is present but empty in `.env`, it used to disable Reply-To—fixed in the notebook via a non-empty default.

**Local `curl`:** `http://127.0.0.1:8765/...`. **Traces:** optional `OPENAI_API_KEY` for [platform.openai.com/traces](https://platform.openai.com/traces).

```bash
cd 2_openai/community_contributions/chrys
uv pip install -r requirements.txt
jupyter lab assessment.ipynb
```

Run all cells in order: the **cold-outreach** cell runs `await start_cold_campaign()` **before** the blocking `await server.serve()` cell, so Resend actually receives a send (visible under **Emails** in the dashboard). If you only run the server cell, nothing is sent until you interrupt and run the cold cell, or `curl -X POST http://127.0.0.1:8765/outbound/cold` while the app runs (e.g. from a terminal `uv run uvicorn …`). Export + `uv run uvicorn assessment:app --host 0.0.0.0 --port 8765` if you prefer the server outside Jupyter.
