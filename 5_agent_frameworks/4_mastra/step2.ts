/**
 * Step 2: Run it.
 *
 * Send a message, await the reply, and print the result's .text. With no tools yet
 * there is nothing to loop over, so the agent just answers. This is still only an
 * LLM call. Run it with: npm run step2
 */

import "./env.ts";
import { Agent } from "@mastra/core/agent";

const agent = new Agent({
  id: "assistant",
  name: "Assistant",
  instructions: "You are a concise, friendly assistant. Reply in a single short sentence.",
  model: "openai/gpt-5.4-mini",
});

const reply = await agent.generate("Say hello in Spanish.");
console.log(reply.text);

process.exit(0); // Mastra keeps its model connection pool open, so exit once the work is done
