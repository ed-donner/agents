# Welcome to Week 5 - Agent Frameworks

## Day 4: Mastra (TypeScript)

Same week, same five steps, a new framework, and today a new language. The whole idea this week is that once you know one agent framework, you basically know them all, so every day we build the same agent the same five steps and watch the idioms rhyme:

1. **Create the agent** - give it a model and a system prompt.
2. **Run it** - send a message, get a reply.
3. **Add tools** - plain typed functions the agent can call.
4. **Add MCP** - connect a tool server someone else wrote, wired the same way every time.
5. **Put it in a loop with a goal** - hand it an objective and let it work, step after step, until the job is done.

Today the five steps are written in **TypeScript** with **Mastra**, the leading TypeScript-native agent framework, built by the team behind Gatsby. This is the day that tests the week's thesis across a language boundary: the same agent, the same SQLite board, the same worker, now in TypeScript, the language of the web.

### How this day works

This is the one TypeScript day, and it runs differently from the Python notebooks. Instead of a notebook, the lab is this file plus five small TypeScript programs sitting next to it, `step1.ts` to `step5.ts`. For each step, read the explanation here, open the matching file to see the full code, then run it from a terminal. The board and the tools live in their own files, `board.ts` and `tools.ts`, which the steps import; open those too, they are the substrate the whole day is built on.

<table style="margin: 0; text-align: left; width:100%">
    <tr>
        <td style="width: 150px; height: 150px; vertical-align: middle;">
            <img src="../../assets/tools.png" width="150" height="150" style="display: block;" />
        </td>
        <td>
            <h2 style="color:#00bfff;">The Mastra docs</h2>
            <span style="color:#00bfff;">The docs live at <a href="https://mastra.ai/docs">mastra.ai/docs</a>. Mastra sits on top of the Vercel AI SDK, so a model is named with a <code>provider/model</code> routing string and you can reach dozens of providers the same way. It reached 1.0 in January 2026 and moves fast, so we pin the version (<code>@mastra/core</code> 1.42 here) and treat older blog posts with care. Two shapes to know: the model is a string like <code>openai/gpt-5.4-mini</code>, and an <code>Agent</code> is built from a name, its <code>instructions</code> and that model.</span>
        </td>
    </tr>
</table>

## Setup

A little one-time setup. Two directories matter, so the commands below say which one to run each in: the **project root**, the directory called `agents` that you cloned, and **this Mastra directory**, `agents/5_agent_frameworks/4_mastra`, the folder this file lives in.

- **Node 24 LTS.** The code is TypeScript run through Node, and the board uses Node's built-in SQLite, which is flagless from Node 23.4 on. Check your version with `node --version`.
- **The Node packages for this day.** Run this in **this Mastra directory, `agents/5_agent_frameworks/4_mastra`**, to install its dependencies once:

  ```bash
  npm install
  ```

- **`OPENAI_API_KEY`** in the repo-root `.env`, the same key you have used since Week 1. The programs read it with `dotenv`, searching up from the folder for the nearest `.env`.

Run every step below from a terminal in **this Mastra directory**. Each one is `npm run stepN`, which is just `tsx stepN.ts` under the hood.

## Our project this week: a SQLite todo board

Open `board.ts`. It is the TypeScript twin of the `board.py` from Days 1 to 3: one file, one table, no server to run, using Node's built-in `node:sqlite`. A worker is handed one **goal**; to reach it, it writes its own **step** todos under that goal, ticks each one off as it goes, and closes the goal at the end. `showBoard()` prints it in the rich style from Week 1, each goal with its steps indented beneath, done todos struck through in green.

Then open `tools.ts`. It holds the three board tools, written the Mastra way with `createTool` and a zod input schema: `show_todos` to read the board, `plan_steps` to break a goal into steps, and `complete_task` to mark a todo done. It also has `makeFilesystem`, the filesystem MCP server we add in step 4.

## Step 1: Create the agent

