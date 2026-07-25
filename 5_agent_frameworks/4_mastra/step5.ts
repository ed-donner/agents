/**
 * Step 5: Put it in a loop with a goal.
 *
 * Now the payoff. Give one agent all three board tools and the filesystem server,
 * hand it the goal, and let it run. It plans its own steps on the board, works them
 * with its file tools, ticks each one off, and closes the goal when the work is
 * done. That is the agent loop running on its own: read, plan, act, check off,
 * repeat. Run it with: npm run step5
 *
 * The terminal worker that Day 5 launches is worker.ts next to this file: the same
 * agent, plus the bits the project needs (claim one task on a shared board, switch
 * model via WORKER_MODEL, print each tool call).
 */

import "./env.ts";
import { join } from "node:path";
import { mkdirSync, rmSync, existsSync, readFileSync } from "node:fs";
import { Agent } from "@mastra/core/agent";
import { boardTools, makeFilesystem, WORKSPACE } from "./tools.ts";
import { resetBoard, addGoal, claimTodo, showBoard } from "./board.ts";

const GOAL = "Read notes.txt, translate its contents into natural Spanish, and write the Spanish to spanish.txt.";

const INSTRUCTIONS = `
You are a careful worker with a shared todo board and a set of file tools.

Take the pending goal and see it through. Begin by laying out a short plan: the handful of concrete steps the work itself breaks down into, added to the board under the goal. Then carry them out with your file tools, marking each step done as you finish it. Once the steps are all done, close the goal. Your files live in the single folder your tools are allowed to use.
`;

// Seed the board with the one goal and clear any old output.
mkdirSync(WORKSPACE, { recursive: true });
rmSync(join(WORKSPACE, "spanish.txt"), { force: true });
resetBoard();
const goalId = addGoal(GOAL);
claimTodo(goalId); // the worker picks up the goal: pending -> in_progress
console.log(`Seeded goal ${goalId}: ${GOAL}\n`);


const filesystem = makeFilesystem();
const worker = new Agent({
  id: "worker",
  name: "Worker",
  instructions: INSTRUCTIONS,
  model: "openai/gpt-5.4-mini",
  tools: { ...boardTools, ...(await filesystem.listTools()) },
});

await worker.generate("Please work the pending goal on the board.", { maxSteps: 25 });
await filesystem.disconnect();

console.log("\nBoard after the run:");
showBoard();
const spanish = join(WORKSPACE, "spanish.txt");
if (existsSync(spanish)) {
  console.log("\nspanish.txt:\n" + readFileSync(spanish, "utf-8"));
}

process.exit(0); // Mastra keeps its model connection pool open, so exit once the work is done
