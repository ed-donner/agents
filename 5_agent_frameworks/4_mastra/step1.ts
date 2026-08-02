/**
 * Step 1: Create the agent.
 *
 * In Mastra an agent is an Agent: a name, instructions (its system prompt), and a
 * model. The model is the routing string "openai/gpt-5.4-mini", resolved through the
 * Vercel AI SDK, which picks OpenAI and reads OPENAI_API_KEY from the environment.
 * Nothing runs yet; we just build it. Run it with: npm run step1
 */

import "./env.ts";
import { Agent } from "@mastra/core/agent";

const agent = new Agent({
  id: "assistant",
  name: "Assistant",
  instructions: "You are a concise, friendly assistant. Reply in a single short sentence.",
  model: "openai/gpt-5.4-mini",
});

console.log(`Created agent: ${agent.name}`);