Open `step1.ts`. In Mastra an agent is an `Agent`: a name, `instructions` (its system prompt), and a model. The model is the routing string `openai/gpt-5.4-mini`, resolved through the Vercel AI SDK, which picks OpenAI and reads `OPENAI_API_KEY` from the environment. Nothing runs yet; we just build it.

```bash
npm run step1
```

You should see `Created agent: Assistant`.

## Step 2: Run it

Open `step2.ts`. Send a message, await the reply, and print the result's `.text`. With no tools yet there is nothing to loop over, so the agent just answers. This is still only an LLM call.

```bash
npm run step2
```

You should see a short Spanish greeting, something like `Hola.`

## Step 3: Add tools

Open `step3.ts`. We give an agent the board tools from `tools.ts`, seed a goal, and ask what is on the board. Watch it decide, on its own, to call `show_todos` before it answers: that decide, call, read, answer is the agent loop starting to turn. All three tools come together in step 5.

```bash
npm run step3
```

The agent reports the one pending goal, then `showBoard()` prints it beneath.

## Step 4: Add MCP

Open `step4.ts`. MCP is just more tools: ones you did not write, connected over a small protocol. We give the agent the filesystem reference server, the same Node server every framework uses this week, scoped to a single `workspace` folder. In Mastra an MCP server is an `MCPClient`; you pull its tools with `await mcp.listTools()` and hand them to the agent.

Mastra has the cleanest MCP wiring of the week. The two fixes this day needs are plain options on the stdio server (see `makeFilesystem` in `tools.ts`): `stderr: "ignore"` discards the server's startup banner, and `cwd` starts the server in the workspace so the agent's relative file names resolve there. No subclass and no monkeypatch.

```bash
npm run step4
```

The agent reads `notes.txt` through the filesystem server and summarizes it in one sentence.

## Step 5: Put it in a loop with a goal

Open `step5.ts`. Now the payoff. Give one agent all three board tools and the filesystem server, hand it the goal, and let it run. It plans its own steps on the board, works them with its file tools, ticks each one off, and closes the goal when the work is done. That is the agent loop running on its own: read, plan, act, check off, repeat.

```bash
npm run step5
```

Watch the board fill with steps and then strike through in green, with the Spanish written into `workspace/spanish.txt`.

## The one cool thing: Studio

Mastra's developer experience is its calling card, and Studio is the centerpiece: a local web UI for your agents, the most polished one in this week's lineup. Start it from a terminal in this folder:

```bash
npm run dev
```

then open `http://localhost:4111`. Pick the Worker agent and ask it to work the goal on the board. It reads the English note waiting there, translates it into Spanish, marks the goal done with the translation, and replies with it, while each model step, each tool call and each result renders live, with full traces you can replay. You can switch models and adjust settings in the same panel.

Two asides in the same spirit as the rest of the week. The model is a routing string, so pointing the worker at any OpenAI-compatible endpoint is a one-line change; `SWAP_AI.md` in this folder shows it. And Mastra has first-class native A2A: any agent you register is automatically exposed with an agent card and a JSON-RPC endpoint, with no extra work. We do not build with A2A this week, but it is a nice thing to get for free.

<table style="margin: 0; text-align: left; width:100%">
    <tr>
        <td style="width: 150px; height: 150px; vertical-align: middle;">
            <img src="../../assets/exercise.png" width="150" height="150" style="display: block;" />
        </td>
        <td>
            <h2 style="color:#ff7800;">Exercise</h2>
            <span style="color:#ff7800;">Change the goal in <code>step5.ts</code>, for example "write a short haiku about Madrid into madrid.txt", and run it again. Does the agent plan sensible steps and pick the right file tools? Then open Studio with <code>npm run dev</code>, watch the worker translate its note live in the browser, and try pointing the model at another OpenAI-compatible endpoint by following <code>SWAP_AI.md</code>.</span>
        </td>
    </tr>
</table>
