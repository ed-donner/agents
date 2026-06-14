/**
 * Register the worker agent so Mastra's Studio can show it.
 *
 * `npm run dev` (mastra dev) reads this file, finds the Mastra instance, and opens
 * Studio at http://localhost:4111, a local UI where you chat with the agent and
 * watch every tool call, the model's reasoning and full traces render live. We
 * seed one goal here so there is something on the board when Studio opens; then in
 * Studio you can ask the worker to plan steps and tick them off and watch the loop
 * turn. Studio bundles and runs the app on its own, away from npx, so this agent
 * uses the board tools; the full worker adds the filesystem MCP the same way (see
 * worker.ts) and runs from npm run worker.
 */

import "../../env.ts";
import { Mastra } from "@mastra/core/mastra";
import { Agent } from "@mastra/core/agent";
import { boardTools } from "../../tools.ts";
import { resetBoard, addGoal, claimTodo } from "../../board.ts";

resetBoard();
claimTodo(addGoal("Read notes.txt, translate its contents into natural Spanish, and write the Spanish to spanish.txt."));

export const worker = new Agent({
  id: "worker",
  name: "Worker",
  instructions: "You are a careful worker with a shared todo board. Plan the steps under your goal, tick each one off as you finish it, and close the goal when they are done.",
  model: "openai/gpt-5.4-mini",
  tools: boardTools,
});

export const mastra = new Mastra({ agents: { worker } });
