# How to build a Slack bot with Next.js and Redis

**Author:** Hayden Bleasel, Ben Sabic

---

You can build a Slack bot that responds to @mentions, tracks thread context, and sends rich interactive messages using Chat SDK with Next.js. Chat SDK handles the platform integration (webhook verification, message parsing, and the Slack API) while a Redis state adapter tracks which threads your bot has subscribed to across serverless invocations. Together with Vercel for deployment, you get a production-ready Slack bot without managing infrastructure or writing platform-specific glue code.

This guide will walk you through scaffolding a Next.js app, configuring a Slack app, wiring up event handlers with Chat SDK, adding interactive cards and buttons, and deploying to Vercel.

## Prerequisites

Before you begin, make sure you have:

*   Node.js 18+
    
*   [pnpm](https://pnpm.io/) (or npm/yarn)
    
*   A Slack workspace where you can install apps
    
*   A Redis instance (local or hosted, such as [Upstash](https://vercel.com/marketplace/upstash))
    

## How it works

Chat SDK is a unified TypeScript SDK for building chatbots across Slack, Teams, Discord, and other platforms. You register event handlers (like `onNewMention` and `onSubscribedMessage`), and the SDK routes incoming webhooks to them. The Slack adapter handles webhook verification, message parsing, and the Slack API. The Redis state adapter tracks which threads your bot has subscribed to and manages distributed locking for concurrent message handling.

When a user @mentions your bot, `onNewMention` fires. Calling `thread.subscribe()` tells the SDK to track that thread, so subsequent messages trigger `onSubscribedMessage`. This lets your bot maintain conversation context across multiple turns without you managing thread state yourself.

## Steps

### 1\. Scaffold the project and install dependencies

Create a new Next.js app and add the Chat SDK and adapter packages:

`npx create-next-app@latest my-slack-bot --typescript --app cd my-slack-bot pnpm add chat @chat-adapter/slack @chat-adapter/state-redis`

The `chat` package is the Chat SDK core. The `@chat-adapter/slack` and `@chat-adapter/state-redis` packages are the [Slack platform adapter](https://chat-sdk.dev/adapters/official/slack) and [Redis state adapter](https://chat-sdk.dev/adapters/official/redis).

### 2\. Create a Slack app

Go to [api.slack.com/apps](https://api.slack.com/apps), click **Create New App**, then **From an app manifest**.

Select your workspace and paste the following manifest:

`display_information: name: My Bot description: A bot built with Chat SDK features: bot_user: display_name: My Bot always_online: true oauth_config: scopes: bot: - app_mentions:read - channels:history - channels:read - chat:write - groups:history - groups:read - im:history - im:read - mpim:history - mpim:read - reactions:read - reactions:write - users:read settings: event_subscriptions: request_url: https://your-domain.com/api/webhooks/slack bot_events: - app_mention - message.channels - message.groups - message.im - message.mpim interactivity: is_enabled: true request_url: https://your-domain.com/api/webhooks/slack org_deploy_enabled: false socket_mode_enabled: false token_rotation_enabled: false`

Replace [`https://your-domain.com/api/webhooks/slack`](https://your-domain.com/api/webhooks/slack) with your deployed webhook URL, then click **Create**.

After creating the app:

1.  Go to **OAuth & Permissions**, click **Install to Workspace**, and copy the **Bot User OAuth Token** (`xoxb-...`). You'll need this as `SLACK_BOT_TOKEN`
    
2.  Go to **Basic Information** → **App Credentials** and copy the **Signing Secret**. You'll need this as `SLACK_SIGNING_SECRET`
    

If you're distributing the app across multiple workspaces via OAuth instead of installing it to one workspace, configure `clientId` and `clientSecret` on the Slack adapter and pass the same redirect URI used during the authorize step into `handleOAuthCallback(request, { redirectUri })` in your callback route.

### 3\. Configure environment variables

Create a `.env.local` file in your project root:

`SLACK_BOT_TOKEN=xoxb-your-bot-token SLACK_SIGNING_SECRET=your-signing-secret REDIS_URL=redis://localhost:6379`

The Slack adapter auto-detects `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` from your environment, and `createRedisState()` reads `REDIS_URL` automatically.

### 4\. Create the bot

Create `lib/bot.ts` with a `Chat` instance configured with the Slack adapter:

``import { Chat } from "chat"; import { createSlackAdapter } from "@chat-adapter/slack"; import { createRedisState } from "@chat-adapter/state-redis"; export const bot = new Chat({ userName: "mybot", adapters: { slack: createSlackAdapter(), }, state: createRedisState(), }); // Respond when someone @mentions the bot bot.onNewMention(async (thread) => { await thread.subscribe(); await thread.post("Hello! I'm listening to this thread now."); }); // Respond to follow-up messages in subscribed threads bot.onSubscribedMessage(async (thread, message) => { await thread.post(`You said: ${message.text}`); });``

`onNewMention` fires when a user @mentions your bot. Calling `thread.subscribe()` tells the SDK to track that thread, so subsequent messages trigger `onSubscribedMessage`.

### 5\. Create the webhook route

Create a dynamic API route that handles incoming webhooks:

``import { after } from "next/server"; import { bot } from "@/lib/bot"; type Platform = keyof typeof bot.webhooks; export async function POST( request: Request, context: RouteContext<"/api/webhooks/[platform]"> ) { const { platform } = await context.params; const handler = bot.webhooks[platform as Platform]; if (!handler) { return new Response(`Unknown platform: ${platform}`, { status: 404 }); } return handler(request, { waitUntil: (task) => after(() => task), }); }``

This creates a `POST /api/webhooks/slack` endpoint. The `waitUntil` option ensures message processing completes after the HTTP response is sent. This is required on serverless platforms where the function would otherwise terminate before your handlers finish.

### 6\. Test locally

1.  Start your development server (`pnpm dev`)
    
2.  Expose it with a tunnel (e.g. `ngrok http 3000`)
    
3.  Update the Slack Event Subscriptions **Request URL** to your tunnel URL
    
4.  Invite your bot to a Slack channel (`/invite @mybot`)
    
5.  @mention the bot. It should respond with "Hello! I'm listening to this thread now."
    
6.  Reply in the thread. It should echo your message back
    

### 7\. Add interactive features

Chat SDK supports rich interactive messages using a JSX-like syntax. Update your bot to send cards with buttons:

``import { Chat, Card, CardText as Text, Actions, Button, Divider } from "chat"; import { createSlackAdapter } from "@chat-adapter/slack"; import { createRedisState } from "@chat-adapter/state-redis"; export const bot = new Chat({ userName: "mybot", adapters: { slack: createSlackAdapter(), }, state: createRedisState(), }); bot.onNewMention(async (thread) => { await thread.subscribe(); await thread.post( <Card title="Welcome!"> <Text>I'm now listening to this thread. Try clicking a button:</Text> <Divider /> <Actions> <Button id="hello" style="primary">Say Hello</Button> <Button id="info">Show Info</Button> </Actions> </Card> ); }); bot.onAction("hello", async (event) => { await event.thread.post(`Hello, ${event.user.fullName}!`); }); bot.onAction("info", async (event) => { await event.thread.post(`You're on ${event.thread.adapter.name}.`); });``

The file extension must be `.tsx` (not `.ts`) when using JSX components like `Card` and `Button`. Make sure your `tsconfig.json` has `"jsx": "react-jsx"` and `"jsxImportSource": "chat"`.

### 8\. Deploy to Vercel

Deploy your bot to Vercel:

`vercel deploy`

After deployment, set your environment variables in the Vercel dashboard (`SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, `REDIS_URL`). If your manifest used a placeholder URL, update the **Event Subscriptions** and **Interactivity** Request URLs in your [Slack app settings](https://api.slack.com/apps) to your production URL.

## Troubleshooting

### Bot doesn't respond to mentions

Check that your Slack app has the `app_mentions:read` scope and that the **Event Subscriptions** Request URL is correct. Slack sends a challenge request when you first set the URL, so your server must be running and reachable.

### Webhook signature verification fails

Confirm that `SLACK_SIGNING_SECRET` matches the value in your Slack app's **Basic Information** → **App Credentials**. A mismatched or missing signing secret will cause the adapter to reject incoming webhooks.

### Redis connection errors

Verify that `REDIS_URL` is reachable from your deployment environment. If running locally, make sure your Redis instance is started. The state adapter uses Redis for distributed locking, so the bot won't process messages without a working connection.

### Handlers don't run to completion on Vercel

Make sure your webhook route passes `waitUntil` to the handler, as shown in step 5. Without it, serverless functions can terminate before your event handlers finish.

* * *

## Build with a template or read more.

---

[View full KB sitemap](/kb/sitemap.md)
