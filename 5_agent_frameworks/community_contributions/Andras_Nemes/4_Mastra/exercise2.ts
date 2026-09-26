/**
 * Exercise part 3: the same agent on a different endpoint.
 *
 * SWAP_AI.md shows the move: instead of the "openai/gpt-5.4-mini" routing string,
 * build a provider with a baseURL and hand the agent a model instance. We point
 * it at DeepSeek's OpenAI-compatible endpoint with deepseek-chat; the
 * DEEPSEEK_API_KEY is already in the repo-root .env from earlier weeks.
 *
 * One lesson carried over from the MAF day applies here too: newer versions of
 * the AI SDK's OpenAI provider default to OpenAI's Responses API, which third
 * party endpoints do not implement. provider.chat(...) pins the classic Chat
 * Completions protocol, the one every OpenAI-compatible endpoint speaks.
 *
 * Everything else, the tools, the MCP server, the instruction and the board, is
 * identical to exercise1.ts. Run it with: npm run exercise2
 */

import "./env.ts";
import { join } from "node:path";
import { mkdirSync, rmSync, existsSync, readFileSync } from "node:fs";
import { Agent } from "@mastra/core/agent";
import { createOpenAI } from "@ai-sdk/openai";
import { boardTools, makeFilesystem, WORKSPACE } from "./tools.ts";
import { resetBoard, addGoal, claimTodo, showBoard } from "./board.ts";

const GOAL = "Write a short haiku about Lisbon into lisbon.txt.";

const INSTRUCTIONS = `
You are a careful worker with a shared todo board and a set of file tools.

Take the pending goal and see it through. Begin by laying out a short plan: the handful of concrete steps the work itself breaks down into, added to the board under the goal. Then carry them out with your file tools, marking each step done as you finish it. Once the steps are all done, close the goal. Your files live in the single folder your tools are allowed to use.
`;

// Seed the board with the one goal and clear any old output.
mkdirSync(WORKSPACE, { recursive: true });
rmSync(join(WORKSPACE, "lisbon.txt"), { force: true });
resetBoard();
const goalId = addGoal(GOAL);
claimTodo(goalId);
console.log(`Seeded goal ${goalId}: ${GOAL}\n`);

const deepseek = createOpenAI({
  baseURL: "https://api.deepseek.com/v1",
  apiKey: process.env.DEEPSEEK_API_KEY,
});

const filesystem = makeFilesystem();
const worker = new Agent({
  id: "worker",
  name: "Worker",
  instructions: INSTRUCTIONS,
  model: deepseek.chat("deepseek-chat"), // the only line that changed from exercise1
  tools: { ...boardTools, ...(await filesystem.listTools()) },
});

await worker.generate("Please work the pending goal on the board.", {
  maxSteps: 25,
  onStepFinish: (step: { toolCalls?: { payload: { toolName: string; args?: unknown } }[] }) => {
    for (const call of step.toolCalls ?? []) {
      console.log(`  called ${call.payload.toolName}(${JSON.stringify(call.payload.args)})`);
    }
  },
});
await filesystem.disconnect();

console.log("\nBoard after the run:");
showBoard();
const lisbon = join(WORKSPACE, "lisbon.txt");
if (existsSync(lisbon)) {
  console.log("\nlisbon.txt:\n" + readFileSync(lisbon, "utf-8"));
}

process.exit(0); // Mastra keeps its model connection pool open, so exit once the work is done
