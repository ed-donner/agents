# Triage form submissions with Chat SDK

**Author:** Ben Sabic

---

Build a Slack bot that triages form submissions where your team already works. When someone submits a form on your website, the bot posts an interactive card to a Slack channel. A reviewer clicks a button to forward the submission via email, edit it before forwarding, or mark it as spam. The whole workflow happens inside Slack, with no separate dashboard or inbox to monitor.

The bot is built with [Chat SDK](https://chat-sdk.dev/), the unified TypeScript SDK for building chatbots that work across Slack, Microsoft Teams, Discord, and other platforms from a single codebase. You write your logic once, and Chat SDK handles the platform-specific details, such as Block Kit on Slack or Adaptive Cards on Teams.

Deploy the template now, or read on for a deeper look at how it all works.

## Quick start with an AI coding agent

If you're working with an AI coding agent like Claude Code or Cursor, you can clone the template and hand off implementation with this prompt:

`I want to build a form triage Slack bot using Chat SDK. Clone the template repo at https://github.com/vercel-labs/chat-sdk-form-bot, install dependencies with pnpm, and walk me through setting up the environment variables in .env.local. I need a Slack app, Redis (Upstash), and Resend configured. After setup, help me deploy it to Vercel and test it with a curl POST to the /api/form endpoint. When searching for information, check for applicable skill(s) first and review local documentation.`

### Vercel Plugin

Turn your agent into a Vercel expert with this [plugin](https://vercel.com/docs/agent-resources/vercel-plugin); the [Chat SDK skill](https://skills.sh/vercel/chat/chat-sdk) is included. This plugin is optional; it’s not required to use Chat SDK or for this guide.

`npx plugins add vercel/vercel-plugin`

## Setup and deployment

### What you need before deploying

You'll need accounts with three services:

*   **Slack** for the bot itself. Create a new app at [api.slack.com/apps](https://api.slack.com/apps).
    
*   **Redis** for temporary submission storage. Any Redis provider works. [Upstash](https://vercel.com/marketplace/upstash) supports serverless deployments and has a free tier.
    
*   **Resend** to send forwarded submissions via email. Sign up at [resend.com](https://resend.com/) and verify a sending domain.
    

### Configure your Slack app

1.  Create a new Slack app from a manifest at [api.slack.com/apps](https://api.slack.com/apps). Use the [slack-manifest.json](https://github.com/vercel-labs/chat-sdk-form-bot/blob/main/slack-manifest.json) file included in the template repo. Replace the two `https://example.com` URLs with your production domain (e.g. `https://your-app.vercel.app/api/webhooks/slack`).
    
2.  Install the app in your workspace and copy the **Bot User OAuth Token**.
    
3.  Copy the **Signing Secret** from the **Basic Information** page.
    

### Environment variables

The template needs these environment variables:

`# Slack SLACK_BOT_TOKEN=xoxb-... SLACK_SIGNING_SECRET=... SLACK_CHANNEL_ID=C... # Redis REDIS_URL=redis://... # Resend RESEND_API_KEY=re_... RESEND_FROM_ADDRESS=bot@yourdomain.com RESEND_FROM_NAME=Formbot # Optional, defaults to "Formbot" # Forwarding FORWARD_EMAIL=team@yourdomain.com # Where approved submissions are sent FORWARD_ENDPOINT= # Optional: webhook URL for downstream systems`

`SLACK_CHANNEL_ID` is the channel where submission cards will appear. You can find it by right-clicking a channel in Slack and selecting "View channel details" (the ID is at the bottom of the modal).

`FORWARD_ENDPOINT` is optional. If set, the bot will also POST the form data as JSON to that URL when a submission is forwarded. This is useful for piping approved submissions into a CRM, database, or another service.

### Deploy to Vercel

[Deploy the bot with one click](https://vercel.com/new/clone?repository-url=https://github.com/vercel-labs/chat-sdk-form-bot&env=SLACK_BOT_TOKEN,SLACK_SIGNING_SECRET,SLACK_CHANNEL_ID,REDIS_URL,RESEND_API_KEY,RESEND_FROM_ADDRESS,FORWARD_EMAIL), or clone the repo and deploy manually:

`git clone https://github.com/vercel-labs/chat-sdk-form-bot.git cd chat-sdk-form-bot pnpm install vercel`

After deploying, update your Slack app's interactivity request URL to point to your production domain: `https://<your-vercel-domain>/api/webhooks/slack`.

### Test the form endpoint

Send a test submission:

`curl -X POST https://<your-domain>/api/form \ -H "Content-Type: application/json" \ -d '{"Name": "Jane Doe", "Email": "jane@example.com", "Message": "Hello!"}'`

A card should appear in your configured Slack channel within a few seconds, and you should see a JSON response in your terminal:

`{"status":"received","submissionId":"a1b2c3d4-..."}`

### Local development

For local development, the template includes a Node.js server entrypoint:

`pnpm dev`

This starts a local server at `http://localhost:3000`. To receive Slack webhooks locally, use [ngrok](https://ngrok.com/) to create a public tunnel:

`ngrok http 3000`

Then update your Slack app's request URL to the ngrok URL (e.g. `https://abc123.ngrok-free.dev/api/webhooks/slack`).

## How the form triage bot works

The bot has three moving parts, including an HTTP endpoint that receives form data, a Redis store that temporarily holds submissions, and a Chat SDK bot that manages Slack interactions.

1.  An external service (your website, a form provider, a webhook) sends a `POST` request to `/api/form` with JSON data
    
2.  The bot generates a unique ID, stores the submission in Redis with a 7-day TTL, and posts an interactive card to a Slack channel
    
3.  A reviewer sees the card and takes one of three actions:
    
    *   **Forward Submission** sends a styled HTML email via [Resend](https://vercel.com/marketplace/resend) to a configured recipient, then updates the card to show who forwarded it
        
    *   **Edit & Forward** opens a modal where the reviewer can modify fields before forwarding
        
    *   **Mark as Spam** updates the card and deletes the submission from Redis
        

Once an action is taken, the card updates in place. The reviewer sees the result immediately in the same channel, without a confirmation page or context switch.

## Code walkthrough

The entire bot is about 200 lines across six files.

### Receiving submissions

The HTTP layer uses [Hono](https://vercel.com/docs/frameworks/backend/hono), a lightweight web framework. The form endpoint accepts any JSON body, assigns it a UUID, and hands it off to the bot:

``import { Hono } from "hono"; import { cors } from "hono/cors"; import { bot, postFormCard } from "./bot.js"; const app = new Hono(); app.use("/api/form", cors()); app.post("/api/form", (c) => c.req.json().then(async (formData: Record<string, unknown>) => { const submissionId = crypto.randomUUID(); await Promise.resolve(postFormCard(formData, submissionId)); return c.json({ status: "received", submissionId }); }) ); app.post("/api/webhooks/:platform", (c) => { const platform = c.req.param("platform"); if (platform !== "slack") { return c.json({ error: `Unknown platform: ${platform}` }, 404); } return bot.webhooks.slack(c.req.raw); }); export default app;``

You can submit directly from a browser-based form on any origin. The webhook route at `/api/webhooks/:platform` handles Slack's interaction payloads (button clicks and modal submissions). The `:platform` parameter is already set up for adding other platforms later.

### Building the bot

The bot itself is a Chat SDK instance with a Slack adapter and Redis-backed state:

`import { Chat } from "chat"; import { createSlackAdapter } from "@chat-adapter/slack"; import { createRedisState } from "@chat-adapter/state-redis"; export const bot = new Chat({ adapters: { slack: createSlackAdapter(), }, state: createRedisState(), userName: "form-bot", });`

That's the entire bot setup. Chat SDK handles Slack's signature verification, payload parsing, and response formatting. The `state` object is a Redis adapter that Chat SDK uses for its internal state management, and the same Redis connection is reused to store form submissions.

### Interactive cards

Cards are built using Chat SDK's component functions. These are platform-agnostic: on Slack, they render as Block Kit, on Teams, they'd render as Adaptive Cards. Here's the card that appears when a new submission arrives:

`import { Actions, Button, Card, Fields, Field, Divider } from "chat"; export const newSubmissionCard = ( formData: Record<string, unknown>, submissionId: string ) => Card({ children: [ Fields( Object.entries(formData).map(([key, value]) => Field({ label: key, value: String(value) }) ) ), Divider(), Actions([ Button({ id: "forward", label: "Forward Submission", style: "primary", value: submissionId, }), Button({ id: "edit", label: "Edit & Forward", style: "primary", value: submissionId, }), ]), Actions([ Button({ id: "spam", label: "Mark as Spam", style: "danger", value: submissionId, }), ]), ], title: "New Form Submission", });`

The form data is dynamic. Whatever keys and values are in the JSON body become fields on the card. A submission with `{"Name": "Jane", "Email": "jane@example.com"}` produces a card with two fields. A submission with ten fields produces a card with ten fields. No schema changes needed.

### Handling actions

When a reviewer clicks a button, Chat SDK routes the event to the right handler based on the action ID:

`bot.onAction(["forward", "spam", "edit"], async (event) => { const submissionId = event.value; if (!submissionId || !event.thread) return; const formData = await getSubmission(submissionId); if (!formData) return; if (event.actionId === "edit") { await event.openModal(editSubmissionModal(formData, submissionId)); } else { const handler = event.actionId === "forward" ? handleForward : handleSpam; await handler(event, formData, submissionId, event.thread.id); } });`

The forward handler sends the email, optionally POSTs to a webhook endpoint, updates the Slack card, and cleans up Redis, all in parallel:

`const handleForward = async (event, formData, submissionId, threadId) => { const slack = bot.getAdapter("slack"); await Promise.all([ forwardToEmail(formData), forwardToEndpoint(formData), slack.editMessage( threadId, event.messageId, forwardedCard(formData, event.user.fullName) ), deleteSubmission(submissionId), ]); };`

After forwarding, the card is replaced with a read-only version showing who forwarded it and where. The submission is deleted from Redis since it's no longer needed.

## How to add Teams, Discord, or other platforms

Chat SDK supports multiple platforms from a single codebase. The cards, fields, and buttons you've already defined render natively on each platform, including Block Kit on Slack, Adaptive Cards on Teams, and Google Chat Cards.

To add Microsoft Teams or another platform, register an additional adapter:

`import { createSlackAdapter } from "@chat-adapter/slack"; import { createTeamsAdapter } from "@chat-adapter/teams"; export const bot = new Chat({ adapters: { slack: createSlackAdapter(), teams: createTeamsAdapter(), }, state, userName: "form-bot", });`

The existing webhook route in `src/index.ts` already uses a `:platform` parameter, so Teams webhooks would be handled at `/api/webhooks/teams` with no additional routing code.

You could also post to multiple platforms at once. For example, you might post form submissions to both a Slack channel and a Teams channel by calling `bot.channel()` with different platform prefixes:

``const slackChannel = bot.channel(`slack:${process.env.SLACK_CHANNEL_ID}`); const teamsChannel = bot.channel(`teams:${process.env.TEAMS_CHANNEL_ID}`); await Promise.all([ slackChannel.post(newSubmissionCard(formData, submissionId)), teamsChannel.post(newSubmissionCard(formData, submissionId)), ]);``

Modals are currently Slack-only, so the Edit & Forward button only works on Slack. On other platforms, you'd want to either hide that button or replace it with a different editing flow.

See the [Chat SDK adapter directory](https://chat-sdk.dev/adapters) for the full list of supported platforms.

## Related resources

*   [Chat SDK Form Bot template](https://github.com/vercel-labs/chat-sdk-form-bot)
    
*   [Chat SDK documentation](https://chat-sdk.dev/docs)
    
*   [Chat SDK GitHub](https://github.com/vercel/chat)
    
*   [The Complete Guide to Chat SDK](https://vercel.com/kb/guide/the-complete-guide-to-chat-sdk)
    
*   [Resend documentation](https://resend.com/docs/api-reference/emails/send-email)
    
*   [Hono documentation](https://hono.dev/docs/getting-started/vercel)

---

[View full KB sitemap](/kb/sitemap.md)
