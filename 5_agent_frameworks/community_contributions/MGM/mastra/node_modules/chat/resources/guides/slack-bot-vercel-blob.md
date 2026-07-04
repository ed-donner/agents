# How to build a Slack bot that manages files in Vercel Blob

**Author:** Ben Sabic

---

You can build a Slack bot that browses, reads, uploads, and deletes files in Vercel Blob by combining Chat SDK, AI SDK's `ToolLoopAgent`, and Files SDK's pre-built tool factory. Chat SDK handles the chat piece, AI SDK runs the agent loop, and Files SDK exposes your Blob store to the agent as a set of approval-gated tools. The result is a chat-first interface to your object storage, with read tools that run freely and write tools that prompt for approval by default.

This guide will walk you through building a Slack bot with Chat SDK, AI SDK's `ToolLoopAgent`, and Files SDK's `createFileTools` factory backed by [Vercel Blob](https://vercel.com/storage/blob). You'll wire up streaming responses, tool calling, and multi-turn conversation history, then configure per-tool approval gates and read-only mode to keep write operations safe in production.

## Prerequisites

Before you begin, make sure you have:

*   Node.js 18 or later
    
*   [pnpm](https://pnpm.io/) (or npm/yarn)
    
*   A Slack workspace where you can install apps
    
*   A Redis instance (local or hosted, such as [Upstash](https://vercel.com/marketplace/upstash))
    
*   A [Vercel account](https://vercel.com/signup) with AI Gateway and Vercel Blob
    

## How it works

Three SDKs cover three distinct layers:

*   **Chat SDK** is the platform layer. It receives Slack webhooks, normalizes them into events like `onNewMention` and `onSubscribedMessage`, and streams responses back to Slack's native streaming API.
    
*   **AI SDK** is the reasoning layer. `ToolLoopAgent` wraps a language model with tools and runs the loop where the model picks a tool, the SDK executes it, and the result feeds back into the next step until the model finishes.
    
*   **Files SDK** is the storage layer. It presents a single `Files` interface over Vercel Blob, S3, R2, and other providers, and ships a `createFileTools` factory that turns that interface into ready-to-use AI SDK tools.
    

`createFileTools` returns eight tools, split between four read tools (`listFiles`, `getFileMetadata`, `downloadFile`, `getFileUrl`) and four write tools (`uploadFile`, `deleteFile`, `copyFile`, `signUploadUrl`). Write tools require approval by default, while read tools run freely, and you decide how to surface the approval gate to your users.

Chat SDK accepts any `AsyncIterable<string>` as a message, so the agent's `fullStream` flows straight into `thread.post()` for real-time streaming in Slack.

Learn more about Chat SDK in [The Complete Guide to Chat SDK](https://vercel.com/kb/guide/the-complete-guide-to-chat-sdk).

## Steps

### 1\. Scaffold the project and install dependencies

Create a new Next.js app and install the Chat SDK, AI SDK, Files SDK, and other related packages:

`npx create-next-app@latest my-files-bot --typescript --app cd my-files-bot pnpm add chat @chat-adapter/slack @chat-adapter/state-redis ai zod files-sdk @vercel/blob`

The `chat` package is the Chat SDK core, and `@chat-adapter/slack` and `@chat-adapter/state-redis` are the [Slack platform adapter](https://chat-sdk.dev/adapters/official/slack) and [Redis state adapter](https://chat-sdk.dev/adapters/official/redis). The `ai` package is AI SDK, which includes the [AI Gateway provider](https://ai-sdk.dev/providers/ai-sdk-providers/ai-gateway) and `ToolLoopAgent`. `files-sdk` is the storage SDK, and `@vercel/blob` is the optional peer dependency required by the Vercel Blob adapter. `zod` is used for tool input schemas.

### 2\. Create a Slack app

Go to [api.slack.com/apps](https://api.slack.com/apps), click **Create New App**, then **From a manifest**.

Select your workspace and paste this manifest:

`display_information: name: Files Bot description: A file management bot built with Chat SDK, AI SDK, and Files SDK features: bot_user: display_name: Files Bot always_online: true oauth_config: scopes: bot: - app_mentions:read - channels:history - channels:read - chat:write - files:read - groups:history - groups:read - im:history - im:read - mpim:history - mpim:read - reactions:read - reactions:write - users:read settings: event_subscriptions: request_url: https://your-domain.com/api/webhooks/slack bot_events: - app_mention - message.channels - message.groups - message.im - message.mpim interactivity: is_enabled: true request_url: https://your-domain.com/api/webhooks/slack org_deploy_enabled: false socket_mode_enabled: false token_rotation_enabled: false`

After creating the app:

1.  Go to **Install App** and install the app to your workspace
    
2.  Go to **OAuth & Permissions** > **OAuth Tokens** and copy the **Bot User OAuth Token**
    
3.  Go to **Basic Information** > **App Credentials** and copy the **Signing Secret**
    

You'll replace the `request_url` placeholders with your real domain after deploying (or a tunnel URL for local testing). The `files:read` scope is included so the bot can later read files users add to Slack threads.

### 3\. Create a Vercel Blob store

In your Vercel dashboard, open **Storage**, click **Create Database**, and create a new **Blob** store. Connect it to the project you'll be deploying to. Vercel will add `BLOB_READ_WRITE_TOKEN` to your project’s environment variables for you, so you don’t need to manage the token yourself.

For local development, link your project and pull the token into `.env.local` with the [Vercel CLI](https://vercel.com/docs/cli):

`vercel link vercel env pull`

This writes `BLOB_READ_WRITE_TOKEN` into `.env.local`.

### 4\. Configure environment variables

Add the remaining environment variables to `.env.local`:

`` SLACK_BOT_TOKEN=xoxb-your-bot-token SLACK_SIGNING_SECRET=your-signing-secret REDIS_URL=redis://localhost:6379 VERCEL_OIDC_TOKEN=your-OIDC-token # BLOB_READ_WRITE_TOKEN comes from `vercel env pull` ``

The Slack adapter reads `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` automatically. The Redis state adapter reads `REDIS_URL`. AI SDK uses `VERCEL_OIDC_TOKEN` to authenticate with the Vercel AI Gateway with [OIDC authentication](https://vercel.com/docs/ai-gateway/authentication-and-byok/authentication#oidc-token). Files SDK will also read `BLOB_READ_WRITE_TOKEN` automatically when handling file operations.

### 5\. Configure Files SDK with the Vercel Blob adapter

Create `lib/files.ts`:

``import { Files } from "files-sdk"; import { vercelBlob } from "files-sdk/vercel-blob"; // BLOB_READ_WRITE_TOKEN is added automatically on Vercel and pulled into // .env.local via `vercel env pull` for local development. export const files = new Files({ adapter: vercelBlob(), });``

The `vercelBlob` adapter defaults to `access: "public"`, which matches the most common Blob usage and lets the agent return permanent CDN URLs from `getFileUrl`. For private buckets, pass `vercelBlob({ access: "private" })`, which routes uploads through Vercel's private mode and reads through the API instead of a public URL. With private access, `getFileUrl` throws because no permanent URL exists; use `downloadFile` instead.

### 6\. Build the agent and bot

Create `lib/bot.ts`:

`import { Chat } from "chat"; import { toAiMessages } from "chat/ai"; import { createSlackAdapter } from "@chat-adapter/slack"; import { createRedisState } from "@chat-adapter/state-redis"; import { ToolLoopAgent } from "ai"; import { createFileTools } from "files-sdk/ai-sdk"; import { files } from "./files"; const agent = new ToolLoopAgent({ model: "anthropic/claude-sonnet-4.6", instructions: "You are a file management assistant in a Slack workspace. " + "Use the file tools to help users browse, read, upload, and delete " + "files in their object storage. When a write operation is rejected, " + "explain what you were about to do and ask the user to confirm.", tools: createFileTools({ files }), }); export const bot = new Chat({ userName: "files-bot", adapters: { slack: createSlackAdapter(), }, state: createRedisState(), }); // Handle first-time mentions bot.onNewMention(async (thread, message) => { await thread.subscribe(); const result = await agent.stream({ prompt: message.text }); await thread.post(result.fullStream); }); // Handle follow-up messages in subscribed threads bot.onSubscribedMessage(async (thread) => { const { messages } = await thread.adapter.fetchMessages(thread.id, { limit: 20, }); const history = await toAiMessages(messages); const result = await agent.stream({ prompt: history }); await thread.post(result.fullStream); });`

**A few things are happening here:**

*   `createFileTools({ files })` returns all eight file tools. Read tools run immediately when the agent calls them; write tools (`uploadFile`, `deleteFile`, `copyFile`, `signUploadUrl`) are gated by AI SDK's tool approval flow.
    
*   `toAiMessages` converts the most recent 20 Chat SDK messages into the AI SDK `ModelMessage[]` shape, preserving roles, attachments, and chronological order.
    
*   `result.fullStream` is preferred over `textStream` because it preserves paragraph breaks between tool-calling steps, which Slack renders cleanly.
    
*   `bot.onNewMention` fires the first time someone @mentions the bot in a channel. `thread.subscribe()` opts the thread into future `onSubscribedMessage` events so the bot keeps responding without further mentions.
    

### 7\. Wire up the webhook route

Create `app/api/webhooks/[platform]/route.ts`:

``import { after } from "next/server"; import { bot } from "@/lib/bot"; type Platform = keyof typeof bot.webhooks; export async function POST( request: Request, context: RouteContext<"/api/webhooks/[platform]">, ) { const { platform } = await context.params; const handler = bot.webhooks[platform as Platform]; if (!handler) { return new Response(`Unknown platform: ${platform}`, { status: 404 }); } return handler(request, { waitUntil: (task) => after(() => task), }); }``

This creates a `POST /api/webhooks/slack` endpoint. The `waitUntil` option ensures event handlers finish processing after the HTTP response is sent, which is required on Vercel where the function would otherwise terminate as soon as the response returns.

### 8\. Test locally

1.  Start the dev server:
    
    `pnpm dev`
    
2.  Expose it with a tunnel:
    
    `npx ngrok http 3000`
    
3.  Copy the tunnel URL (for example, [`https://abc123.ngrok-free.dev`](https://abc123.ngrok-free.dev)) and update both **Event Subscriptions** and **Interactivity** Request URLs in your [Slack app settings](https://api.slack.com/apps) to [`https://abc123.ngrok-free.dev/api/webhooks/slack`](https://abc123.ngrok-free.dev/api/webhooks/slack).
    
4.  Invite the bot to a channel: `/invite @Files Bot`.
    
5.  @mention the bot and ask it to list files: "Show me what's in the bucket." The agent calls `listFiles` and streams the response back into the thread. To test a write operation end-to-end before building an approval flow, temporarily pass `requireApproval: false` to `createFileTools` in `lib/bot.ts` and ask the bot to "Upload a file called test.txt with the contents 'hello world'."
    

### 9\. Deploy to Vercel

Link your project and add your environment variables:

`vercel env add SLACK_BOT_TOKEN vercel env add SLACK_SIGNING_SECRET vercel env add REDIS_URL`

Alternatively, add them in the Vercel dashboard under **Environment Variables**.

Reminder: `BLOB_READ_WRITE_TOKEN` is already managed by the Blob store connection from step three. You don't need to add it manually.

Then deploy to production:

`vercel --prod`

Update the **Event Subscriptions** and **Interactivity** Request URLs in your Slack app settings to your production URL, for example [`https://my-files-bot.vercel.app/api/webhooks/slack`](https://my-files-bot.vercel.app/api/webhooks/slack).

## Configuring approval and read-only mode

The default `createFileTools({ files })` gates every write tool with approval and leaves reads open. That's a reasonable default, but you'll often want to tune it.

### Granular approval

Pass an object to `requireApproval` to opt individual tools in or out:

`const tools = createFileTools({ files, requireApproval: { deleteFile: true, signUploadUrl: true, uploadFile: false, copyFile: false, }, });`

Unspecified entries default to `true`, so it's safe to opt in only the cases you trust. In the example above, the agent can upload and copy without prompting, but still needs approval for deletes and pre-signed upload URLs.

For a production-grade approval handler that pauses the workflow in Slack until a human clicks Approve or Deny, see [Human-in-the-Loop with Chat SDK and Workflow SDK](https://vercel.com/kb/guide/human-in-the-loop-with-chat-sdk-and-workflow-sdk). The same pattern wraps any write tool from `createFileTools`.

### Read-only mode

For a bot that should only browse and summarize files, pass `readOnly: true`:

`const tools = createFileTools({ files, readOnly: true }); // Returns only: listFiles, getFileMetadata, downloadFile, getFileUrl`

Read-only mode drops every write tool from the toolset, so approval configuration becomes irrelevant. This is useful when the bot's job is to find a file and hand the user a download URL rather than mutate the bucket.

### Tightening descriptions per tool

If you want to scope a tool's behavior to your domain (for example, "list files in the Acme team folder"), use `overrides` to patch the description without touching the underlying implementation:

`const tools = createFileTools({ files, overrides: { listFiles: { description: "List files in the current Slack workspace's bucket", }, deleteFile: { title: "Remove file" }, }, });`

`execute`, `inputSchema`, and `outputSchema` are intentionally not overridable. Override descriptions to improve tool selection, override titles for clearer approval UIs, and let the SDK keep ownership of the I/O contract.

## Reading Slack uploads with `toAiMessages`

When users upload files to a Slack thread, `toAiMessages` automatically includes them in the AI SDK message stream. Images become `image` parts and supported text files (JSON, XML, YAML, plain text) become `file` parts, both with base64 data. Video and audio attachments are skipped, with a `console.warn` by default.

This means a user can drag a CSV into the thread and ask, "Upload this to reports/q4.csv," and the agent will see the file contents in its message history and can call `uploadFile` with that content. No extra wiring needed.

To customize how unsupported attachments are handled, pass `onUnsupportedAttachment`:

``const history = await toAiMessages(messages, { onUnsupportedAttachment: (attachment, message) => { logger.warn( `Skipped ${attachment.type} in message ${message.id}`, ); }, });``

PDFs and other unrecognized MIME types are silently skipped. If you need to handle them, fetch the raw attachment via `attachment.fetchData()` in your handler and route it directly to `files.upload()` outside the agent loop.

## Troubleshooting

### The bot doesn't respond to mentions

Check that your Slack app has the `app_mentions:read` scope and that the **Event Subscriptions** Request URL is correct. Slack sends a challenge request when you first set the URL, so your server must be running and reachable.

### Tool calls fail silently

If the agent calls a tool but no result appears, check your server logs for thrown errors. Common causes include a missing `BLOB_READ_WRITE_TOKEN`, an invalid file key, or a `vercelBlob({ access: "private" })` adapter trying to call `getFileUrl`. AI SDK surfaces tool execution errors back to the model, which may attempt to recover; add explicit error handling in your tools if you need to control how the model sees the failure.

### Write operations are always rejected

By default, write tools require approval. Until you build an approval handler that resolves these requests, every write call will be denied. For development, pass `requireApproval: false` to disable the gate, or `requireApproval: { deleteFile: true }` to leave only the most destructive operations gated.

### `getFileUrl` throws on private blobs

`vercelBlob({ access: "private" })` has no permanent public URL, so `getFileUrl` (which wraps `url()`) throws an error. Use `downloadFile` to fetch private blob contents through the API instead. If you need both public and private blobs in the same bot, construct two `Files` instances with different adapters and route the agent to the right one through separate tools.

### Thread history grows too large

For long-running threads, the conversation history can exceed the model's context window. Limit the number of messages passed to the agent (the example above uses `limit: 20`) or summarize older messages in a separate step.

## How to add Teams, Discord, or other platforms

Chat SDK supports multiple platforms from a single codebase. The event handlers and agent logic you've already defined work identically across all of them, since the SDK normalizes messages, threads, and reactions into a consistent format.

To add Microsoft Teams or another platform, register an additional adapter:

`import { createSlackAdapter } from "@chat-adapter/slack"; import { createTeamsAdapter } from "@chat-adapter/teams"; export const bot = new Chat({ adapters: { slack: createSlackAdapter(), teams: createTeamsAdapter(), }, state, userName: "files-bot", });`

The existing webhook route already uses a `:platform` parameter, so Teams webhooks would be handled at `/api/webhooks/teams` with no additional routing code.

Streaming behavior varies by platform. Slack uses its native streaming API for smooth real-time updates, while Teams, Discord, and Google Chat fall back to a post-then-edit pattern that throttles updates to avoid rate limits. You can adjust the update interval with the `streamingUpdateIntervalMs` option when creating your `Chat` instance.

See the [Chat SDK adapter directory](https://chat-sdk.dev/adapters) for the full list of supported platforms.

### Other Chat SDK Guides

## Related resources

*   [Chat SDK AI utilities overview](https://chat-sdk.dev/docs/ai)
    
*   [Files SDK AI SDK integration](https://files-sdk.dev/ai)
    
*   [Files SDK Vercel Blob adapter](https://files-sdk.dev/adapters/vercel-blob)
    
*   [How to build an AI agent for Slack with Chat SDK and AI SDK](https://vercel.com/kb/guide/how-to-build-an-ai-agent-for-slack-with-chat-sdk-and-ai-sdk)
    
*   [AI SDK agents documentation](https://ai-sdk.dev/docs/agents/building-agents)
    
*   [Vercel Blob documentation](https://vercel.com/docs/storage/vercel-blob)
    
*   [AI Gateway documentation](https://vercel.com/docs/ai-gateway)

---

[View full KB sitemap](/kb/sitemap.md)
