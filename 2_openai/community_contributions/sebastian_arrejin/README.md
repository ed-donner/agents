# Mail merge campaign with the OpenAI Agents SDK

My solution to the Week 2 Lab 2 exercise: I extended the Sales Manager so it sends a personalized email
to every contact in a list, instead of a single email.

## What I added

- **New tools** (`@function_tool`): `get_contacts` reads the contact list from a CSV, `preview_merge` shows the email
  for the first contact before sending, and `mail_merge_and_send` fills in `{name}`, `{company}` and `{role}` for each contact and sends it.
- **New agents as tools**: `template_writer` turns the best draft into a mail-merge template, and `html_converter` creates the HTML version.
- **Campaign Manager**: a planning agent that gets drafts from the 3 sales writers, picks the best one,
  builds the template, checks the preview and sends the campaign.
- **Safety**: the contacts are fictional and their addresses are generated as aliases of my own `EMAIL_ADDRESS`
  (for example `me+ana@gmail.com`), so no real person receives an email. Sending is capped with `MAX_RECIPIENTS`.

## How to run

Open `2_lab2_mail_merge.ipynb`, select the course's `.venv` kernel and run all cells.
It uses `EMAIL_ADDRESS`, `EMAIL_SMTP_SERVER` and `EMAIL_APP_PASSWORD` from `.env`, and falls back to Pushover if email isn't configured.
