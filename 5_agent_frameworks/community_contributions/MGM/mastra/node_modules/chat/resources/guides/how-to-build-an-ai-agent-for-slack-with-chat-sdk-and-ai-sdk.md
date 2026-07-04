# How to build an AI agent for Slack with Chat SDK and AI SDK

**Author:** Ben Sabic

---

You can build an AI-powered Slack agent that responds to mentions, maintains conversation history, and calls tools autonomously using Chat SDK and AI SDK. Chat SDK handles the platform integration (webhooks, message formatting, thread tracking), while AI SDK's `ToolLoopAgent` manages the reasoning loop that lets your agent call tools and act on results. Together with Vercel AI Gateway and Redis for state, you get a production-ready Slack agent without managing infrastructure or juggling provider SDKs.

This guide will walk you through building a Slack agent with Chat SDK, AI SDK's `ToolLoopAgent`, and Claude via the [Vercel AI Gateway](https://vercel.com/ai-gateway). You'll wire up streaming responses, tool calling, and multi-turn conversation history, then scale your tool set for production with toolpick.

## Prerequisites

Before you begin, make sure you have:

*   Node.js 18+
    
*   [pnpm](https://pnpm.io/) (or npm/yarn)
    
*   A Slack workspace where you can install apps
    
*   A Redis instance (local or hosted, such as [Upstash](https://vercel.com/marketplace/upstash))
    
*   A [Vercel account](https://vercel.com/signup) with an AI Gateway API key
    

## How it works

Chat SDK is a unified TypeScript SDK for building chatbots across Slack, Teams, Discord, and other platforms. You register event handlers (like `onNewMention` and `onSubscribedMessage`), and the SDK routes incoming webhooks to them. The Slack adapter handles webhook verification, message parsing, and the Slack API. The Redis state adapter tracks which threads your bot has subscribed to and manages distributed locking for concurrent message handling.

AI SDK's `ToolLoopAgent` wraps a language model with tools and runs an autonomous loop: the model generates text or calls a tool, the SDK executes the tool, feeds the result back, and repeats until the model finishes. When you pass a model string like `"anthropic/claude-sonnet-4.6"`, and host your application on Vercel, the AI SDK will route the request through the AI Gateway automatically.

Chat SDK accepts any `AsyncIterable<string>` as a message, so you can pass the agent's `fullStream` directly to `thread.post()` for real-time streaming in Slack.

## Steps

### 1\. Scaffold the project, install dependencies, and add Vercel Plugin

Create a new Next.js app and add the Chat SDK, AI SDK, and adapter packages:

`npx create-next-app@latest my-slack-agent --typescript --app cd my-slack-agent pnpm add chat @chat-adapter/slack @chat-adapter/state-redis ai zod`

The `chat` package is the Chat SDK core. The `@chat-adapter/slack` and `@chat-adapter/state-redis` packages are the [Slack platform adapter](https://chat-sdk.dev/adapters/slack) and [Redis state adapter.](https://chat-sdk.dev/adapters/redis) The `ai` package is the AI SDK, which includes the AI Gateway provider and `ToolLoopAgent`. `zod` is used to define tool input schemas.

The [Vercel Plugin](https://vercel.com/docs/agent-resources/vercel-plugin) equips your AI coding agent (e.g., Claude Code) with skills, specialist agents, slash commands, and more.

`npx plugins add vercel/vercel-plugin`

### 2\. Create a Slack app

Go to [api.slack.com/apps](https://api.slack.com/apps), click **Create New App**, then **From a manifest**.

Select your workspace and paste this manifest:

`display_information: name: AI Agent description: An AI agent built with Chat SDK and AI SDK features: bot_user: display_name: AI Agent always_online: true oauth_config: scopes: bot: - app_mentions:read - channels:history - channels:read - chat:write - groups:history - groups:read - im:history - im:read - mpim:history - mpim:read - reactions:read - reactions:write - users:read settings: event_subscriptions: request_url: https://your-domain.com/api/webhooks/slack bot_events: - app_mention - message.channels - message.groups - message.im - message.mpim interactivity: is_enabled: true request_url: https://your-domain.com/api/webhooks/slack org_deploy_enabled: false socket_mode_enabled: false token_rotation_enabled: false`

After creating the app:

1.  Go to **Install App**, and install the app to your workspace
    
2.  Go to **OAuth & Permissions** > **OAuth Tokens** and copy the **Bot User OAuth Token**
    
3.  Go to **Basic Information** > **App Credentials** and copy the **Signing Secret**
    

You'll replace the `request_url` placeholders with your real domain after deploying (or a tunnel URL for local testing).

### 3\. Configure environment variables

Create a `.env.local` file in your project root:

`SLACK_BOT_TOKEN=xoxb-your-bot-token SLACK_SIGNING_SECRET=your-signing-secret REDIS_URL=redis://localhost:6379 AI_GATEWAY_API_KEY=your-ai-gateway-api-key`

The Slack adapter reads `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` automatically. The Redis state adapter reads `REDIS_URL`. AI SDK uses `AI_GATEWAY_API_KEY` to authenticate with the Vercel AI Gateway, or alternatively, use [OIDC authentication](https://ai-sdk.dev/providers/ai-sdk-providers/ai-gateway#oidc-authentication-vercel-deployments).

You can create an AI Gateway API key from your [Vercel dashboard](https://vercel.com) under **AI Gateway** and click **Create an API Key**.

### 4\. Define your agent's tools

Create `lib/tools.ts` with the tools your agent can call. This example defines a weather tool and docs tool, but you can add any tools your use case requires:

``import { tool } from "ai"; import { z } from "zod"; export const tools = { getWeather: tool({ description: "Get the current weather for a location", inputSchema: z.object({ location: z.string().describe("City name, e.g. San Francisco"), }), execute: async ({ location }) => { // Replace with a real weather API call const response = await fetch( `https://api.weatherapi.com/v1/current.json?key=${process.env.WEATHER_API_KEY}&q=${encodeURIComponent(location)}` ); const data = await response.json(); return { location, temperature: data.current.temp_f, condition: data.current.condition.text, }; }, }), searchDocs: tool({ description: "Search the company documentation for a topic", inputSchema: z.object({ query: z.string().describe("The search query"), }), execute: async ({ query }) => { // Replace with your actual search implementation return { results: [`Result for: ${query}`] }; }, }), };``

Each tool has a `description` (which tells the model when to use it), an `inputSchema` (a Zod schema that the model fills in), and an `execute` function that runs when the tool is called.

### 5\. Create the agent and bot

Create `lib/bot.ts` with a `ToolLoopAgent` and a `Chat` instance:

`import { Chat } from "chat"; import { toAiMessages } from "chat/ai"; import { createSlackAdapter } from "@chat-adapter/slack"; import { createRedisState } from "@chat-adapter/state-redis"; import { ToolLoopAgent } from "ai"; import { tools } from "./tools"; const agent = new ToolLoopAgent({ model: "anthropic/claude-sonnet-4.6", instructions: "You are a helpful AI assistant in a Slack workspace. " + "Answer questions clearly and use your tools when you need " + "real-time data. Keep responses concise and well-formatted for chat.", tools, }); export const bot = new Chat({ userName: "ai-agent", adapters: { slack: createSlackAdapter(), }, state: createRedisState(), }); // Handle first-time mentions bot.onNewMention(async (thread, message) => { await thread.subscribe(); const result = await agent.stream({ prompt: message.text }); await thread.post(result.fullStream); }); // Handle follow-up messages in subscribed threads bot.onSubscribedMessage(async (thread, message) => { const allMessages = []; for await (const msg of thread.allMessages) { allMessages.push(msg); } const history = await toAiMessages(allMessages); const result = await agent.stream({ messages: history }); await thread.post(result.fullStream); });`

When someone @mentions the bot, `onNewMention` fires. The handler subscribes to the thread (to track future messages in that thread) and streams the agent's response. For follow-up messages, `onSubscribedMessage` retrieves the full thread history using `thread.allMessages`, converts it to the AI SDK message format with `toAiMessages`and passes it to the agent so it has a complete conversation context.

The `fullStream` is preferred over `textStream` because it preserves paragraph breaks between tool-calling steps. Chat SDK auto-detects the stream type and handles Slack's native streaming API for real-time updates.

### 6\. Wire up the webhook route

Create the API route at `app/api/webhooks/[platform]/route.ts`:

``import { after } from "next/server"; import { bot } from "@/lib/bot"; type Platform = keyof typeof bot.webhooks; export async function POST( request: Request, context: RouteContext<"/api/webhooks/[platform]"> ) { const { platform } = await context.params; const handler = bot.webhooks[platform as Platform]; if (!handler) { return new Response(`Unknown platform: ${platform}`, { status: 404 }); } return handler(request, { waitUntil: (task) => after(() => task), }); }``

This creates a `POST /api/webhooks/slack` endpoint. The `waitUntil` option ensures your event handlers finish processing after the HTTP response is sent, which is required on serverless platforms where the function would otherwise terminate early.

### 7\. Test locally

1.  Start the dev server:
    
    `pnpm dev`
    
2.  Expose it with a tunnel:
    
    `npx ngrok http 3000`
    
3.  Copy the tunnel URL (for example, `https://abc123.ngrok-free.dev`) and update both **Event Subscriptions** and **Interactivity** Request URLs in your [Slack app settings](https://api.slack.com/apps) to `https://abc123.ngrok-free.dev/api/webhooks/slack`
    
4.  Invite the bot to a channel (`/invite @AI Agent`)
    
5.  @mention the bot with a question. You should see a streaming response appear in the thread. Try asking it to use one of your tools, such as "What's the weather in San Francisco?"
    

### 8\. Deploy to Vercel

First, link your project and add your environment variables:

`vercel link vercel env add SLACK_BOT_TOKEN vercel env add SLACK_SIGNING_SECRET vercel env add REDIS_URL vercel env add AI_GATEWAY_API_KEY`

Alternatively, add them in the Vercel dashboard under **Settings** > **Environment Variables**.

Then deploy:

`vercel`

Update the **Event Subscriptions** and **Interactivity** Request URLs in your Slack app settings to your production URL, for example `https://my-slack-agent.vercel.app/api/webhooks/slack`.

When deployed to Vercel, AI Gateway supports OIDC-based authentication, so you can also authenticate without a static API key. See the [AI Gateway authentication docs](https://vercel.com/docs/ai-gateway/authentication-and-byok#oidc-tokens).

## Troubleshooting

### Bot doesn't respond to mentions

Check that your Slack app has the `app_mentions:read` scope and that the **Event Subscriptions** Request URL is correct. Slack sends a challenge request when you first set the URL, so your server must be running.

### Streaming appears choppy or delayed

Chat SDK uses Slack's native streaming API for smooth updates. If you're seeing issues, check that your Redis connection is stable, as the SDK uses distributed locks to manage concurrent messages.

### Tool calls fail silently

If the agent calls a tool but no result appears, check for errors in your tool's `execute` function. AI SDK surfaces tool execution errors back to the model, which may attempt to recover. Add error handling in your tools and check your server logs for details.

### Thread history grows too large

For long-running threads, the conversation history can exceed the model's context window. Consider limiting the number of messages you pass to the agent by slicing the history array or by using a summarization step for older messages.

## Scaling to many tools with toolpick

The agent in this guide has two tools. In production, a Slack agent often grows to 15, 20, or 30 tools as you integrate services like GitHub, [Linear](https://vercel.com/marketplace/linear), [Upstash](https://vercel.com/marketplace/upstash), calendars, and deploy pipelines. At that scale, every tool definition is sent to the model on every step, which increases token costs and makes it harder for the model to pick the right tool.

[toolpick](https://www.npmjs.com/package/toolpick) solves this by indexing your tools at startup and selecting only the most relevant ones for each step. It hooks into `ToolLoopAgent` via the `prepareStep` option, so you don't need to change your handler logic.

### Install toolpick

`pnpm add toolpick`

### Create a tool index

Build an index from your full tool set. toolpick uses a combination of keyword matching and semantic embeddings to find the best tools for each step:

`import { createToolIndex } from "toolpick"; const toolIndex = createToolIndex(tools, { embeddingModel: "openai/text-embedding-3-small", });`

For higher accuracy with vague queries (like "ship it" or "ping the team"), add a re-ranker model that uses a cheap LLM to pick the final candidates:

`const toolIndex = createToolIndex(tools, { embeddingModel: "openai/text-embedding-3-small", rerankerModel: "openai/gpt-4o-mini", });`

### Update your agent to use toolpick

Pass `toolIndex.prepareStep()` to your `ToolLoopAgent`. This sets `activeTools` on each step, so the model only sees the tools it needs, while all tools remain available for execution:

`const agent = new ToolLoopAgent({ model: "anthropic/claude-sonnet-4.6", instructions: "..." tools, prepareStep: toolIndex.prepareStep(), });`

If the model can't find a relevant tool in the current selection, toolpick automatically moves to the next page of results. After two misses, it exposes all tools as a fallback. Your agent never gets stuck in a loop, unable to find the right tool.

### Enrich descriptions and cache embeddings

For an extra accuracy boost, enable `enrichDescriptions` to expand your tool descriptions with synonyms and alternative phrasings. This runs a one-time LLM call during `warmUp()` at server startup. You can also persist the computed embeddings to disk with `fileCache` so subsequent restarts skip the embedding API call entirely:

`import { createToolIndex, fileCache } from "toolpick"; const toolIndex = createToolIndex(tools, { embeddingModel: "openai/text-embedding-3-small", rerankerModel: "openai/gpt-4o-mini", enrichDescriptions: true, embeddingCache: fileCache(".toolpick-cache.json"), }); await toolIndex.warmUp();`

This setup is optional for agents with a handful of tools, but becomes worthwhile as your tool set grows. The per-step cost of re-ranking with `gpt-4o-mini` is approximately $0.0001, which is negligible compared to the token savings from sending fewer tool definitions to the primary model.

## How to add Teams, Discord, or other platforms

Chat SDK supports multiple platforms from a single codebase. The event handlers and agent logic you've already defined work identically across all of them, since the SDK normalizes messages, threads, and reactions into a consistent format.

To add Microsoft Teams or another platform, register an additional adapter:

`import { createSlackAdapter } from "@chat-adapter/slack"; import { createTeamsAdapter } from "@chat-adapter/teams"; export const bot = new Chat({ adapters: { slack: createSlackAdapter(), teams: createTeamsAdapter(), }, state, userName: "ai-agent", });`

The existing webhook route in `src/index.ts` already uses a `:platform` parameter, so Teams webhooks would be handled at `/api/webhooks/teams` with no additional routing code.

Streaming behavior varies by platform. Slack uses its native streaming API for smooth real-time updates, while Teams, Discord, and Google Chat fall back to a post-then-edit pattern that throttles updates to avoid rate limits. You can adjust the update interval with the `streamingUpdateIntervalMs` option when creating your `Chat` instance.

See the [Chat SDK adapter directory](https://chat-sdk.dev/adapters) for the full list of supported platforms.

### Other Chat SDK Guides

## Related resources

*   [Chat SDK streaming](https://chat-sdk.dev/docs/streaming)
    
*   [Chat SDK actions](https://chat-sdk.dev/docs/actions) and [cards](https://chat-sdk.dev/docs/cards)
    
*   [AI SDK agent documentation](https://ai-sdk.dev/docs/agents/building-agents)
    
*   [AI Gateway documentation](https://vercel.com/docs/ai-gateway)
    
*   [toolpick documentation](https://github.com/pontusab/toolpick)

---

[View full KB sitemap](/kb/sitemap.md)
