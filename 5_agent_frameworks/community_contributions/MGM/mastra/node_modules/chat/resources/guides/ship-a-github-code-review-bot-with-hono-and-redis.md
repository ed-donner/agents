# Ship a GitHub code review bot with Hono and Redis

**Author:** Hayden Bleasel, Ben Sabic

---

You can ship a GitHub bot that reviews pull requests on demand by combining Chat SDK, Vercel Sandbox, and AI SDK. When a user @mentions the bot on a PR, Chat SDK picks up the mention, spins up a Vercel Sandbox with the repo cloned, and uses AI SDK to analyze the diff. The sandbox gives the agent safe shell access to the repository, so it can run `git diff`, read source files, and explore the codebase without any code escaping a disposable environment.

This guide will walk you through scaffolding a Hono app, configuring a GitHub webhook, wiring up Chat SDK with the GitHub adapter, running a sandboxed AI review, and deploying to Vercel.

## Prerequisites

Before you begin, make sure you have:

*   Node.js 18+
    
*   [pnpm](https://pnpm.io/) (or npm/yarn)
    
*   A GitHub repository where you have admin access
    
*   A Redis instance (local or hosted, such as [Upstash](https://vercel.com/marketplace/upstash))
    
*   A [Vercel account](https://vercel.com/signup)
    

## How it works

Chat SDK is a unified TypeScript SDK for building chatbots across GitHub, Slack, Teams, and other platforms. You register event handlers (like `onNewMention` and `onSubscribedMessage`), and the SDK routes incoming webhooks to them. The GitHub adapter handles signature verification, event parsing, and routing, while the Redis state adapter tracks which threads your bot has subscribed to and manages distributed locking for concurrent message handling.

When someone @mentions the bot on a pull request, the handler fetches the PR's head and base branches, creates a Vercel Sandbox with the repo cloned, and gives an AI SDK `ToolLoopAgent` a `bash` tool scoped to that sandbox. The agent can run `git diff`, read files, and explore the codebase freely. Everything it runs stays inside the sandbox, which is destroyed after the review completes.

## Steps

### 1\. Scaffold the project and install dependencies

Create a new Hono app and add the Chat SDK, AI SDK, and adapter packages:

`pnpm create hono my-review-bot cd my-review-bot pnpm add @octokit/rest @vercel/functions @vercel/sandbox ai bash-tool chat @chat-adapter/github @chat-adapter/state-redis`

Select the `vercel` template when prompted by `create-hono`. This sets up the project for Vercel deployment with the correct entry point.

The `chat` package is the Chat SDK core. The `@chat-adapter/github` and `@chat-adapter/state-redis` packages are the [GitHub platform adapter](https://chat-sdk.dev/adapters/official/github) and [Redis state adapter](https://chat-sdk.dev/adapters/official/redis). `@vercel/sandbox` provides the ephemeral execution environment, and `bash-tool` wires it up as an AI SDK tool.

### 2\. Configure a GitHub webhook

1.  Go to your repository **Settings**, then **Webhooks**, then **Add webhook**
    
2.  Set **Payload URL** to [`https://your-domain.com/api/webhooks/github`](https://your-domain.com/api/webhooks/github)
    
3.  Set **Content type** to `application/json`
    
4.  Set a **Secret** and save it. You'll need this as `GITHUB_WEBHOOK_SECRET`
    
5.  Under **Which events would you like to trigger this webhook?**, select **Let me select individual events** and check:
    
    *   **Issue comments** (for @mention on the PR conversation tab)
        
    *   **Pull request review comments** (for @mention on inline review threads)
        

Then gather your credentials:

1.  Go to [Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens) and create a token with `repo` scope. You'll need this as `GITHUB_TOKEN`
    
2.  Copy the **Webhook secret** you set above. You'll need this as `GITHUB_WEBHOOK_SECRET`
    

### 3\. Configure environment variables

Create a `.env` file in your project root:

`GITHUB_TOKEN=ghp_your_personal_access_token GITHUB_WEBHOOK_SECRET=your_webhook_secret REDIS_URL=redis://localhost:6379 BOT_USERNAME=my-review-bot`

The model (`anthropic/claude-sonnet-4.6`) uses AI Gateway. Develop locally by linking to your Vercel project with `vc link`, then pulling your OIDC token with `vc pull --environment development`.

### 4\. Define the review function

Create the core review logic. This clones the repo into a Vercel Sandbox, then uses AI SDK with a bash tool to let Claude analyze the diff and read files directly.

``import { Sandbox } from "@vercel/sandbox"; import { ToolLoopAgent, stepCountIs } from "ai"; import { createBashTool } from "bash-tool"; interface ReviewInput { owner: string; repo: string; prBranch: string; baseBranch: string; } export async function reviewPullRequest(input: ReviewInput): Promise<string> { const { owner, repo, prBranch, baseBranch } = input; const sandbox = await Sandbox.create({ source: { type: "git", url: `https://github.com/${owner}/${repo}`, username: "x-access-token", password: process.env.GITHUB_TOKEN, depth: 50, }, timeout: 5 * 60 * 1000, }); try { await sandbox.runCommand("git", ["fetch", "origin", prBranch, baseBranch]); await sandbox.runCommand("git", ["checkout", prBranch]); const diffResult = await sandbox.runCommand("git", [ "diff", `origin/${baseBranch}...HEAD`, ]); const diff = await diffResult.output("stdout"); const { tools } = await createBashTool({ sandbox }); const agent = new ToolLoopAgent({ model: "anthropic/claude-sonnet-4.6", tools, stopWhen: stepCountIs(20), }); const result = await agent.generate({ prompt: `You are reviewing a pull request for bugs and issues. Here is the diff for this PR: \`\`\`diff ${diff} \`\`\` Use the bash and readFile tools to inspect any files you need more context on. Look for bugs, security issues, performance problems, and missing error handling. Organize findings by severity (critical, warning, suggestion). If the code looks good, say so.`, }); return result.text; } finally { await sandbox.stop(); } }``

The `createBashTool` gives the agent `bash`, `readFile`, and `writeFile` tools, all scoped to the sandbox. The agent can run `git diff`, read source files, and explore the repo freely without any code escaping the sandbox.

The function returns the review text instead of posting it directly. This lets the Chat SDK handler post it as a threaded reply.

### 5\. Create the bot

Create a `Chat` instance with the GitHub adapter. When someone @mentions the bot on a PR, it fetches the PR metadata, runs the review, and posts the result back to the thread.

`import { Chat } from "chat"; import { createGitHubAdapter } from "@chat-adapter/github"; import { createRedisState } from "@chat-adapter/state-redis"; import { Octokit } from "@octokit/rest"; import { reviewPullRequest } from "./review"; import type { GitHubRawMessage } from "@chat-adapter/github"; const octokit = new Octokit({ auth: process.env.GITHUB_TOKEN }); export const bot = new Chat({ userName: process.env.BOT_USERNAME!, adapters: { github: createGitHubAdapter(), }, state: createRedisState(), }); bot.onNewMention(async (thread, message) => { const raw = message.raw as GitHubRawMessage; const { owner, repo, prNumber } = { owner: raw.repository.owner.login, repo: raw.repository.name, prNumber: raw.prNumber, }; // Fetch PR branch info const { data: pr } = await octokit.pulls.get({ owner, repo, pull_number: prNumber, }); await thread.post("Starting code review..."); await thread.subscribe(); const review = await reviewPullRequest({ owner, repo, prBranch: pr.head.ref, baseBranch: pr.base.ref, }); await thread.post(review); }); bot.onSubscribedMessage(async (thread, message) => { await thread.post( "I've already reviewed this PR. @mention me on a new PR to start another review." ); });`

`onNewMention` fires when a user @mentions the bot, for example `@codereview can you review this?`. The handler extracts the PR details from the message's raw payload, runs the sandboxed review, and posts the result. Calling `thread.subscribe()` lets the bot respond to follow-up messages in the same thread.

### 6\. Handle the webhook

Create the Hono app with a single webhook route that delegates to Chat SDK:

`import { Hono } from "hono"; import { waitUntil } from "@vercel/functions"; import { bot } from "./bot"; const app = new Hono(); app.post("/api/webhooks/github", async (c) => { const handler = bot.webhooks.github; if (!handler) { return c.text("GitHub adapter not configured", 404); } return handler(c.req.raw, { waitUntil }); }); export default app;`

Chat SDK's GitHub adapter handles signature verification, event parsing, and routing internally. The `waitUntil` option ensures the review completes after the HTTP response is sent. This is required on serverless platforms where the function would otherwise terminate before your handlers finish.

### 7\. Test locally

1.  Start your development server (`pnpm dev`)
    
2.  Expose it with a tunnel (e.g. `ngrok http 3000`)
    
3.  Update the webhook URL in your GitHub repository settings to your tunnel URL
    
4.  Open a pull request
    
5.  Comment `@my-review-bot can you review this?`. The bot should respond with "Starting code review..." followed by the full review
    

### 8\. Deploy to Vercel

Deploy your bot to Vercel:

`vercel deploy`

After deployment, set your environment variables in the Vercel dashboard (`GITHUB_TOKEN`, `GITHUB_WEBHOOK_SECRET`, `REDIS_URL`, `BOT_USERNAME`). Update the webhook URL in your GitHub repository settings to your production URL.

## Troubleshooting

### Bot doesn't respond to mentions

Check that your webhook is configured with the **Issue comments** and **Pull request review comments** events, and that the **Payload URL** matches your deployed endpoint. GitHub sends a `ping` event when you first save the webhook, so your server must be running and reachable.

### Webhook signature verification fails

Confirm that `GITHUB_WEBHOOK_SECRET` matches the secret you set in the webhook configuration. A mismatched or missing secret will cause the adapter to reject incoming webhooks.

### Sandbox fails to clone the repo

Verify that `GITHUB_TOKEN` has `repo` scope and hasn't expired. For private repositories, the token must also have access to the specific repo. Check the sandbox logs for authentication errors.

### Review times out or runs out of steps

The sandbox has a 5-minute timeout and the agent stops after 20 steps. For large PRs, increase these limits in `src/review.ts` by adjusting the `timeout` option on `Sandbox.create()` and the `stepCountIs()` value on the agent.

### Redis connection errors

Verify that `REDIS_URL` is reachable from your deployment environment. The state adapter uses Redis for distributed locking, so the bot won't process messages without a working connection.

* * *

## Build with a template or read more.

---

[View full KB sitemap](/kb/sitemap.md)
