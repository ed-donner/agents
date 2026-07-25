/**
 * Register the worker agent so Mastra's Studio can show it.
 *
 * `npm run dev` (mastra dev) reads this file, finds the Mastra instance, and opens
 * Studio at http://localhost:4111, a local UI where you chat with the agent and watch
 * every model step, tool call and result render live. We seed one goal here, an English
 * note to translate, so there is something on the board when Studio opens; ask the
 * worker to work the goal and it reads the note, translates it, records the Spanish on
 * the board, and replies with it.
 *
 * This agent gets the board tools only, not the filesystem MCP. Studio bundles the app
 * and runs it from .mastra/output, where a spawned `npx` is not on PATH, so the MCP
 * server cannot start here ("spawn npx ENOENT"). So the Studio goal carries its text on
 * the board itself; the full file worker with the filesystem MCP runs from the terminal
 * as worker.ts (npm run worker).
 */

import "../../env.ts";
import { Mastra } from "@mastra/core/mastra";
import { Agent } from "@mastra/core/agent";
import { boardTools } from "../../tools.ts";
import { resetBoard, addGoal, claimTodo } from "../../board.ts";

const NOTE =
  "Welcome to the team. Today we are building a small language tutor, one piece at a time. Each helper picks a single task from the shared board, does the work carefully, and marks it done.";

resetBoard();
claimTodo(addGoal(`Translate this note into natural Spanish, then close the goal with your Spanish translation as the result:\n\n${NOTE}`));

export const worker = new Agent({
  id: "worker",
  name: "Worker",
  instructions:
    "You are a careful worker with a shared todo board. Read the pending goal with show_todos and do what it asks. Always record your finished work by calling complete_task with the goal's id and your result, which marks the goal done. Then reply with your result so the user can read it.",
  model: "openai/gpt-5.4-mini",
  tools: boardTools,
});

export const mastra = new Mastra({ agents: { worker } });
