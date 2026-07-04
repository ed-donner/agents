# Run and track deploys from Slack

**Author:** Ben Sabic

---

Build a Slack bot that orchestrates your entire deployment lifecycle in the workspace your team already uses daily.

This guide walks you through a Slack bot that orchestrates the entire deploy lifecycle from a single slash command. Type `/deploy staging` and the bot:

*   Dispatches a GitHub Actions workflow
    
*   Polls the run until it completes
    
*   Comments on the relevant PR(s)
    
*   Updates linked Linear issue(s)
    
*   Posts a summary card back to Slack
    

For production deploys, the bot gates the workflow with an approval step, so the deploy proceeds only after an authorized team member approves it.

The bot is built with [Chat SDK](https://chat-sdk.dev) and [Vercel Workflows](https://vercel.com/workflow). Chat SDK handles the Slack interaction layer (cards, buttons, modals, and slash commands), while Vercel Workflow handles stateful orchestration (pausing for approval, polling GitHub, and resuming when events arrive). You write the deploy pipeline as a single function that pauses and resumes over minutes or hours without a database or state machine.

Deploy the template now, or read on for a deeper look at how it all works.

## Quick start with an AI coding agent

If you're working with an AI coding agent like Claude Code or Cursor, you can clone the template and hand off implementation with this prompt:

`I want to build a deploy bot for Slack using Chat SDK and Vercel Workflows. Clone the template repo at https://github.com/vercel-labs/chat-sdk-deploy-bot, install dependencies with pnpm, and walk me through setting up the environment variables in .env.local. I need a Slack app, a GitHub fine-grained personal access token with Actions (read/write), Contents (read), Issues (write), and Pull requests (read) permissions, and Redis (Upstash) configured. After setup, help me deploy it to Vercel and test the /deploy slash command. When searching for information, check for applicable skill(s) first and review local documentation.`

### Vercel Plugin

Turn your agent into a Vercel expert with this [plugin](https://vercel.com/docs/agent-resources/vercel-plugin). The [Chat SDK](https://skills.sh/vercel/chat/chat-sdk) and [Workflow](https://skills.sh/vercel/workflow/workflow) skills are both included. This plugin is optional; it’s not required to use Chat SDK or for this guide.

`npx plugins add vercel/vercel-plugin`

## Setup and deployment

### What you need before deploying

You'll need accounts with these services:

*   **Slack** for the bot interface. Create a new app at [api.slack.com/apps](https://api.slack.com/apps).
    
*   **GitHub** for workflow dispatch. You'll need a fine-grained personal access token for the target repository.
    
*   **Redis** for Chat SDK state and Vercel Workflow. Any Redis provider works. [Upstash](https://upstash.com) supports serverless deployments and has a free tier.
    
*   **Linear** (optional) for issue tracking. Set `LINEAR_API_KEY` to enable it.
    

### Configure your Slack app

1.  Create a new Slack app from a manifest at [api.slack.com/apps](https://api.slack.com/apps). Use the [slack-manifest.json](https://github.com/vercel-labs/chat-sdk-deploy-bot/blob/main/slack-manifest.json) file included in the template repo. Replace the `https://example.com` URLs with your production domain (e.g. `https://your-app.vercel.app/api/webhooks/slack`).
    
2.  Install the app in your workspace and copy the **Bot User OAuth Token**.
    
3.  Copy the **Signing Secret** from the **Basic Information** page.
    

### Configure GitHub

1.  Create a fine-grained [personal access token](https://github.com/settings/tokens) for the target repository with these permissions:
    
    *   Actions: read and write
        
    *   Contents: read
        
    *   Issues: write
        
    *   Pull requests: read
        
2.  Configure the token for a repository that has a workflow triggered with `workflow_dispatch`. Here's an example:
    

`name: Deploy on: workflow_dispatch: inputs: environment: description: Target environment required: true type: choice options: - staging - production deploy_id: description: Optional deploy correlation ID required: false type: string run-name: Deploy ${{ inputs.environment }} (${{ inputs.deploy_id || github.sha }})`

The `deploy_id` input is optional, but including it in `run-name` helps the bot reliably match the run it dispatched against other concurrent runs.

If you want the bot to comment on GitHub PRs as a thread (with webhook-driven replies):

1.  Add a repository webhook pointing at `https://<your-domain>/api/webhooks/github`
    
2.  Set the content type to `application/json`
    
3.  Use the same secret as `GITHUB_WEBHOOK_SECRET`
    
4.  Subscribe to `issue_comment` and `pull_request_review_comment` events
    

### Configure Linear (optional)

Set `LINEAR_API_KEY` to enable Linear integration. No separate webhook setup is required.

The bot extracts issue keys from branch names and commit messages using a team prefix (defaults to `ENG`, configurable via `LINEAR_TEAM_PREFIX`). On successful deploys, staging deploys comment on linked issues. Production deploys comment and transition issues to the state configured in `LINEAR_PRODUCTION_STATE` (defaults to `Done`).

For the bot to know which commits are new in each deploy, your deploy pipeline must maintain four git tags in the target repo:

*   `deploy/staging/previous`
    
*   `deploy/staging/latest`
    
*   `deploy/production/previous`
    
*   `deploy/production/latest`
    

The bot compares `previous` to `latest` to find the commit range. It doesn't create or move these tags itself, so your CI pipeline should update them as part of the deploy process. If the tags don't exist, the bot skips Linear updates rather than guessing.

### Environment variables

| Variable                  | Required | Purpose                                                        |
| ------------------------- | -------- | -------------------------------------------------------------- |
| `SLACK_BOT_TOKEN`         | Yes      | Bot User OAuth Token (`xoxb-...`)                              |
| `SLACK_SIGNING_SECRET`    | Yes      | Request verification from the **Basic Information** page       |
| `GITHUB_TOKEN`            | Yes      | Fine-grained personal access token (`github_pat_...`)          |
| `GITHUB_WEBHOOK_SECRET`   | Yes      | Secret for verifying GitHub webhook payloads                   |
| `GITHUB_REPO_OWNER`       | Yes      | Repository owner or organization                               |
| `GITHUB_REPO_NAME`        | Yes      | Repository name                                                |
| `GITHUB_WORKFLOW_ID`      | Yes      | Workflow filename (e.g. `deploy.yml`) or numeric ID            |
| `REDIS_URL`               | Yes      | Redis connection string                                        |
| `LINEAR_API_KEY`          | No       | Enables Linear integration (`lin_api_...`)                     |
| `LINEAR_TEAM_PREFIX`      | No       | Issue key prefix (default: `ENG`)                              |
| `LINEAR_PRODUCTION_STATE` | No       | State to transition prod issues to (default: `Done`)           |
| `DEPLOY_PROD_ALLOWED`     | No       | Comma-separated Slack user IDs allowed to trigger prod deploys |
| `DEPLOY_PROD_APPROVERS`   | No       | Comma-separated Slack user IDs allowed to approve prod deploys |

If `DEPLOY_PROD_ALLOWED` is empty or unset, nobody can trigger production deploys. If `DEPLOY_PROD_APPROVERS` is empty or unset, nobody can approve them. Staging deploys are available to everyone.

### Deploy to Vercel

[Deploy the bot with one click](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fvercel-labs%2Fchat-sdk-deploy-bot&env=SLACK_BOT_TOKEN,SLACK_SIGNING_SECRET,GITHUB_TOKEN,GITHUB_WEBHOOK_SECRET,GITHUB_REPO_OWNER,GITHUB_REPO_NAME,GITHUB_WORKFLOW_ID,REDIS_URL), or clone the repo and deploy manually:

`git clone https://github.com/vercel-labs/chat-sdk-deploy-bot.git cd chat-sdk-deploy-bot pnpm install vercel`

After deploying, update your Slack app's request URLs to point to your production domain: `https://<your-vercel-domain>/api/webhooks/slack`.

### Test the slash command

Open Slack and type:

`/deploy staging`

The bot should post a deploy card to the channel and dispatch your GitHub Actions workflow. You'll see status updates in the Slack thread as the run progresses, followed by a summary card when it completes.

### Local development

`git clone https://github.com/vercel-labs/chat-sdk-deploy-bot.git cd chat-sdk-deploy-bot pnpm install cp .env.example .env.local pnpm dev`

This starts a Next.js dev server. To receive Slack webhooks locally, use [ngrok](https://ngrok.com) to create a public tunnel:

`ngrok http 3000`

Then update your Slack app's request URLs to the ngrok URL (e.g. `https://abc123.ngrok-free.dev/api/webhooks/slack`).

## How the deploy bot works

The bot has three interfaces: Slack for user interaction, GitHub for dispatching and monitoring workflows, and (optionally) Linear for issue tracking. Here's the flow:

1.  A user types `/deploy staging`, `/deploy production`, or `/deploy` (which opens a modal with environment and branch options)
    
2.  For staging deploys, the bot posts a deploy card to Slack and immediately dispatches a GitHub Actions workflow
    
3.  For production deploys, the bot adds Approve and Cancel buttons to the card and pauses. The workflow only continues if an authorized approver clicks Approve
    
4.  Once dispatched, the bot polls the GitHub Actions run every 5 seconds for up to 60 minutes, updating a status message in Slack as it progresses
    
5.  When the run completes, the bot comments on associated GitHub PRs and (if Linear is enabled) comments on linked issues and transitions production issues to your configured done state
    
6.  The bot posts a final summary card to Slack with the environment, branch, commit, duration, linked issues, and a link to the workflow run
    

[Vercel Workflows](https://vercel.com/workflow) makes this possible. A Vercel Workflow function can suspend itself mid-execution and resume later with full state preserved. The approval gate and the polling loop are both regular code. The function pauses while waiting for a button click, resumes when it arrives, then loops while polling GitHub. No cron jobs, no queues, no external state store.

## Code walkthrough

The template is a Next.js app. The bot logic lives in `lib/` (setup, handlers, and integrations) and `workflows/` (stateful deploy orchestration).

### Building the bot

The bot is a Chat SDK instance with adapters for Slack, GitHub, and optionally Linear, plus Redis-backed state:

`import { Chat } from "chat"; import { createGitHubAdapter } from "@chat-adapter/github"; import { createLinearAdapter } from "@chat-adapter/linear"; import { createSlackAdapter } from "@chat-adapter/slack"; import { createRedisState } from "@chat-adapter/state-redis"; const adapters = { github: createGitHubAdapter(), ...(LINEAR_ENABLED ? { linear: createLinearAdapter() } : {}), slack: createSlackAdapter(), }; export const bot = new Chat<typeof adapters, DeployThreadState>({ adapters, state: createRedisState(), userName: "deploy-bot", }).registerSingleton();`

Each deploy lives in a Slack thread with typed state (environment, branch, commit SHA, and the Slack user ID of whoever ran `/deploy`). This state is stored in Redis via Chat SDK's state adapter, so the approval handler and the workflow can coordinate without passing data through button payloads alone.

### Slash command and permissions

The bot registers a `/deploy` slash command with two paths. If the user provides an argument (`/deploy staging` or `/deploy production`), the bot deploys immediately on the `main` branch. If no argument is given, the bot opens a modal where the user can pick an environment and optionally specify a branch:

`bot.onSlashCommand("/deploy", async (event) => { const args = event.text.trim().toLowerCase(); if (!args) { await event.openModal( Modal({ callbackId: "deploy_form", children: [ Select({ id: "environment", label: "Environment", options: [ SelectOption({ label: "Staging", value: "staging" }), SelectOption({ label: "Production", value: "production" }), ], }), TextInput({ id: "branch", label: "Branch", optional: true, placeholder: "main", }), ], submitLabel: "Deploy", title: "Deploy", }) ); return; } const environment = args === "production" || args === "prod" ? "production" : "staging"; // ... permission check, payload build, workflow start });`

The bot resolves the HEAD commit for the branch, posts a deploy card to Slack, and starts the Vercel Workflow. Staging deploys are open to everyone. Production deploys are gated by `DEPLOY_PROD_ALLOWED` (who can trigger) and `DEPLOY_PROD_APPROVERS` (who can approve). When a permission check fails, the bot sends an ephemeral message visible only to the user who tried.

### The deploy workflow

The deploy workflow is the core of the bot.

It's a single function, marked with `"use workflow"`, that orchestrates the entire deploy lifecycle:

`export const deployWorkflow = async (rawPayload: string) => { "use workflow"; const parsed: unknown = JSON.parse(rawPayload); if (!isDeployWorkflowPayload(parsed)) { throw new Error("Invalid deploy workflow payload"); } const { thread: serializedThread, ...deploy } = parsed; // Gate production behind approval if (deploy.environment === "production") { const approved = await runApprovalGate(serializedThread, deploy); if (!approved) return; } // Dispatch and find the GitHub Actions run const githubRunId = await findGitHubRun(serializedThread, deploy); if (githubRunId === null) return; // Poll until complete (up to 60 minutes) const result = await pollUntilComplete(deploy, githubRunId); // Notify Linear and GitHub const { prCount, resolved } = await notifyExternalSystems( serializedThread, deploy, result ); // Post summary card await postFinalSummary(serializedThread, deploy, result, resolved, prCount); };`

This reads like sequential code, but it may take an hour to finish. Vercel Workflow handles the suspend-and-resume mechanics. When the function calls `sleep("5s")` during polling, or waits for a hook event during approval, it suspends. When the timer fires or the webhook arrives, it resumes exactly where it left off with all variables intact.

### Approval gate

For production deploys, the workflow creates a hook and waits:

`const runApprovalGate = async (serializedThread, deploy) => { const { workflowRunId } = getWorkflowMetadata(); await postApprovalCard(serializedThread, deploy, workflowRunId); using hook = createHook<ApprovalPayload>({ token: workflowRunId }); for await (const event of hook) { if (event.approved) return true; return false; } return false; };`

`createHook` registers a listener with a unique token (the workflow run ID). The workflow suspends at the `for await` loop. When someone clicks Approve in Slack, the action handler calls `resumeHook` with that same token, and the workflow picks up with `event.approved` set to `true`. If they click Cancel, it resumes with `false` and the workflow exits.

Only the person who triggered the deploy can cancel it. Anyone in the `DEPLOY_PROD_APPROVERS` list can approve.

### GitHub Actions dispatch and polling

The bot dispatches a `workflow_dispatch` event to your GitHub Actions workflow, then finds the resulting run by matching it against the branch, commit SHA, and a deploy correlation ID:

`const findGitHubRun = async (serializedThread, deploy) => { const dispatch = await dispatchGitHubWorkflow(deploy); let githubRunId = null; for (let attempt = 0; attempt < 10; attempt++) { await sleep("3s"); githubRunId = await findDispatchedRunOnce(deploy, dispatch); if (githubRunId !== null) break; } return githubRunId; };`

The dispatch function gracefully degrades if your workflow doesn't accept all the expected inputs. It tries `{ environment, deploy_id }` first, then `{ environment }` alone, then no inputs at all. This makes the bot compatible with most existing deploy workflows without changes.

Once a run is found, the bot polls every 5 seconds until the run completes or 60 minutes pass. Each `sleep("5s")` call suspends the Vercel Workflow function, and each `fetchRunSnapshot` is marked with `"use step"` so it retries automatically if the GitHub API call fails.

### Linear and GitHub notifications

On a successful deploy, the bot notifies both Linear and GitHub.

Linear issues are found by comparing deploy tags. The bot looks at the commit range between `deploy/{environment}/previous` and `deploy/{environment}/latest` in your repo, extracts Linear issue keys (like `ENG-123`) from branch names and commit messages, then comments on each issue with the deploy details. For production deploys, it also transitions issues to your configured done state.

GitHub pull requests associated with the deploy commit receive a comment with a summary table linking back to the workflow run.

Both steps are wrapped in `"use step"` directives, so they're retryable and isolated from each other. If the Linear step fails, the GitHub PR comments still proceed.

### Summary card

When the run completes, the bot posts a final card to the Slack thread with the environment, branch, commit, duration, linked issues, and a link to the GitHub Actions run. If Linear is enabled, the card also includes a table of issue identifiers and titles. If the deploy fails to dispatch or the run can't be matched, the triggerer is notified.

## How to add Teams, Discord, or other platforms

Chat SDK supports multiple platforms from a single codebase. The cards, fields, and buttons you've already defined render natively on each platform, including Block Kit on Slack, Adaptive Cards on Teams, and Google Chat Cards.

To add Microsoft Teams or another platform, register an additional adapter:

`import { createTeamsAdapter } from "@chat-adapter/teams"; export const bot = new Chat({ adapters: { github: createGitHubAdapter(), slack: createSlackAdapter(), teams: createTeamsAdapter(), }, state: createRedisState(), userName: "deploy-bot", });`

The existing webhook route at `app/api/webhooks/[platform]/route.ts` already uses a dynamic segment, so Teams webhooks would be handled at `/api/webhooks/teams` with no additional routing code.

Modals are currently Slack-only, so the `/deploy` command with no arguments (which opens a modal) only works on Slack. On other platforms, require the environment argument.

See the [Chat SDK adapter directory](https://chat-sdk.dev/adapters) for the full list of supported platforms.

## Related resources

*   [Chat SDK Deploy Bot template](https://github.com/vercel-labs/chat-sdk-deploy-bot)
    
*   [Chat SDK documentation](https://chat-sdk.dev/docs)
    
*   [Chat SDK GitHub](https://github.com/vercel/chat)
    
*   [The Complete Guide to Chat SDK](https://vercel.com/kb/guide/the-complete-guide-to-chat-sdk)
    
*   [Vercel Workflows documentation](https://vercel.com/docs/workflow)
    
*   [Workflow SDK](https://useworkflow.dev/)

---

[View full KB sitemap](/kb/sitemap.md)
