/**
 * Step 3: Add tools.
 *
 * First our project for the week: a tiny SQLite todo board, the TypeScript twin of
 * the board.py from Days 1 to 3, using Node's built-in node:sqlite. It lives in
 * board.ts; open it to read it. A worker is handed one goal; to reach it, it writes
 * its own step todos under that goal, ticks each one off, and closes the goal.
 *
 * A tool in Mastra is createTool with an id, a description, a zod input schema, and
 * an async execute. The three board tools (show_todos, plan_steps, complete_task)
 * live in tools.ts. Here we give an agent the board tools and ask what is on the
 * board: watch it decide, on its own, to call show_todos before it answers. Run it
 * with: npm run step3
 */

import "./env.ts";
import { Agent } from "@mastra/core/agent";
import { showTodos, completeTask } from "./tools.ts";
import { resetBoard, addGoal, showBoard } from "./board.ts";

resetBoard();
addGoal("Read notes.txt, translate its contents into natural Spanish, and write the Spanish to spanish.txt.");

const boardAgent = new Agent({
  id: "board-agent",
  name: "Board Agent",
  instructions: "You help manage a shared todo board.",
  model: "openai/gpt-5.4-mini",
  tools: { showTodos, completeTask },
});

const reply = await boardAgent.generate("What is on the board right now, and what is its status?");
console.log(reply.text);

console.log("\nThe board:");
showBoard();

process.exit(0); // Mastra keeps its model connection pool open, so exit once the work is done
