# Create a Discord support bot with Nuxt and Redis

**Author:** Hayden Bleasel, Ben Sabic

---

You can build a Discord support bot that answers questions with AI, sends interactive cards with buttons, and escalates to human agents on demand by combining Chat SDK, AI SDK, and Nuxt. Chat SDK handles the platform integration (Gateway connection, event parsing, and the Discord API), while AI SDK generates responses using Claude. A Redis state adapter tracks subscribed threads across serverless invocations so conversations stay in context.

This guide will walk you through scaffolding a Nuxt app, configuring a Discord application, wiring up Chat SDK with the Discord adapter, adding AI-powered responses and interactive cards, setting up the Gateway forwarder, and deploying to Vercel.

## Prerequisites

Before you begin, make sure you have:

*   Node.js 18+
    
*   [pnpm](https://pnpm.io/) (or npm/yarn)
    
*   A Discord server where you have admin access
    
*   A Redis instance (local or hosted, such as [Upstash](https://vercel.com/marketplace/upstash))
    
*   An [Anthropic API key](https://console.anthropic.com/)
    

## How it works

Chat SDK is a unified TypeScript SDK for building chatbots across Discord, Slack, Teams, and other platforms. You register event handlers (like `onNewMention` and `onSubscribedMessage`), and the SDK routes incoming events to them. The Discord adapter handles Gateway connection, webhook verification, and the Discord API. The Redis state adapter tracks which threads your bot has subscribed to and manages distributed locking for concurrent message handling.

Discord doesn't push messages to HTTP webhooks like Slack does. Instead, messages arrive through Discord's Gateway WebSocket. The Discord adapter includes a built-in Gateway listener that connects to the WebSocket and forwards events to your webhook endpoint, so the rest of your bot logic looks the same as any other Chat SDK adapter.

When someone @mentions the bot, `onNewMention` fires and posts a support card. Calling `thread.subscribe()` tells the SDK to track that thread, so subsequent messages trigger `onSubscribedMessage` where AI SDK generates a response using Claude.

## Steps

### 1\. Scaffold the project and install dependencies

Create a new Nuxt app and add the Chat SDK, AI SDK, and adapter packages:

`npx nuxi@latest init my-discord-bot cd my-discord-bot pnpm add chat @chat-adapter/discord @chat-adapter/state-redis ai @ai-sdk/anthropic`

The `chat` package is the Chat SDK core. The `@chat-adapter/discord` and `@chat-adapter/state-redis` packages are the [Discord platform adapter](https://chat-sdk.dev/adapters/official/discord) and [Redis state adapter](https://chat-sdk.dev/adapters/official/redis). The `ai` and `@ai-sdk/anthropic` packages are used to generate responses with Claude.

### 2\. Create a Discord app

1.  Go to [discord.com/developers/applications](https://discord.com/developers/applications)
    
2.  Click **New Application**, give it a name, and click **Create**
    
3.  Go to **Bot** in the sidebar and click **Reset Token**. Copy the token, you'll need this as `DISCORD_BOT_TOKEN`
    
4.  Under **Privileged Gateway Intents**, enable **Message Content Intent**
    
5.  Go to **General Information** and copy the **Application ID** and **Public Key**. You'll need these as `DISCORD_APPLICATION_ID` and `DISCORD_PUBLIC_KEY`
    

Then set up the Interactions endpoint:

1.  In **General Information**, set the **Interactions Endpoint URL** to [`https://your-domain.com/api/webhooks/discord`](https://your-domain.com/api/webhooks/discord)
    
2.  Discord will send a PING to verify the endpoint. You'll need to deploy first or use a tunnel
    

Then invite the bot to your server:

1.  Go to **OAuth2** in the sidebar
    
2.  Under **OAuth2 URL Generator**, select the `bot` scope
    
3.  Under **Bot Permissions**, select:
    
    *   Send Messages
        
    *   Create Public Threads
        
    *   Send Messages in Threads
        
    *   Read Message History
        
    *   Add Reactions
        
    *   Use Slash Commands
        
4.  Copy the generated URL and open it in your browser to invite the bot
    

### 3\. Configure environment variables

Create a `.env` file in your project root:

`DISCORD_BOT_TOKEN=your_bot_token DISCORD_PUBLIC_KEY=your_public_key DISCORD_APPLICATION_ID=your_application_id REDIS_URL=redis://localhost:6379 ANTHROPIC_API_KEY=your_anthropic_api_key`

The Discord adapter reads `DISCORD_BOT_TOKEN`, `DISCORD_PUBLIC_KEY`, and `DISCORD_APPLICATION_ID` automatically. The Redis state adapter reads `REDIS_URL`, and AI SDK's Anthropic provider reads `ANTHROPIC_API_KEY`.

### 4\. Create the bot

Create `server/lib/bot.tsx` with a `Chat` instance configured with the Discord adapter. This bot uses AI SDK to answer support questions:

``import { Chat, Card, CardText as Text, Actions, Button, Divider } from "chat"; import { createDiscordAdapter } from "@chat-adapter/discord"; import { createRedisState } from "@chat-adapter/state-redis"; import { generateText } from "ai"; import { anthropic } from "@ai-sdk/anthropic"; export const bot = new Chat({ userName: "support-bot", adapters: { discord: createDiscordAdapter(), }, state: createRedisState(), }); bot.onNewMention(async (thread) => { await thread.subscribe(); await thread.post( <Card title="Support"> <Text>Hey! I'm here to help. Ask your question in this thread and I'll do my best to answer it.</Text> <Divider /> <Actions> <Button id="escalate" style="danger">Escalate to Human</Button> </Actions> </Card> ); }); bot.onSubscribedMessage(async (thread, message) => { await thread.startTyping(); const { text } = await generateText({ model: anthropic("claude-sonnet-4-5-20250514"), system: "You are a friendly support bot. Answer questions concisely. If you don't know the answer, say so and suggest the user click 'Escalate to Human'.", prompt: message.text, }); await thread.post(text); }); bot.onAction("escalate", async (event) => { await event.thread.post( `${event.user.fullName} requested human support. A team member will follow up shortly.` ); });``

The file extension must be `.tsx` (not `.ts`) when using JSX components like `Card` and `Button`. Make sure your `tsconfig.json` has `"jsx": "react-jsx"` and `"jsxImportSource": "chat"`.

`onNewMention` fires when a user @mentions the bot. Calling `thread.subscribe()` tells the SDK to track that thread, so subsequent messages trigger `onSubscribedMessage` where AI SDK generates a response.

### 5\. Create the webhook route

Create a server route that handles incoming Discord webhooks:

``import { bot } from "../lib/bot"; type Platform = keyof typeof bot.webhooks; export default defineEventHandler(async (event) => { const platform = getRouterParam(event, "platform") as Platform; const handler = bot.webhooks[platform]; if (!handler) { throw createError({ statusCode: 404, message: `Unknown platform: ${platform}` }); } const request = toWebRequest(event); return handler(request, { waitUntil: (task) => event.waitUntil(task), }); });``

This creates a `POST /api/webhooks/discord` endpoint. The `waitUntil` option ensures message processing completes after the HTTP response is sent.

### 6\. Set up the Gateway forwarder

Discord doesn't push messages to webhooks like Slack does. Instead, messages arrive through the Gateway WebSocket. The Discord adapter includes a built-in Gateway listener that connects to the WebSocket and forwards events to your webhook endpoint.

Create a route that starts the Gateway listener:

``import { bot } from "../../lib/bot"; export default defineEventHandler(async (event) => { await bot.initialize(); const discord = bot.getAdapter("discord"); if (!discord) { throw createError({ statusCode: 404, message: "Discord adapter not configured" }); } const baseUrl = process.env.NUXT_PUBLIC_SITE_URL || "http://localhost:3000"; const webhookUrl = `${baseUrl}/api/webhooks/discord`; const durationMs = 10 * 60 * 1000; // 10 minutes return discord.startGatewayListener( { waitUntil: (task: Promise<unknown>) => event.waitUntil(task) }, durationMs, undefined, webhookUrl, ); });``

The Gateway listener connects to Discord's WebSocket, receives messages, and forwards them to your webhook endpoint for processing. In production, you'll want a cron job to restart it periodically.

### 7\. Test locally

1.  Start your development server (`pnpm dev`)
    
2.  Trigger the Gateway listener by visiting [`http://localhost:3000/api/discord/gateway`](http://localhost:3000/api/discord/gateway) in your browser
    
3.  Expose your server with a tunnel (e.g. `ngrok http 3000`)
    
4.  Update the **Interactions Endpoint URL** in your Discord app settings to your tunnel URL (e.g. [`https://abc123.ngrok.io/api/webhooks/discord`](https://abc123.ngrok.io/api/webhooks/discord))
    
5.  @mention the bot in your Discord server. It should respond with a support card
    
6.  Reply in the thread. AI SDK should generate a response
    
7.  Click **Escalate to Human**. The bot should post an escalation message
    

### 8\. Add a cron job for production

The Gateway listener runs for a fixed duration. In production, set up a cron job to restart it automatically. If you're deploying to Vercel, add a `vercel.json`:

`{ "crons": [ { "path": "/api/discord/gateway", "schedule": "*/9 * * * *" } ] }`

This restarts the Gateway listener every 9 minutes, ensuring continuous connectivity. Protect the endpoint with a `CRON_SECRET` environment variable in production.

### 9\. Deploy to Vercel

Deploy your bot to Vercel:

`vercel deploy`

After deployment, set your environment variables in the Vercel dashboard (`DISCORD_BOT_TOKEN`, `DISCORD_PUBLIC_KEY`, `DISCORD_APPLICATION_ID`, `REDIS_URL`, `ANTHROPIC_API_KEY`). Update the **Interactions Endpoint URL** in your Discord app settings to your production URL.

## Troubleshooting

### Bot doesn't respond to mentions

Check that **Message Content Intent** is enabled under **Privileged Gateway Intents** in your Discord app settings. Without it, the bot can't read message content and won't see @mentions. Also confirm the Gateway listener is running by visiting `/api/discord/gateway` or checking that the cron job is configured in production.

### Interactions endpoint verification fails

Discord sends a signed PING request to verify your endpoint. Confirm that `DISCORD_PUBLIC_KEY` matches the value in your Discord app's **General Information** page. A mismatched or missing public key will cause the adapter to reject the verification request.

### Gateway listener disconnects frequently

The listener runs for a fixed duration (10 minutes in this guide) and must be restarted. In production, use the cron job shown in step 8 to restart it every 9 minutes. If disconnections happen sooner, check your server logs for WebSocket errors and verify that `DISCORD_BOT_TOKEN` is valid.

### AI responses are slow or time out

`generateText` blocks until the full response is returned. For long answers, consider switching to streaming with `streamText` and passing the stream directly to [`thread.post`](http://thread.post)`()`. See the [Streaming docs](https://chat-sdk.dev/docs/streaming) for details.

### Redis connection errors

Verify that `REDIS_URL` is reachable from your deployment environment. The state adapter uses Redis for distributed locking, so the bot won't process messages without a working connection.

* * *

## Build with a template or read more.

---

[View full KB sitemap](/kb/sitemap.md)
