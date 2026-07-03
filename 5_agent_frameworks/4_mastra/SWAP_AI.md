# Pointing this day at a different model

Mastra resolves models through the Vercel AI SDK, so the `model` field takes a `provider/model` routing string. We use `"openai/gpt-5.4-mini"`, which picks OpenAI and reads `OPENAI_API_KEY` from your `.env`. To run against any OpenAI-compatible endpoint instead (OpenRouter, a local server, a gateway), build a provider with a `baseURL` and pass the resulting model instance to the agent.

Install the provider in this folder (it is already a dependency, so this is usually a no-op):

```bash
npm i @ai-sdk/openai
```

Then build a provider and use it in place of the routing string:

```typescript
import { createOpenAI } from "@ai-sdk/openai";

const provider = createOpenAI({
  baseURL: process.env.OPENAI_BASE_URL, // e.g. https://openrouter.ai/api/v1 or http://localhost:11434/v1
  apiKey: process.env.OPENAI_API_KEY,
});

const worker = new Agent({
  name: "Worker",
  instructions: INSTRUCTIONS,
  model: provider("gpt-5.4-mini"), // instead of the "openai/gpt-5.4-mini" string
  tools: { ...boardTools, ...(await filesystem.listTools()) },
});
```

The default base URL is `https://api.openai.com/v1`; setting `baseURL` redirects every call. For an endpoint that only mimics the chat-completions shape, `createOpenAICompatible({ baseURL, name, apiKey })` from `@ai-sdk/openai-compatible` is the leaner alternative, used the same way: `compat("model-name")`.

Everything else in the day stays exactly the same. The board tools, the filesystem MCP server, and the board are all model-agnostic, so only the one model line changes.
