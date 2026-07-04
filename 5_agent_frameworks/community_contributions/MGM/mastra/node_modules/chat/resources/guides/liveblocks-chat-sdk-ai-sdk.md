# How to build an agent for Liveblocks with Chat SDK and AI SDK

**Author:** Chris Nicholas, Ben Sabic

---

You can build an AI-powered bot that reads and responds to Liveblocks comment threads using [Chat SDK](https://chat-sdk.dev), [AI SDK](https://ai-sdk.dev/docs/reference/ai-sdk-core/tool-loop-agent)'s `ToolLoopAgent`, and the [Liveblocks Chat SDK adapter](https://chat-sdk.dev/adapters/vendor-official/liveblocks). Chat SDK handles webhook verification, message routing, and the Liveblocks API. `ToolLoopAgent` wraps your language model with tools and runs an autonomous reasoning loop, calling tools and feeding results back until it has a complete answer. Redis tracks thread subscriptions and manages distributed locking for concurrent message handling, giving you a production-ready AI bot without managing infrastructure.

This guide walks you through wiring up a Next.js app directory project that responds to @-mentions in Liveblocks threads with streamed AI replies and tool calling.

## Prerequisites

Before you begin, make sure you have:

*   Node.js 18+
    
*   A Next.js app that uses [Liveblocks Comments](https://liveblocks.io/docs/get-started/comments)
    
*   A Liveblocks account and the [dashboard](https://liveblocks.io/dashboard) open
    
*   A Redis instance (local or hosted, such as [Upstash](https://vercel.com/marketplace/upstash))
    
*   A [Vercel account](https://vercel.com/signup) with AI Gateway access
    

## How it works

[Liveblocks Comments](https://liveblocks.io/comments) is a fully featured React commenting system you can embed in any application, giving users threaded discussions, @-mentions, emoji reactions, and notifications out of the box. Threads are attached to specific rooms in your app, making them ideal for contextual conversations around documents, designs, or any shared content.

The `@liveblocks/chat-sdk-adapter` connects Chat SDK to Liveblocks' webhook system. You register event handlers (like `onNewMention` and `onReaction`) and the adapter routes incoming webhook payloads to them. It handles signature verification, parses comment and reaction events, and exposes a consistent thread API for posting replies or adding emoji reactions.

AI SDK's `ToolLoopAgent` wraps a language model with tools and runs an autonomous loop: the model generates text or calls a tool, the SDK executes the tool, feeds the result back, and repeats until the model finishes. When you pass a model string like `"anthropic/claude-sonnet-4-6"` and host your application on Vercel, the AI SDK routes the request through the [Vercel AI Gateway](https://vercel.com/ai-gateway) automatically. Chat SDK accepts any `AsyncIterable<string>` as a message, so you can pass the agent's `fullStream` directly to `thread.post()` for real-time streaming in Liveblocks threads.

The [Redis state adapter](https://chat-sdk.dev/adapters/official/redis) tracks which threads the bot has subscribed to, so follow-up messages in the same thread are handled automatically after the first mention.

## Steps

### 1\. Have your Comments app ready

Before continuing, make sure you have a React app with Liveblocks Comments up and running. If you haven't set that up yet, follow the [quickstart guide](https://liveblocks.io/docs/get-started/comments) first.

### 2\. Install Liveblocks, Chat SDK, and AI SDK

Install the Liveblocks adapter, Chat SDK, AI SDK, and other related packages:

`npm install @liveblocks/chat-sdk-adapter @liveblocks/node chat @chat-adapter/state-redis ai zod`

The `chat` package is the Chat SDK core. `@liveblocks/chat-sdk-adapter` is the Liveblocks platform adapter. `ai` is the AI SDK, which includes `ToolLoopAgent`. `zod` is used to define tool input schemas. `@chat-adapter/state-redis` is the [Redis state adapter,](https://chat-sdk.dev/adapters/official/redis) which handles thread subscriptions and distributed locking.

### 3\. Create a Liveblocks project

Head to the [Liveblocks dashboard](https://liveblocks.io/dashboard), open the project you'd like to use, and copy the **Secret Key** from the **API Keys** page.

### 4\. Add your environment variables

Create a `.env.local` file in your project root:

`LIVEBLOCKS_SECRET_KEY="sk_..." LIVEBLOCKS_WEBHOOK_SECRET="whsec_..." REDIS_URL="redis://localhost:6379"`

You'll create the webhook secret further on in the guide.

Instead of an AI Gateway API key, this guide uses [Vercel OIDC tokens](https://vercel.com/docs/ai-gateway/authentication-and-byok/authentication#oidc-token) to authenticate to the AI Gateway. Link your app to a Vercel project and pull the token into your local environment:

`vercel link vercel env pull`

`vercel env pull` writes a `VERCEL_OIDC_TOKEN` into `.env.local` alongside any other project environment variables. The AI SDK's [gateway provider](https://ai-sdk.dev/providers/ai-sdk-providers/ai-gateway) reads this token automatically when no `AI_GATEWAY_API_KEY` is set, so no code changes are needed.

OIDC tokens expire after 12 hours, so re-run `vercel env pull` during longer development sessions to refresh it. In production on Vercel, the token is generated and rotated for you automatically.

### 5\. Set up user resolution

Create `app/database.ts` to export your bot's user ID and a `getUser` function. Chat SDK calls `resolveUsers` to convert user IDs from @-mentions into display names when constructing messages.

The function must return an object matching this shape:

`type UserInfo = { name: string; avatar?: string; color?: string; };`

In production, query your own user database or auth provider:

`export const BOT_USER_ID = "__bot__"; export const BOT_USER_NAME = "My Bot"; export async function getUser(id: string): Promise<UserInfo | undefined> { const user = await db.users.findUnique({ where: { id } }); return user ? { name: user.displayName, avatar: user.avatarUrl } : undefined; }`

### 6\. Define your agent's tools

Create `app/tools.ts` with the tools your agent can call. Each tool has a `description` that tells the model when to use it, an `inputSchema` that the model fills in, and an `execute` function that runs when the tool is called:

``import { tool } from "ai"; import { z } from "zod"; export const tools = { getWeather: tool({ description: "Get the current weather for a location", inputSchema: z.object({ location: z.string().describe("City name, e.g. San Francisco"), }), execute: async ({ location }) => { // Replace with a real weather API call const response = await fetch( `https://api.weatherapi.com/v1/current.json?key=${process.env.WEATHER_API_KEY}&q=${encodeURIComponent(location)}` ); const data = await response.json(); return { location, temperature: data.current.temp_f, condition: data.current.condition.text, }; }, }), searchDocs: tool({ description: "Search the company documentation for a topic", inputSchema: z.object({ query: z.string().describe("The search query"), }), execute: async ({ query }) => { // Replace with your actual search implementation return { results: [`Result for: ${query}`] }; }, }), };``

### 7\. Create the agent and bot instance

Create `app/bot.ts` with a `ToolLoopAgent` and a `Chat` instance. The agent is configured with a model, a system prompt, and your tools. The bot wires the Liveblocks adapter and Redis state to your event handlers:

`import { Chat } from "chat"; import { createLiveblocksAdapter, LiveblocksAdapter, } from "@liveblocks/chat-sdk-adapter"; import { createRedisState } from "@chat-adapter/state-redis"; import { ToolLoopAgent } from "ai"; import { BOT_USER_ID, BOT_USER_NAME, getUser } from "./database"; import { tools } from "./tools"; const agent = new ToolLoopAgent({ model: "anthropic/claude-sonnet-4-6", instructions: "You are a helpful assistant in a Liveblocks comment thread. " + "Answer questions clearly and use your tools when you need " + "up-to-date information. Keep responses concise.", tools, }); export const bot = new Chat<{ liveblocks: LiveblocksAdapter }>({ userName: BOT_USER_NAME, adapters: { liveblocks: createLiveblocksAdapter({ apiKey: process.env.LIVEBLOCKS_SECRET_KEY!, webhookSecret: process.env.LIVEBLOCKS_WEBHOOK_SECRET!, botUserId: BOT_USER_ID, botUserName: BOT_USER_NAME, resolveUsers: ({ userIds }) => { return userIds.map((id) => getUser(id)); }, }), }, state: createRedisState(), });`

### 8\. Handle mentions and reactions

Add event handlers to `app/bot.ts` after the bot instance. When someone @-mentions the bot, `onNewMention` fires. The handler acknowledges the message with a reaction, then streams the agent's response directly into the thread. `fullStream` is preferred over `textStream` because it preserves paragraph breaks between tool-calling steps:

``// Handle @-mentions of the bot bot.onNewMention(async (thread, message) => { await thread.adapter.addReaction(thread.id, message.id, "👀"); const result = await agent.stream({ prompt: message.text }); await thread.post(result.fullStream); }); // Handle reactions to messages bot.onReaction(async (event) => { if (!event.added) return; await event.adapter.postMessage( event.threadId, `${event.user.userName} reacted with "${event.emoji.name}"` ); });``

### 9\. Create the webhook route

Create the API route at `app/api/webhooks/liveblocks/route.ts`. This is the endpoint Liveblocks will POST webhook events to:

`import { bot } from "@/app/bot"; export async function POST(request: Request) { return bot.webhooks.liveblocks(request, { waitUntil: (p) => void p, }); }`

For production deployments on Vercel, use `waitUntil` from `@vercel/functions` so your handler finishes processing after the HTTP response has been sent. This is required on serverless platforms where the function would otherwise terminate early:

`import { bot } from "@/app/bot"; import { waitUntil } from "@vercel/functions"; export async function POST(request: Request) { return bot.webhooks.liveblocks(request, { waitUntil }); }`

### 10\. Set up Liveblocks webhooks

1.  Expose your dev server with a tunnel, for example using [ngrok](https://ngrok.com):
    
    `npx ngrok http 3000`
    
2.  Go to the [Liveblocks dashboard](https://liveblocks.io/dashboard) and create a new webhook endpoint. Set the URL to your generated ngrok URL, add your webhook route’s pathname to the end, and enable these events in the project dashboard:
    
    *   `commentCreated`
        
    *   `commentReactionAdded`
        
    *   `commentReactionRemoved`
        
3.  Copy the **webhook secret** and add it to `.env.local` as `LIVEBLOCKS_WEBHOOK_SECRET`:
    
    `LIVEBLOCKS_WEBHOOK_SECRET="whsec_..."`
    

Now when users @-mention your bot in a Liveblocks thread, it will stream a response and call tools autonomously.

## How to add Slack, Teams, or other platforms

Chat SDK supports multiple platforms from a single codebase. The event handlers and agent logic you've already defined work identically across all of them, since the SDK normalizes messages, threads, and reactions into a consistent format.

To add Slack or Teams, install the relevant adapter packages and register them alongside the Liveblocks adapter:

`npm install @chat-adapter/slack @chat-adapter/teams`

Then add them to your `Chat` instance in `app/bot.ts`:

`import { createSlackAdapter } from "@chat-adapter/slack"; import { createTeamsAdapter } from "@chat-adapter/teams"; export const bot = new Chat({ userName: BOT_USER_NAME, adapters: { liveblocks: createLiveblocksAdapter({ ... }), slack: createSlackAdapter(), teams: createTeamsAdapter(), }, state: createRedisState(), });`

The existing webhook route already uses a `[platform]` parameter, so each platform gets its own endpoint automatically: `/api/webhooks/slack` and `/api/webhooks/teams`. No additional routing code is needed.

Streaming behavior varies by platform. Slack uses its native streaming API for smooth real-time updates, while Liveblocks and Teams fall back to a post-then-edit pattern that throttles updates to avoid rate limits. You can adjust the update interval with the `streamingUpdateIntervalMs` option when creating your `Chat` instance.

See the [Chat SDK adapter directory](https://chat-sdk.dev/adapters) for the full list of supported platforms and their configuration options.

## Related resources

*   [Chat SDK documentation](https://chat-sdk.dev)
    
*   [Chat SDK adapter directory](https://chat-sdk.dev/adapters)
    
*   [AI SDK agent documentation](https://ai-sdk.dev/docs/agents/building-agents)
    
*   [`@liveblocks/chat-sdk-adapter`](https://liveblocks.io/docs/api-reference/liveblocks-chat-sdk-adapter) [API reference](https://liveblocks.io/docs/api-reference/liveblocks-chat-sdk-adapter)
    
*   [Next.js Chat SDK bot quickstart](https://liveblocks.io/docs/get-started/nextjs-chat-sdk-bot)
    
*   [How to test webhooks on localhost](https://liveblocks.io/docs/guides/how-to-test-webhooks-on-localhost)

---

[View full KB sitemap](/kb/sitemap.md)
