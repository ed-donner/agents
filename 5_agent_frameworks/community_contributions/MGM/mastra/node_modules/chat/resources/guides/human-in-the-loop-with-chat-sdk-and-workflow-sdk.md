# Human-in-the-Loop with Chat SDK and Workflow SDK

**Author:** Ben Sabic

---

You can pause a durable workflow until a human approves it in Slack by combining Chat SDK and Workflow SDK. Chat SDK posts an interactive card with Approve and Deny buttons; Workflow SDK's `createWebhook` generates a URL that those buttons POST to when clicked, suspending the workflow until the click arrives. The workflow resumes with the click payload, decides what to do, and continues, with no `onAction` handler, no custom approval database, and no polling.

This guide walks you through suspending a workflow with `createWebhook`, posting a Chat SDK approval card with `callbackUrl` buttons, and resuming the workflow based on the user's choice. You'll add a timeout so abandoned approvals can't suspend forever, and see how to extend the pattern to multiple decision points within a single workflow.

## Prerequisites

Before you begin, make sure you have:

*   Node.js 18 or later
    
*   An existing [Chat SDK](https://chat-sdk.dev) bot (see the [Slack agent guide](https://vercel.com/kb/guide/how-to-build-an-ai-agent-for-slack-with-chat-sdk-and-ai-sdk) or [Slack file bot guide](https://vercel.com/kb/guide/slack-bot-vercel-blob))
    
*   A project configured for [Workflow SDK](https://workflow-sdk.dev/docs/getting-started)
    
*   A [Vercel account](https://vercel.com/signup) if you're deploying to Vercel
    

> Workflow SDK runs against any [world](https://workflow-sdk.dev/worlds); a pluggable backend for storage, queuing, and authentication. When you deploy to Vercel, [Vercel Workflows](https://vercel.com/workflows) is selected automatically with zero configuration. For self-hosted setups, see [Postgres World](https://workflow-sdk.dev/worlds/postgres) and the other providers.

## How it works

Three pieces fit together:

*   **Workflow SDK** runs the long-lived process. A function becomes durable when you mark it with `"use workflow"`: it can suspend, resume, and survive crashes without losing state. `createWebhook()` returns an object with a `url` that's a public endpoint. When you `await` it, the workflow is suspended until that endpoint receives an HTTP request.
    
*   **Chat SDK** presents the decision to a human. A `<Button callbackUrl="...">` posts the click's action data to the URL you supply, in addition to firing any `onAction` handler. When the URL is the workflow's `webhook.url`, the click resumes the workflow directly.
    
*   **The pairing** removes the usual glue. There's no separate approvals table, no `onAction` callback that has to look up which workflow is waiting, and no polling. The workflow suspends, the user clicks, and the same workflow function picks up where it left off with the click payload in hand.
    

`createWebhook()` is the right primitive when the workflow itself owns the resume URL. For cases where you'd rather keep the URL private and resume from your own server code, use `createHook()` with a deterministic business token instead.

## Steps

### 1\. Install dependencies

Add Workflow SDK to a project that already has a Chat SDK bot set up:

`pnpm add workflow`

If you're starting from scratch, also install a few Chat SDK packages:

`pnpm add chat @chat-adapter/slack @chat-adapter/state-redis`

The `workflow` package is Workflow SDK's core. The `chat` package is the Chat SDK core, and `@chat-adapter/slack` and `@chat-adapter/state-redis` are the [Slack platform adapter](https://chat-sdk.dev/adapters/official/slack) and [Redis state adapter](https://chat-sdk.dev/adapters/official/redis). See the [Chat SDK getting started guide](https://vercel.com/kb/guide/the-complete-guide-to-chat-sdk) and [Slack agent guide](https://vercel.com/kb/guide/how-to-build-an-ai-agent-for-slack-with-chat-sdk-and-ai-sdk) if you don't have a bot yet.

### 2\. Define the approval workflow

Create `workflows/approval.ts`:

``import { createWebhook } from "workflow"; import { finalizeApprovalCard, postApprovalCard, postReply, } from "@/lib/slack"; export async function requestDeployApproval(opts: { threadId: string; version: string; requestedBy: string; }) { "use workflow"; using webhook = createWebhook(); const messageId = await postApprovalCard({ threadId: opts.threadId, version: opts.version, requestedBy: opts.requestedBy, webhookUrl: webhook.url, }); const request = await webhook; const payload = await request.json(); if (payload.actionId === "approve") { await deploy(opts.version); await finalizeApprovalCard({ threadId: opts.threadId, messageId, version: opts.version, requestedBy: opts.requestedBy, outcome: `Approved by <@${payload.user.id}> — ${opts.version} deployed.`, }); await postReply( opts.threadId, `Deployed **${opts.version}** by <@${payload.user.id}>.`, ); } else { await finalizeApprovalCard({ threadId: opts.threadId, messageId, version: opts.version, requestedBy: opts.requestedBy, outcome: `Denied by <@${payload.user.id}>.`, }); await postReply( opts.threadId, `Deploy of **${opts.version}** denied by <@${payload.user.id}>.`, ); } } async function deploy(version: string) { "use step"; // Trigger your deploy here. This runs as a durable step, // so retries and observability come for free. }``

The workflow is intentionally thin. It owns the webhook and the resume logic; everything else (posting the card, sending follow-up messages, triggering the deploy) is a step. That separation keeps the workflow body deterministic and pushes side effects into retryable units.

Next, define the helper steps in `lib/slack.ts`:

``import { Card, CardText, Actions, Button } from "chat"; import { bot } from "@/lib/bot"; export async function postApprovalCard(opts: { threadId: string; version: string; requestedBy: string; webhookUrl: string; }): Promise<string> { "use step"; const thread = bot.thread(opts.threadId); const sent = await thread.post( <Card title={`Deploy ${opts.version}?`} subtitle={`Requested by ${opts.requestedBy}`}> <CardText>Approve to roll out **{opts.version}**, or deny to abort.</CardText> <Actions> <Button id="approve" style="primary" callbackUrl={opts.webhookUrl}> Approve </Button> <Button id="deny" style="danger" callbackUrl={opts.webhookUrl}> Deny </Button> </Actions> </Card>, ); return sent.id; } // Re-render the approval card without the Actions block, swapping the // buttons for a static outcome line. The title, subtitle, and body text // stay the same so the thread keeps its context. export async function finalizeApprovalCard(opts: { threadId: string; messageId: string; version: string; requestedBy: string; outcome: string; }) { "use step"; const thread = bot.thread(opts.threadId); await thread.adapter.editMessage( thread.id, opts.messageId, <Card title={`Deploy ${opts.version}?`} subtitle={`Requested by ${opts.requestedBy}`}> <CardText>Approve to roll out **{opts.version}**, or deny to abort.</CardText> <CardText>{opts.outcome}</CardText> </Card>, ); } // Post a follow-up message as markdown so platforms with native markdown // support render bold/italic/links instead of literal asterisks. Plain // strings are passed through as-is — `{ markdown }` is the explicit form. export async function postReply(threadId: string, markdown: string) { "use step"; await bot.thread(threadId).post({ markdown }); }``

`bot.thread(threadId)` constructs a `Thread` reference from a serialized ID, which is exactly the entry point Chat SDK provides for posting outside an event handler. Thread IDs follow the format `adapter:channel:thread` (for example, `slack:C123ABC:1234567890.123456`) and round-trip cleanly through JSON, so they're safe to pass as workflow inputs.

**Key details in this workflow**

*   The `using` declaration ensures the webhook is cleaned up automatically when the workflow exits, even if it throws.
    
*   Both buttons point at the same `webhook.url`. The `actionId` travels in the callback payload, so a single webhook handles all the buttons on the card.
    
*   `await webhook` suspends the workflow. The function pauses here until the user clicks, which could take seconds, hours, or days. Workflow SDK persists the state and resumes on the click.
    
*   The `deploy` function is marked `"use step"`, which makes it a durable step with automatic retries and observability. Workflow SDK only re-runs steps when they fail, not on resumption.
    
*   `postApprovalCard` returns the posted message's `id`, and `finalizeApprovalCard` calls `thread.adapter.editMessage` to re-render the card without buttons once the decision is in. That prevents a stale click on the original card from hitting the consumed webhook, and it leaves a clear audit trail in the thread.
    
*   `postReply` posts with `{ markdown }` rather than a bare string. The bare-string form is passed through as-is, so `**bold**` would render as literal asterisks on Slack and Teams; the `{ markdown }` form is converted to the platform's native markup.
    

If you need to preserve more of the original thread context across the workflow boundary (for example, the triggering message or thread metadata), use `thread.toJSON()` on the way in and [`bot.reviver()`](https://chat-sdk.dev/docs/api/thread) when restoring on the other side. For the approval flow above, the thread ID is enough.

### 3\. Start the workflow

Trigger the workflow from wherever the approval request originates.

From a Chat SDK handler:

`import { start } from "workflow/api"; import { requestDeployApproval } from "@/workflows/approval"; bot.onNewMention(async (thread, message) => { const version = parseVersion(message.text); if (!version) { await thread.post("Usage: @bot deploy v1.2.3"); return; } await start(requestDeployApproval, [ { threadId: thread.id, version, requestedBy: message.author.fullName, }, ]); });`

`start` queues the workflow run and returns immediately with a run handle, allowing the mention handler to respond without blocking. The workflow takes over from there, posting the card, suspending on the webhook, and resuming when the user clicks.

### 4\. Read the callback payload

Chat SDK POSTs a JSON body to the callback URL with this shape:

`{ "type": "action", "actionId": "approve", "value": "approve", "user": { "id": "U123", "name": "alice" }, "threadId": "slack:C123:1234567890.123", "messageId": "1234567890.456" }`

\- `actionId` is the button's `id` prop: `"approve"` or `"deny"` in this workflow.

\- `value` is the optional `value` prop you set on the button, a string for passing extra context to the handler. It's most useful when multiple buttons share an `id` (so `actionId` alone can't distinguish them) or when the button needs to carry a record identifier like `"item-123"`. In the approval workflow above, the buttons have distinct `id`s, so `value` isn't set and arrives as `undefined`.

\- `user` is the user who clicked, regardless of who triggered the workflow.

Use `actionId` to branch on which button was pressed, and [`user.id`](http://user.id) to record or validate who approved.

## Handling multiple decision points

For workflows that need more than one approval, call `createWebhook()` multiple times. Each call generates a fresh URL, so suspensions are independent:

``export async function multiStageApproval(opts: { threadId: string }) { "use workflow"; using draftReview = createWebhook(); const draftTitle = "Approve draft?"; const draftMessageId = await postPrompt(opts.threadId, draftTitle, draftReview.url); const draftPayload = await (await draftReview).json(); if (draftPayload.actionId !== "approve") { await finalizePromptCard(opts.threadId, draftMessageId, draftTitle, `Rejected by <@${draftPayload.user.id}>.`); return; } await finalizePromptCard(opts.threadId, draftMessageId, draftTitle, `Approved by <@${draftPayload.user.id}>.`); using finalReview = createWebhook(); const finalTitle = "Approve final?"; const finalMessageId = await postPrompt(opts.threadId, finalTitle, finalReview.url); const finalPayload = await (await finalReview).json(); if (finalPayload.actionId !== "approve") { await finalizePromptCard(opts.threadId, finalMessageId, finalTitle, `Rejected by <@${finalPayload.user.id}>.`); return; } await finalizePromptCard(opts.threadId, finalMessageId, finalTitle, `Approved by <@${finalPayload.user.id}>.`); await publish(); }``

This workflow relies on two helpers used at each stage. Add `postPrompt` and `finalizePromptCard` to `lib/slack.ts`:

`export async function postPrompt( threadId: string, title: string, webhookUrl: string, ): Promise<string> { "use step"; const thread = bot.thread(threadId); const sent = await thread.post( <Card title={title}> <Actions> <Button id="approve" style="primary" callbackUrl={webhookUrl}> Approve </Button> <Button id="deny" style="danger" callbackUrl={webhookUrl}> Deny </Button> </Actions> </Card>, ); return sent.id; } export async function finalizePromptCard( threadId: string, messageId: string, title: string, outcome: string, ) { "use step"; const thread = bot.thread(threadId); await thread.adapter.editMessage( thread.id, messageId, <Card title={title}> <CardText>{outcome}</CardText> </Card>, ); }`

Each `using` declaration scopes the webhook to its block, so cleanup happens as soon as the workflow moves past that approval. `finalizePromptCard` strips the buttons once a decision lands, so every stage shows its final state without leaving stale buttons in the thread. The workflow itself can suspend at any point, without you tracking which webhook is which, since the runtime handles that.

## Adding a timeout

A workflow that suspends on a webhook indefinitely is fine until someone forgets to click. Race the webhook against a durable `sleep` to bound the wait:

``import { createWebhook, sleep } from "workflow"; export async function approvalWithTimeout(opts: { threadId: string }) { "use workflow"; using webhook = createWebhook(); const title = "Proceed with the change?"; const messageId = await postPrompt(opts.threadId, title, webhook.url); const result = await Promise.race([ webhook.then(async (req) => ({ kind: "clicked" as const, body: await req.json() })), sleep("24h").then(() => ({ kind: "timeout" as const })), ]); if (result.kind === "timeout") { await finalizePromptCard(opts.threadId, messageId, title, "Timed out after 24h — no decision recorded."); return; } await finalizePromptCard( opts.threadId, messageId, title, `${result.body.actionId === "approve" ? "Approved" : "Denied"} by <@${result.body.user.id}>.`, ); if (result.body.actionId === "approve") { await proceed(); } }``

`sleep` is itself a durable suspension, so the 24-hour wait costs nothing while it's pending and survives deploys. When the timeout wins the race, the workflow continues without resuming the webhook, and the `using` cleanup releases the URL. The card is finalized in both branches, so the timeout is visible in the thread rather than silently leaving a stale set of buttons.

## Validating the approver

The callback URL is authenticated only by its token, which means anyone who can intercept the URL can resume the workflow. For sensitive operations, validate the user in the payload before continuing:

``const APPROVERS = new Set(["U_ALICE", "U_BOB"]); const request = await webhook; const payload = await request.json(); if (!APPROVERS.has(payload.user.id)) { await thread.post( `<@${payload.user.id}> isn't authorized to approve this deploy.`, ); return; }``

For stronger guarantees, switch to [`createHook()`](https://workflow-sdk.dev/docs/api-reference/workflow/create-hook) and resume the workflow from your own authenticated route with `resumeHook()`. That pattern keeps the resume URL private and gives you full control over the authorization check, at the cost of writing a route handler.

## Troubleshooting

### The workflow never resumes after a click

Confirm the button's `callbackUrl` matches `webhook.url` exactly. The URL contains a token that's bound to the suspension, so a stale or hand-edited URL won't resolve. Check the Workflow SDK CLI to see whether the workflow is still suspended on the webhook:

`npx workflow inspect runs --web`

If the click reached the URL but the workflow didn't move, look for an error in the workflow logs. The `using` declaration disposes the webhook on the next throw, so an uncaught error in the workflow body can release the URL before the click arrives.

### `ValidationError` when posting the card on Discord or Telegram

Discord's `custom_id` has a 100-character limit; Telegram's `callback_data` has a 64-byte limit. The encoded button data is the action ID plus the callback token, which can exceed those caps. Shorten the action ID (`"a"` instead of `"approve-deploy-v1-2-3"`) and move long context into `value` or out of the card entirely. Slack and Teams don't have this limit.

### The same approval card gets clicked twice

The main flow above guards against this by calling `finalizeApprovalCard` immediately after the decision lands. The card is re-rendered without its `Actions` block, so there's nothing left to click. If you skip that step, Chat SDK won't dedupe clicks for you: once `await webhook` has resolved, a second click hits a webhook that no longer exists, and the user sees the platform's default error. Either edit the card to remove the buttons (the pattern shown above, via `thread.adapter.editMessage`), or accept that only the first click matters and ignore the rest.

### A workflow run shows as suspended forever

Workflows suspend until something resumes them. If your callback URL was lost (for example, a card was deleted before anyone could click), the run will stay suspended until its associated webhook is cleaned up. Use a timeout (see above) to bound every suspension, and use the Workflow SDK CLI to cancel runs that should no longer wait:

`npx workflow inspect runs # find the run ID, then: npx workflow runs cancel <run-id>`

## Related resources

*   [Chat SDK Threads, Messages, and Channels](https://chat-sdk.dev/docs/threads-messages-channels)
    
*   [Chat SDK Actions](https://chat-sdk.dev/docs/actions)
    
*   [Workflow SDK](https://workflow-sdk.dev/docs/api-reference/workflow/create-webhook) [`createWebhook`](https://workflow-sdk.dev/docs/api-reference/workflow/create-webhook)
    
*   [Workflow SDK](https://workflow-sdk.dev/docs/api-reference/workflow/create-hook) [`createHook`](https://workflow-sdk.dev/docs/api-reference/workflow/create-hook)
    
*   [Workflow SDK Human-in-the-Loop example](https://workflow-sdk.dev/cookbook/agent-patterns/human-in-the-loop)
    
*   [How to build an AI agent for Slack with Chat SDK and AI SDK](https://vercel.com/kb/guide/how-to-build-an-ai-agent-for-slack-with-chat-sdk-and-ai-sdk)

---

[View full KB sitemap](/kb/sitemap.md)
