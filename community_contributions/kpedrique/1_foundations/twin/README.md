# Professional digital twin

The chat combines a professional profile, retrieved FAQs, tools, and a response
evaluator. Deployment is a later step.

The response-language selector defaults to English and also offers Spanish.
Each new message uses the current selection, regardless of the language typed
or used earlier in the conversation. Changing it applies to future responses;
it does not translate existing messages. Examples preserve the current selection.
Gradio history is normalized to text messages before retrieval or API calls:
UI fields such as `metadata` and `options` are excluded, and text blocks are
flattened while preserving the conversation.

## Minimal RAG

`retrieval.py` searches the answered entries in `docs/twin_faqs_es.json` and
`docs/twin_faqs_en.json`. It normalizes accents and case, removes common words,
and ranks matches by weighted word overlap. Questions receive extra weight;
rare words receive more weight than common words. Up to three FAQ IDs are
selected, including both translations. Short follow-ups also use the previous
user question, with a lower weight.

`context.py` adds those answers to the summary and extracted LinkedIn profile.
Reviewed FAQ answers take precedence when they conflict with the profile.
Only answered FAQs are retrieved: pending questions, review notes, source notes,
and recruiting references are excluded.

This is lexical RAG: retrieve relevant records, add them to the prompt, then
generate an answer. It does not require embeddings or a vector database.
Paraphrases without matching words can be missed. A retrieval miss does not
prove that the profile contains no answer; the model still has the base profile.

## Evaluation and tools

The evaluator follows the original lab3's narrow role: professional scope,
privacy, friendly tone, and the selected response language. It receives only
the latest visitor message and candidate response. It does not receive the
professional profile, FAQ context, conversation history, or tool receipts.
The generator still receives those career sources and conversation history.
The verdict uses a strict JSON schema via OpenAI
[Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

Rejected responses can be revised twice. Every revision processes tool calls
and is evaluated again. Tool loops have a limit, and identical tool calls are
cached within one visitor turn so a revision does not repeat a notification.
If generation/evaluation fails or all candidates are rejected, the chat returns
a fixed apology in the selected language and records the original question via
the existing Lupai notification tool. A successfully recorded question is not
sent again in the same turn. A failed notification is not retried automatically
and the reply explicitly says that recording failed.

The evaluator also classifies whether a question is outside the professional
scope. Personal questions such as "Tienes hijos" receive a fixed professional
redirection in the selected language, and the question is recorded. A refusal
to discuss private facts is a valid response, not a reason to keep regenerating.
Model evaluation is still fallible.

Application code checks tool names, visitor-provided contact emails, and
successful tool results. The Lupai endpoint must return HTTP success and JSON
`true` before a notification tool reports `OK`. Failures never count as success.
After `record_user_details` succeeds, code returns a localized confirmation
immediately, without another generation or evaluation call. Contact action
confirmation does not depend on an evaluator's wording preference.

The lab3 email deduplication behavior is preserved: comparison uses stripped,
lowercase addresses. Existing entries in `../emails.txt` are read without
modifying that legacy list. New contacts are saved to `data/emails.txt`, which
is excluded from Git, only after a successful notification. Already registered
addresses return a localized acknowledgment without another notification.
A process lock prevents concurrent Gradio sessions from sending the same new
contact twice. Notifications sent before this persistence was added can only
be recognized if their address is already present in one of the lists.
When multiple addresses are requested, the chat supports tool calls in one batch
or successive model turns. Confirmations distinguish new registrations,
existing addresses, and addresses that were not registered; a partial failure
never confirms that all addresses were saved.

Greetings, thanks, and farewells use the normal conversation flow with the
lightweight evaluator. There is no hardcoded list of courtesy phrases, and the
evaluator does not audit earlier actions or demand scheduling details.

## Run locally

From this directory, install `requirements.txt` in your Python environment and
run `python app.py`. Configure `OPENAI_API_KEY` and the existing Lupai notification
environment variables before using their respective services.

Resources can be loaded from individual public file URLs configured in `.env`:

| Variable | File |
| --- | --- |
| `TWIN_LINKEDIN_URL` | `linkedin.pdf` |
| `TWIN_SUMMARY_URL` | `summary.txt` |
| `TWIN_FAQS_EN_URL` | `twin_faqs_en.json` |
| `TWIN_FAQS_ES_URL` | `twin_faqs_es.json` |

See `.env.example` for empty configuration entries. A configured URL takes
precedence over the local file. With all four configured, `docs` is not needed
in the deployment. Blank URLs use the corresponding file in local `docs`, with
paths resolved relative to this application.

Use links to uploaded PDF, TXT, and JSON files with public download access.
Google Drive file-sharing links are converted to download links; folder links
are not supported. HTML access/confirmation pages, invalid PDF data, HTTP errors,
and timeouts are reported as loading failures. Remote content stays in memory;
downloads are not written to the repo. Profile and FAQ data are cached for the
process lifetime; restart after changing the URLs or file contents.

## Verify

Run `python -m unittest discover -s tests -v` from this directory. Tests use
synthetic FAQs, temporary files, and simulated HTTP/model/tool responses. They
do not require personal documents, send notifications, or call external services.
When installed, Gradio and pypdf are used for a history round-trip and parsing
a generated blank PDF, respectively. The UI is not launched by these tests.

For a later live check, ask about English proficiency, Lupai's start date,
unknown salary expectations, and a personal topic. Try both languages and a
follow-up question. Confirm that unsupported facts are not invented. Contact
and unknown-question tools still use the existing Lupai integration; its network
errors now propagate instead of being reported as successful notifications.
Use `CHANNEL_TOKEN` (or the legacy `GUPSHUP_TOKEN`), `DESTINATION`, and
`RECORD_USER_DETAIL` to configure the contact notification.
