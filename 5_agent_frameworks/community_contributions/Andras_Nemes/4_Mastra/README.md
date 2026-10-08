# Mastra Lab Exercises

Solutions for the exercise in `5_agent_frameworks/4_mastra/lab.md`.

- `exercise1.ts` runs the worker with a new goal: write a Madrid haiku to `madrid.txt`.
- `exercise2.ts` runs the same worker against DeepSeek's OpenAI-compatible endpoint and writes a Lisbon haiku.
- `board.ts`, `tools.ts`, and `env.ts` provide the local board, tools, and environment setup.

## Setup

Use Node 24 and install the dependencies once from this directory:

```bash
npm install
```

The repository root `.env` must contain `OPENAI_API_KEY` and `DEEPSEEK_API_KEY`.

## Run

```bash
npm run exercise1
npm run exercise2
```

Each command prints the tool calls and completed board. Generated workspace files are excluded from Git.

## Mastra Studio

Studio is the interactive part of the course lab, so it does not add a separate solution artifact. To try it, run the existing course project:

```bash
cd 5_agent_frameworks/4_mastra
npm run dev
```

Open `http://localhost:4111`, select the Worker, and ask it to work the pending goal. Studio displays the model steps, tool calls, and results.
